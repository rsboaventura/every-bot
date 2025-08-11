import os, json, faiss, numpy as np  # type: ignore[import-not-found]
from typing import List, Dict, Any
from .config import settings  # type: ignore[attr-defined]
from .utils import logger, cosine  # type: ignore[attr-defined]

class VectorStore:
	def __init__(self):
		self.index = None
		self.meta: List[Dict[str, Any]] = []
		self.vectors: np.ndarray | None = None
		self.load()

	def load(self):
		base = settings.INDEX_DIR
		meta_path = os.path.join(base,'meta.json')
		vec_path = os.path.join(base,'vectors.npy')
		index_path = os.path.join(base,'index.faiss')
		if not (os.path.exists(meta_path) and os.path.exists(vec_path) and os.path.exists(index_path)):
			logger.warning('Index incompleto; inicializando vazio')
			return
		with open(meta_path,'r') as f: self.meta = json.load(f)
		self.vectors = np.load(vec_path)
		self.index = faiss.read_index(index_path)  # type: ignore[attr-defined]
		logger.info(f"Index carregado: {len(self.meta)} chunks")

	def search(self, query_vec: List[float], k:int=5) -> List[Dict[str, Any]]:
		if self.vectors is None or not self.meta:
			return []
		q = np.array(query_vec, dtype='float32')
		q = q / (np.linalg.norm(q) + 1e-9)
		sims: List[tuple[int, float]] = []
		vecs32: np.ndarray = self.vectors.astype('float32', copy=False)  # type: ignore[assignment]
		for i in range(vecs32.shape[0]):
			v = vecs32[i].astype('float32', copy=False)
			sims.append((i, cosine(q, v)))  # type: ignore[arg-type]
		sims.sort(key=lambda x: x[1], reverse=True)
		out: List[Dict[str, Any]] = []
		for idx, score in sims[:k]:
			m: Dict[str, Any] = self.meta[idx]
			out.append({
				'chunk_id': str(m.get('chunk_id')),
				'title': str(m.get('title','')),
				'url': str(m.get('url','')),
				'score': float(score),
				'text': str(m.get('text',''))
			})
		return out

store = VectorStore()

