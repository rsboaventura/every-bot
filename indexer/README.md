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
