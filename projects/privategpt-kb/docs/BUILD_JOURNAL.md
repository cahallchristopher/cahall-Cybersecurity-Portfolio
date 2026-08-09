# Build Journal

> How the PrivateGPT Red Team KB was built -- every decision, failure, and fix.

---

## Session 1 -- Assessment and Cleanup

Found legacy PrivateGPT at /home/chris/private-gpt/ running via:
```bash
poetry run python -m private_gpt
```

Discovered root-owned models/ directory blocking deletion:
```bash
ls -la ~/private-gpt/models/
# drwxr-xr-x 3 root root 4096 Jun 6 22:23 models

sudo rm -rf ~/private-gpt
# Freed 8.4 GB
```

---

## Session 2 -- Installing uv and PrivateGPT v1.0.1

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.bashrc

uv tool install --python 3.11 \
  --find-links https://wheels.privategpt.dev/packages/ \
  "private-gpt[core]"
# 209 packages installed
```

---

## Session 3 -- Model Selection

Selected nous-hermes2:10.7b:
- Trained on Hermes dataset
- No safety refusals on red team content
- 6.1 GB fits in 12-16 GB RAM

Selected mxbai-embed-large:
- 1024 dimensions vs 768 for nomic-embed-text
- Better retrieval on technical content

```bash
ollama pull nous-hermes2:10.7b
ollama pull mxbai-embed-large
```

---

## Session 4 -- Configuration Battles

Three layers of failure before working state.

Attempt 1 -- settings.yaml file:
PrivateGPT ignored it. --settings flag does not exist in v1.0.1.

Attempt 2 -- Environment variables:
PGPT_QDRANT_PATH= (empty string) does not clear the default.
Qdrant client received both url and path simultaneously.

Attempt 3 -- Patch built-in file:
```bash
sed -i "s|path: \${PGPT_QDRANT_PATH:local_data/qdrant}|path: \${PGPT_QDRANT_PATH:}|" settings.yaml
```
Combined with unset PGPT_QDRANT_PATH and PGPT_QDRANT_PREFER_GRPC=false.

Result: working.

---

## Session 5 -- Qdrant Docker

First attempt exposed only port 6333. PrivateGPT tried gRPC on 6334. Failed.

Fix:
```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
  -v ~/privategpt-data/qdrant_storage:/qdrant/storage qdrant/qdrant
export PGPT_QDRANT_PREFER_GRPC=false
```

---

## Session 6 -- Document Ingest API Discovery

Old endpoint /v1/ingest/files returns 404.

Found new endpoint via OpenAPI introspection:
```bash
curl -s http://localhost:8080/openapi.json | python3 -c "
import json, sys
api = json.load(sys.stdin)
for path in api['paths'].keys(): print(path)
"
# /v1/artifacts/ingest
```

Shell interpolation broke JSON. Fixed with Python requests.

First successful ingest confirmed end-to-end RAG pipeline working.
