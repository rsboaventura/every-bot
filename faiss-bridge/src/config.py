from pathlib import Path
from dotenv import load_dotenv  # type: ignore[import-not-found]
try:
	from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
	from pydantic import BaseSettings  # type: ignore[misc]
	SettingsConfigDict = None  # type: ignore[assignment]

if not Path('.env').exists() and Path('.env.example').exists():
	load_dotenv('.env.example')

class Settings(BaseSettings):  # type: ignore[misc]
	OPENAI_API_KEY: str
	EMBEDDING_MODEL: str = "text-embedding-3-large"
	INDEX_DIR: str = "../indexer/database/every"
	ALLOWED_ORIGINS: str = "*"

	if 'SettingsConfigDict' in globals() and SettingsConfigDict is not None:  # type: ignore[name-defined]
		model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')  # type: ignore[call-arg]
	else:
		class Config:  # type: ignore[no-redef]
			env_file = '.env'
			env_file_encoding = 'utf-8'
			extra = 'ignore'

settings = Settings()

