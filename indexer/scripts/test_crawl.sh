#!/usr/bin/env bash
set -euo pipefail

# Simple script to run crawl + build index (offline optional)
# Usage:
#   ./scripts/test_crawl.sh [rebuild|append] [offline]
# Example offline:
#   ./scripts/test_crawl.sh rebuild offline
# Requires: .env with BASE_URL etc.

MODE=${1:-rebuild}
OFFLINE_FLAG=${2:-}

if [[ ! -f .env && -f .env.example ]]; then
  echo "[info] copiando .env.example para .env"
  cp .env.example .env
fi

if [[ ${OFFLINE_FLAG} == "offline" ]]; then
  export OFFLINE_EMBED=1
  echo "[info] OFFLINE_EMBED ativado"
fi

echo "[info] Iniciando crawl + build (mode=$MODE)"
python -m indexer.src.cli --mode "$MODE"

OUT_DIR=$(grep '^OUT_DIR=' .env | head -1 | cut -d'=' -f2)
if [[ -z "$OUT_DIR" ]]; then
  OUT_DIR=./database/every
fi

if [[ -f "$OUT_DIR/meta.json" ]]; then
  COUNT=$(jq length "$OUT_DIR/meta.json" 2>/dev/null || echo 0)
  echo "[ok] meta.json encontrado com $COUNT chunks"
else
  echo "[erro] meta.json não encontrado em $OUT_DIR" >&2
  exit 1
fi

ls -1 "$OUT_DIR" | sed 's/^/[out]/'
