import os, json, faiss, numpy as np  # type: ignore[import-not-found]
from typing import List, Dict, Any
from openai import OpenAI  # type: ignore[import-not-found]
from tqdm import tqdm  # type: ignore[import-not-found]
from tenacity import retry, wait_exponential, stop_after_attempt  # type: ignore[import-not-found]
from .config import settings
from .chunking import iter_split
from .utils import logger, meta_record
try:
	from .utils import mem_mb  # type: ignore
except Exception:  # pragma: no cover
	def mem_mb():
		return None
from .io_paths import ensure_out

_client: OpenAI | None = None

@retry(wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(5))
def embed_batch(texts:List[str]):
	# Offline/testing mode (no chamadas externas) gera vetores zero determinísticos
	global _client
	if os.getenv('OFFLINE_EMBED'):
		DIM = 1536
		return [[0.0]*DIM for _ in texts]
	if _client is None:
		_client = OpenAI(api_key=settings.OPENAI_API_KEY)
	resp = _client.embeddings.create(model=settings.EMBEDDING_MODEL, input=texts)
	return [d.embedding for d in resp.data]

def build(all_docs:List[Dict[str, Any]], mode:str):
	ensure_out()
	# Streaming padrão (desativar com STREAM_EMBED=0 ou false)
	stream_env = os.getenv('STREAM_EMBED','1')
	stream = stream_env.lower() not in ('0','false','no')
	flush_threshold = int(os.getenv('STREAM_FLUSH','64'))
	embed_batch_size = int(os.getenv('EMBED_BATCH','32'))
	safe_mode = bool(os.getenv('SAFE_MODE'))  # SAFE_MODE=1 força flush a cada chunk
	max_chunks_env = os.getenv('MAX_CHUNKS')
	max_chunks = int(max_chunks_env) if max_chunks_env else None
	out_dir = ensure_out()
	meta_path = os.path.join(out_dir,'meta.json')
	vec_path = os.path.join(out_dir,'vectors.npy')
	index_path = os.path.join(out_dir,'index.faiss')
	all_meta: List[Dict[str, Any]] = []
	current_vecs: np.ndarray | None = None
	index = None
	if mode=='append' and os.path.exists(index_path) and os.path.exists(vec_path) and os.path.exists(meta_path):
		logger.info('Append: carregando índice existente (modo streaming compatível)')
		with open(meta_path,'r') as f: all_meta = json.load(f)
		loaded = np.load(vec_path)
		current_vecs = loaded.astype('float32', copy=False)
		dim = current_vecs.shape[1]  # type: ignore[union-attr]
		index = faiss.IndexFlatL2(dim)  # type: ignore[attr-defined]
		index.add(current_vecs)  # type: ignore[call-arg]
	num_chunks_total = len(all_meta)
	def add_vectors(new_meta: List[Dict[str, Any]], new_vecs: np.ndarray):
		nonlocal current_vecs, index, num_chunks_total, all_meta
		if new_vecs.ndim==1:
			new_vecs = new_vecs.reshape(1,-1)
		# normalize
		norms = np.linalg.norm(new_vecs, axis=1, keepdims=True) + 1e-9
		new_vecs = new_vecs / norms
		if index is None:
			index = faiss.IndexFlatL2(new_vecs.shape[1])  # type: ignore[attr-defined]
			index.add(new_vecs)  # type: ignore[call-arg]
			current_vecs = new_vecs
			all_meta = new_meta
		else:
			index.add(new_vecs)  # type: ignore[call-arg]
			current_vecs = np.vstack([current_vecs, new_vecs]) if current_vecs is not None else new_vecs
			all_meta.extend(new_meta)
		num_chunks_total = len(all_meta)
		faiss.write_index(index, index_path)  # type: ignore[attr-defined]
		np.save(vec_path, current_vecs)
		with open(meta_path,'w') as f: json.dump(all_meta, f, ensure_ascii=False)
		m = mem_mb()
		if m:
			logger.debug(f"Persistidos {len(new_meta)} chunks (total {num_chunks_total}) RAM~{m:.1f}MB")
	processed_chunks = 0
	buffer_texts: List[str] = []
	buffer_meta: List[Dict[str, Any]] = []
	def flush_buffer():
		nonlocal buffer_texts, buffer_meta, processed_chunks
		if not buffer_texts:
			return
		logger.debug(f"Embedding buffer {len(buffer_texts)} (batch={embed_batch_size})")
		emb: List[List[float]] = []
		for i in range(0,len(buffer_texts),embed_batch_size):
			batch = buffer_texts[i:i+embed_batch_size]
			emb.extend(embed_batch(batch))
		vecs = np.array(emb, dtype='float32')
		add_vectors(buffer_meta, vecs)
		processed_chunks += len(buffer_texts)
		buffer_texts = []
		buffer_meta = []
	try:
		for d in all_docs:
			logger.debug(f"Chunking doc: {d.get('title')}")
			text_len = len(d['text']) if d.get('text') else 0
			if text_len > settings.CHUNK_SIZE_CHARS * 200:
				logger.warning(f"Doc muito grande ({text_len} chars), truncando para evitar OOM")
				d['text'] = d['text'][:settings.CHUNK_SIZE_CHARS * 200]
			chunk_iter = iter_split(d['text'], settings.CHUNK_SIZE_CHARS, settings.CHUNK_OVERLAP_CHARS)
			for p in chunk_iter:
				cid = f"{num_chunks_total + len(buffer_meta)}"
				meta = meta_record(cid, d['title'], d['url'], 'site' if d['url'].startswith('http') else 'doc', settings.TENANT_ID, p)
				if stream:
					buffer_texts.append(p)
					buffer_meta.append(meta)
					if safe_mode or len(buffer_texts) >= flush_threshold:  # flush threshold configurável ou modo seguro
						flush_buffer()
				else:
					buffer_texts.append(p)
					buffer_meta.append(meta)
				processed_chunks += 1
				if processed_chunks % 500 == 0:
					m = mem_mb()
					if m:
						logger.debug(f"Progresso chunking {processed_chunks} RAM~{m:.1f}MB")
				if max_chunks and (processed_chunks + num_chunks_total) >= max_chunks:
					logger.warning(f"Max chunks atingido ({max_chunks}) interrompendo")
					break
			if max_chunks and (processed_chunks + num_chunks_total) >= max_chunks:
				break
	except KeyboardInterrupt:
		logger.warning('Interrompido por usuário; tentando flush parcial...')
	finally:
		if stream and buffer_texts:
			try:
				logger.debug(f"Flush final parcial {len(buffer_texts)} chunks")
				emb: List[List[float]] = []
				for i in range(0,len(buffer_texts),embed_batch_size):
					batch = buffer_texts[i:i+embed_batch_size]
					emb.extend(embed_batch(batch))
				vecs = np.array(emb, dtype='float32')
				add_vectors(buffer_meta, vecs)
				processed_chunks += len(buffer_texts)
			except Exception as e:  # pragma: no cover
				logger.error(f"Falha flush parcial: {e}")
			finally:
				buffer_texts.clear(); buffer_meta.clear()
	# Final flush
	flush_buffer()
	if not stream:
		# Non streaming path: embed everything accumulated once
		if not buffer_texts:
			logger.warning('Sem chunks para indexar')
			return
		logger.info(f"Embedding {len(buffer_texts)} chunks (modo não streaming, batch={embed_batch_size})")
		emb: List[List[float]] = []
		for i in range(0,len(buffer_texts),embed_batch_size):
			batch = buffer_texts[i:i+embed_batch_size]
			logger.debug(f"Embedding batch {i//embed_batch_size +1} size={len(batch)}")
			emb.extend(embed_batch(batch))
		vecs = np.array(emb, dtype='float32')
		add_vectors(buffer_meta, vecs)
	logger.info(f"Index pronto. Total chunks: {len(all_meta)}")
