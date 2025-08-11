import requests, re, os
from bs4 import BeautifulSoup  # type: ignore[import-not-found]
from urllib.parse import urljoin, urlparse
from .config import settings
from .utils import logger

def clean(text:str):
	text = re.sub(r'\s+',' ',text)
	return text.strip()

from typing import List, Dict, Any

def crawl() -> List[Dict[str, Any]]:
	start = settings.BASE_URL.rstrip('/')
	seen=set([start])
	out: List[Dict[str, Any]] = []
	q=[start]
	domain = urlparse(start).netloc
	max_pages = int(getattr(settings, 'CRAWL_MAX_PAGES', 200))
	input_dir = settings.INPUT_DIR
	os.makedirs(input_dir, exist_ok=True)
	max_chars = int(getattr(settings,'CRAWL_MAX_PAGE_CHARS',60000))
	skip_patterns = [
		'/tags/', '/categories/', '/profile/'
	]
	while q and len(out) < max_pages:
		url = q.pop(0)
		try:
			if any(sp in url for sp in skip_patterns):
				logger.debug(f"Skip pattern {url}")
				continue
			# Skip (or size-check) PDF URLs early
			if url.lower().endswith('.pdf'):
				# Download PDF into INPUT_DIR for later ingestion
				fname = url.split('/')[-1] or 'file.pdf'
				local_path = os.path.join(input_dir, fname)
				if os.path.exists(local_path):
					logger.debug(f"PDF already downloaded: {local_path}")
					continue
				try:
					head = requests.head(url, timeout=10, allow_redirects=True, headers={'User-Agent':'every-bot-indexer/1.0'})
					sz = int(head.headers.get('Content-Length','0'))
					limit = getattr(settings,'MAX_PDF_BYTES',5_000_000)
					if sz and sz > limit:
						logger.debug(f"Skip large PDF {sz}B > {limit}: {url}")
						continue
				except Exception:
					pass
				try:
					r_pdf = requests.get(url, timeout=20, headers={'User-Agent':'every-bot-indexer/1.0'})
					if r_pdf.status_code==200:
						with open(local_path,'wb') as f: f.write(r_pdf.content)
						logger.debug(f"PDF baixado: {local_path}")
					else:
						logger.debug(f"Falha download PDF status {r_pdf.status_code}: {url}")
				except Exception as e:
					logger.debug(f"Erro download PDF {url}: {e}")
				continue
			logger.debug(f"Fetch: {url}")
			r=requests.get(url,timeout=10, headers={'User-Agent':'every-bot-indexer/1.0'})
			if r.status_code!=200: continue
			soup=BeautifulSoup(r.text,'html.parser')
			raw_title = soup.title.string if soup.title and soup.title.string else url
			title = raw_title.strip()
			# collect text but cap to avoid giant pages
			from typing import List as _List
			parts: _List[str] = []
			acc = 0
			for h in soup.find_all(['h1','h2','h3','p','li']):
				seg = h.get_text(' ',strip=True)
				parts.append(seg)
				acc += len(seg)
				if acc > max_chars:
					logger.debug(f"Truncate page text at {acc} chars {url}")
					break
			main = ' '.join(parts)
			out.append({'title':title,'url':url,'text':clean(main)})
			for a in soup.find_all('a',href=True):
				href = urljoin(url,a['href'])
				if settings.CRAWL_SAME_DOMAIN_ONLY and urlparse(href).netloc!=domain: continue
				if '#' in href: continue
				if href not in seen:
					seen.add(href); q.append(href)
		except Exception as e:
			logger.warning(f"Falha {url}: {e}")
	logger.info(f"Crawl coletou {len(out)} páginas")
	return out
