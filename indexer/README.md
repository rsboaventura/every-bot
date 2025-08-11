# indexer
Crawler + ingestão de documentos e geração/atualização de índice FAISS (append/replace).

## Uso
```bash
python -m indexer.src.cli --tenant every --source both --mode append
```

Parâmetros:
- --source site|input|both
- --mode append|replace

Env vars em `.env.example`.

## Script rápido de teste
```bash
chmod +x scripts/test_crawl.sh
./scripts/test_crawl.sh rebuild offline   # executa crawl com embeddings offline
./scripts/test_crawl.sh append            # append real (requer OPENAI_API_KEY)
```

