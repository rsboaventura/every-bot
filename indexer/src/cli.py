import argparse, sys
from typing import List, Dict, Any
from .config import settings  # type: ignore[attr-defined]
from .crawl_site import crawl  # type: ignore[attr-defined]
from .ingest_docs import ingest_local  # type: ignore[attr-defined]
from .build_index import build  # type: ignore[attr-defined]
from .export_crawl import export_docs  # type: ignore[attr-defined]
from .utils import logger  # type: ignore[attr-defined]

def main():
	parser = argparse.ArgumentParser(description='Indexer CLI')
	parser.add_argument('--mode', choices=['rebuild','append'], default='rebuild')
	parser.add_argument('--no-crawl', action='store_true')
	parser.add_argument('--no-docs', action='store_true')
	parser.add_argument('-v','--verbose', action='store_true', help='Ativa logs detalhados')
	parser.add_argument('--export-crawl', action='store_true', help='Salva cada página crawleada em arquivos .txt no INPUT_DIR antes de indexar')
	args = parser.parse_args()
	if args.verbose:
		logger.setLevel('DEBUG')  # type: ignore[arg-type]
		logger.debug('Verbose ON')
	site_docs: List[Dict[str, Any]] = []
	if not args.no_crawl:
		logger.info('Iniciando crawl...')
		site_docs = crawl()
		logger.info(f'Crawl coletou {len