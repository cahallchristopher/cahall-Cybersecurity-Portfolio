# Architecture

---

## Overview

PrivateGPT v1.0.1 API server + Ollama inference + Qdrant vector database.
Everything runs locally. No external API calls.

---

## Component Map
---

## Configuration System

PrivateGPT v1.0.1 uses environment variables mapped to built-in settings.yaml.

Key variables:
| Variable | Value |
|---|---|
| OPENAI_API_BASE | http://localhost:11434/v1 |
| PGPT_LLM_DEFAULT | nous-hermes2:10.7b |
| PGPT_EMBEDDING_DEFAULT | mxbai-embed-large:latest |
| PGPT_QDRANT_URL | http://localhost:6333 |
| PGPT_QDRANT_PREFER_GRPC | false |
| PGPT_QDRANT_PATH | (must be unset, not empty string) |

Built-in settings.yaml was patched to clear PGPT_QDRANT_PATH default.
Re-apply after any uv upgrade of private-gpt.

---

## Engineering Decisions

| Decision | Reason |
|---|---|
| uv over pip | 10x faster, custom wheel server |
| Docker Qdrant | Eliminates lock conflicts |
| Patch built-in yaml | Only reliable way to clear path default |
| nous-hermes2 | No safety filters, strong reasoning |
| mxbai-embed-large | Better retrieval quality (1024-dim) |
| Python requests for ingest | Correct JSON serialization |
| Collections by category | Targeted retrieval per domain |
