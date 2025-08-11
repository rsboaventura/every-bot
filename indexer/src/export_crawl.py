import os, hashlib
from typing import List, Dict, Any
from .config import settings
from .utils import slugify, logger

def export_docs(docs: List[Dict[str, Any]]) -> int:
    base = settings.INPUT_DIR
    os.makedirs(base, exist_ok=True)
    count = 0
    for d in docs:
        text = d.get('text','').strip()
        if not text:
            continue
        title_part = slugify(d.get('title') or '')
        h = hashlib.sha1(text.encode('utf-8','ignore')).hexdigest()[:10]
        fname = f"{title_part}-{h}.txt"
        path = os.path.join(base, fname)
        if os.path.exists(path):
            continue
        with open(path,'w',encoding='utf-8') as f:
            f.write(text)
        count += 1
    logger.info(f"Exportou {count} arquivos de crawl para {base}")
    return count
