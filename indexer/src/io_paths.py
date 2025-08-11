import os
from .config import settings

def ensure_out():
	os.makedirs(settings.OUT_DIR, exist_ok=True)
	return settings.OUT_DIR
