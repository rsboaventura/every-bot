import os, glob
from .config import settings
from .utils import logger
from .utils import logger
from pypdf import PdfReader  # type: ignore[import-not-found]
import docx  # type: ignore[import-not-found]
import markdown  # type: ignore[import-not-found]
from typing import List, Dict, Any

def read_file(path:str)->str:
	ext=os.path.splitext(path)[1].lower()
	if ext=='.pdf':
		try:
			size = os.path.getsize(path)
			if size > settings.MAX_PDF_BYTES:
				logger.debug(f"skip pdf over size limit {size} > {settings.MAX_PDF_BYTES}: {path}")
				return ''
			reader=PdfReader(path)  # type: ignore[call-arg]
			texts: List[str] = []
			for i,p in enumerate(reader.pages):  # type: ignore[attr-defined]
				if i >= settings.MAX_PDF_PAGES:
					logger.debug(f"truncate pdf at page limit {settings.MAX_PDF_PAGES}: {path}")
					break
				try:
					texts.append(p.extract_text() or '')  # type: ignore[attr-defined]
				except Exception:
					continue
			return '\n'.join(texts)
		except Exception as e:
			logger.debug(f"error reading pdf {path}: {e}")
			return ''
	if ext in ('.md','.markdown'):
		with open(path,'r',encoding='utf-8',errors='ignore') as f: return f.read()
	if ext=='.txt':
		with open(path,'r',encoding='utf-8',errors='ignore') as f: return f.read()
	if ext=='.docx':
		d=docx.Document(path)  # type: ignore[attr-defined]
		paras: List[str] = []
		for p in d.paragraphs:  # type: ignore[attr-defined]
			paras.append(getattr(p, 'text', ''))  # type: ignore[arg-type]
		return '\n'.join(paras)
	return ''

def ingest_local()->List[Dict[str, Any]]:
	base = settings.INPUT_DIR
	if not os.path.isdir(base):
		logger.info("Sem pasta input")
		return []
	docs: List[Dict[str, Any]] = []
	for path in glob.glob(os.path.join(base,'**/*'), recursive=True):
		if os.path.isdir(path): continue
		text=read_file(path)
		if not text.strip(): continue
		docs.append({'title':os.path.basename(path),'url':path,'text':text})
	logger.info(f"Ingest docs: {len(docs)} arquivos")
	return docs
