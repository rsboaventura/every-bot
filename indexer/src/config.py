from pathlib import Path
from dotenv import load_dotenv  # type: ignore[import-not-found]
try:
	from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
	from pydantic import BaseSettings  # type: ignore[misc]
	SettingsConfigDict = None  # type: ignore[assignment]

# Carrega sempre .env (override True garante que mudanças no arquivo prevaleçam
# sobre variáveis previamente carregadas no processo) e faz fallback para
# .env.example apenas se .env não existir.
if Path('.env').exists():
	load_dotenv('.env', override=True)
elif Path('.env.example').exists():
	load_dotenv('.env.example', override=True)

class Settings(BaseSettings):  # type: ignore[misc]
	OPENAI_API_KEY: str
	EMBEDDING_MODEL: str = "text-embedding-3-large"
	BASE_URL: str
	TENANT_ID: str
	INPUT_DIR: str
	OUT_DIR: str
	CRAWL_MAX_PAGES: int = 200
	CRAWL_MAX_PAGE_CHARS: int = 60000
	CRAWL_SAME_DOMAIN_ONLY: bool = True
	CHUNK_SIZE_CHARS: int = 1400
	CHUNK_OVERLAP_CHARS: int = 160
	MAX_PDF_PAGES: int = 20
	MAX_PDF_BYTES: int = 5000000  # ~5MB

	# Pydantic v2 style
	if 'SettingsConfigDict' in globals() and SettingsConfigDict is not None:  # type: ignore[name-defined]
		model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')  # type: ignore[call-arg]
	else:  # v1 fallback
		class Config:  # type: ignore[no-redef]
			env_file = '.env'
			env_file_encoding = 'utf-8'
			extra = 'ignore'

settings = Settings()

def reload_settings():
	"""Recarrega variáveis do .env em runtime.

	Uso:
	from indexer.config import reload_settings, settings
	reload_settings(); print(settings.BASE_URL)
	"""
	global settings
	if Path('.env').exists():
		load_dotenv('.env', override=True)
	settings = Settings()
	return settings
