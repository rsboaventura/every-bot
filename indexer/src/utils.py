import hashlib, logging, os
try:
	import psutil  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
	psutil = None  # type: ignore[assignment]
from datetime import datetime, timezone
import re

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("indexer")

def sha1(text:str):
	return hashlib.sha1(text.encode('utf-8','ignore')).hexdigest()

def meta_record(chunk_id:str, title:str, url:str, source:str, tenant:str, text:str):
	return {
		'chunk_id': chunk_id,
		'title': title,
		'url': url,
		'source': source,
		'tenant': tenant,
	'created_at': datetime.now(timezone.utc).isoformat(),
		'sha1': sha1(text),
		'text': text
	}

def mem_mb():
	if psutil is None:
		return None
	try:
		return psutil.Process(os.getpid()).memory_info().rss/1_000_000
	except Exception:
		return None

def slugify(text: str, max_len: int = 80) -> str:
	text = text.lower().strip()
	text = re.sub(r'[^a-z0-9\-\s_]+', '', text)
	text = re.sub(r'[\s_]+', '-', text)
	text = re.sub(r'-{2,}', '-', text)
	return text[:max_len].strip('-') or 'doc'
