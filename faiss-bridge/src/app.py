from fastapi import FastAPI  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]
from typing import Any, Dict, List
from pydantic import BaseModel
from .config import settings  # type: ignore[attr-defined]
from .store import store  # type: ignore[attr-defined]
from .utils import logger  # type: ignore[attr-defined]
from openai import OpenAI  # type: ignore[import-not-found]

client = OpenAI(api_key=settings.OPENAI_API_KEY)

app = FastAPI(title='faiss-bridge')  # type: ignore[call-arg]

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(',')] if settings.ALLOWED_ORIGINS != '*' else ['*']
app.add_middleware(  # type: ignore[attr-defined]
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

class QueryIn(BaseModel):  # type: ignore[misc]
	query: str
	top_k: int = 5

@app.get('/health')  # type: ignore[misc]
def health() -> Dict[str, Any]:
	return {'status':'ok','chunks': len(store.meta)}

@app.post('/search')  # type: ignore[misc]
def search(q: QueryIn) -> Dict[str, List[Dict[str, Any]]]:
	if not q.query.strip():
		return {'results': []}
	emb = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=[q.query])
	vec = emb.data[0].embedding
	results = store.search(vec, q.top_k)
	# normalize score 0..1 to 0..100
	out: List[Dict[str, Any]] = []
	for r in results:
		score = (r['score'] + 1) / 2  # cosine -1..1
		out.append({**r, 'score': round(score*100,2)})
	return {'results': out}

