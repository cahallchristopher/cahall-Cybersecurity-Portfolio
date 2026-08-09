# PrivateGPT Red Team Knowledge Base

> A fully local RAG knowledge base for red team research.
> Built on PrivateGPT v1.0.1, Ollama, and Qdrant. Nothing leaves the machine.

![Red Team](https://img.shields.io/badge/purpose-red%20team-red)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Ollama](https://img.shields.io/badge/LLM-Ollama-orange)
![Qdrant](https://img.shields.io/badge/vectordb-Qdrant-purple)

---

## What This Is

A local AI knowledge base that answers questions across red team documents:
CVEs, exploit writeups, tool manuals, payloads, and custom scripts.

You ingest documents. You ask questions. The system retrieves relevant
chunks and generates an answer using a local uncensored LLM.
No cloud. No API keys. No data leaving the machine.

---

## Architecture
Document
|
v
POST /v1/artifacts/ingest
|
v
PrivateGPT (:8080)
|-- Chunk (size=768, overlap=100)
|-- Embed --> Ollama --> mxbai-embed-large
`-- Store --> Qdrant (:6333)

Query
|
v
POST /v1/messages {use_context: true}
|
v
PrivateGPT
|-- Embed query --> mxbai-embed-large
|-- Search Qdrant --> top-K chunks
`-- Generate --> nous-hermes2:10.7b
|
v
Response + citations
---

## Tech Stack

| Component | Technology |
|---|---|
| RAG Platform | PrivateGPT v1.0.1 |
| Package Manager | uv 0.11.30 |
| LLM | nous-hermes2:10.7b (uncensored) |
| Embedding Model | mxbai-embed-large (1024-dim) |
| LLM Runtime | Ollama 0.24.0 |
| Vector Database | Qdrant (Docker, server mode) |
| Language | Python 3.11 |
| OS | Ubuntu 24 |

---

## Quick Start

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.bashrc
```

### 2. Install PrivateGPT

```bash
uv tool install --python 3.11 \
  --find-links https://wheels.privategpt.dev/packages/ \
  "private-gpt[core]"
```

### 3. Pull Models

```bash
ollama pull nous-hermes2:10.7b
ollama pull mxbai-embed-large
```

### 4. Deploy Qdrant

```bash
docker run -d \
  --name qdrant \
  --restart unless-stopped \
  -p 6333:6333 \
  -p 6334:6334 \
  -v ~/privategpt-data/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### 5. Patch Built-in Settings

```bash
sed -i "s|path: \${PGPT_QDRANT_PATH:local_data/qdrant}|path: \${PGPT_QDRANT_PATH:}|" \
  ~/.local/share/uv/tools/private-gpt/lib/python3.11/site-packages/settings.yaml
```

### 6. Start PrivateGPT

```bash
~/privategpt-data/start.sh
# Open http://localhost:8080/ui
```

---

## Ingesting Documents

```python
import requests

with open("/path/to/document.txt", "r") as f:
    content = f.read()

payload = {
    "input": {"type": "text", "value": content},
    "artifact": "document_name",
    "collection": "redteam_tools",
    "metadata": {"file_name": "document.txt", "category": "tools"}
}

r = requests.post("http://localhost:8080/v1/artifacts/ingest", json=payload)
print(r.json())
```

---

## Querying the Knowledge Base

```bash
curl -X POST http://localhost:8080/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nous-hermes2:10.7b",
    "messages": [{"role": "user", "content": "What tools are used for Pass the Hash?"}],
    "use_context": true,
    "context_filter": {"collection": "redteam_scripts"}
  }'
```

---

## Knowledge Base Structure
~/redteam-kb/
├── cves/ # CVE advisories, NVD exports
├── exploits/ # Exploit techniques and writeups
├── tools/ # Metasploit, Burp, Nmap, Nessus docs
├── payloads/ # Payload references, cheatsheets
└── scripts/ # Annotated scripts, technique docs
---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/artifacts/ingest` | Ingest a document |
| `GET` | `/v1/artifacts/list` | List all ingested documents |
| `POST` | `/v1/messages` | Query with RAG |
| `GET` | `/v1/models` | List available models |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/ui` | PrivateGPT web UI |

---

## Key Challenges Solved

| Problem | Solution |
|---|---|
| PrivateGPT ignoring settings.yaml | Switched to environment variable config |
| Qdrant embedded mode file lock | Deployed Qdrant as Docker server |
| PGPT_QDRANT_PATH conflicting with URL | Patched built-in settings.yaml default |
| gRPC connection refused on port 6334 | Exposed both ports, disabled gRPC preference |
| Embedding model name mismatch | Used full tag: mxbai-embed-large:latest |
| JSON encoding errors in curl | Switched to Python requests library |
| Old API endpoint 404 | Introspected /openapi.json for new routes |

---

## Built As Part Of

[cahall-Cybersecurity-Portfolio](https://github.com/cahallchristopher/cahall-Cybersecurity-Portfolio)

See also:
- [OSINT Tool](../osint-tool/)
- [CyberAI SOC Assistant](../cyberai-soc-assistant/)

---

## License

MIT — for authorized security research and penetration testing only.
