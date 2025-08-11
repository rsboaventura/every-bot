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
			current_vecs = np.vstack([current_vecs, new_vecs]) if current_vecs is not None else new_vec