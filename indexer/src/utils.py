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
