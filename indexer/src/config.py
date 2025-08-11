from pathlib import Path
from dotenv import load_dotenv  # type: ignore[import-not-found]
try:
	from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
	from pydantic import BaseSettings  # type: ignore[misc]
	SettingsConfigDict = None  # type: ignore[assignment]

# Carrega sempre .env (override True garante que mudanças no arqu