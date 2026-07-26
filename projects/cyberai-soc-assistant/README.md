# CyberAI SOC Assistant

> A fully local AI-powered Security Operations Center assistant.
> Built from scratch with a custom RAG pipeline — no frameworks, no wrappers.
> Qdrant + Ollama + custom Python modules. Nothing leaves the machine.

![Python](https://img.shields.io/badge/python-3.11-blue)
![Ollama](https://img.shields.io/badge/LLM-Ollama-orange)
![Qdrant](https://img.shields.io/badge/vectordb-Qdrant-purple)
![Red Team](https://img.shields.io/badge/purpose-SOC%20%2F%20Red%20Team-red)

---

## What This Is

A terminal-based SOC analyst assistant that answers cybersecurity questions
using your own local knowledge base.

You ask a question. The system searches a vector database of security documents,
retrieves the most relevant context, and generates a structured analyst response
using a local uncensored LLM.

The entire RAG pipeline is written from scratch — document loading, chunking,
embedding, vector storage, semantic search with custom ranking, and response
generation are all custom Python modules.

---

## How It Works

```
User Question
      |
      v
search.py  -->  generate_embedding()  -->  Ollama (mxbai-embed-large)
      |
      v
Qdrant vector search  -->  top-K relevant document chunks
      |
      v
calculate_boost()  -->  re-rank by document quality
      |
      v
generator.py  -->  SOC analyst prompt  -->  Ollama (nous-hermes2:10.7b)
      |
      v
Structured analyst response:
  1. Summary
  2. Technical Details
  3. Relevant Tools or Techniques
  4. Analyst Recommendations
```

---

## RAG Pipeline Modules

| Module | Purpose |
|---|---|
| `loader.py` | Scans knowledge base files, extracts content, builds metadata |
| `chunker.py` | Splits documents into overlapping chunks (size=1000, overlap=200) |
| `embeddings.py` | Generates 1024-dim vectors via Ollama, saves/loads from disk |
| `vectorstore.py` | Batch-uploads embeddings to Qdrant with upsert support |
| `search.py` | Semantic search with custom re-ranking and source filtering |
| `generator.py` | SOC analyst prompt + Ollama response generation |
| `chat.py` | Interactive terminal chat interface connecting all modules |

---

## Features

- **Custom RAG pipeline** — every component written from scratch
- **Security domain detection** — auto-tags documents as OSINT, Reconnaissance, Vulnerability Management, etc.
- **Smart document ranking** — boosts READMEs and docs, penalizes prompts/templates/tests
- **Source filtering** — blocks contamination from AI prompt files and examples
- **Structured SOC responses** — Summary, Technical Details, Tools, Recommendations
- **Fully local** — Qdrant + Ollama, no cloud, no API keys
- **Uncensored LLM** — nous-hermes2:10.7b, no safety filters for red team queries
- **44MB embeddings** — pre-generated vector store ready to search
- **Interactive terminal UI** — clean chat loop with source citations

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| LLM | nous-hermes2:10.7b via Ollama |
| Embedding Model | mxbai-embed-large (1024-dim) via Ollama |
| Vector Database | Qdrant (Docker, server mode) |
| Search | Custom semantic search with re-ranking |
| Interface | Terminal chat loop |

---

## Quick Start

### 1. Prerequisites

```bash
# Start Qdrant
docker run -d --name qdrant --restart unless-stopped \
  -p 6333:6333 -p 6334:6334 \
  -v ~/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Pull models
ollama pull nous-hermes2:10.7b
ollama pull mxbai-embed-large
```

### 2. Install Dependencies

```bash
cd CyberAI-SOC-Assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Load Knowledge Base

```bash
# Generate embeddings from your documents
python app/rag/embeddings.py

# Upload to Qdrant
python app/rag/vectorstore.py
```

### 4. Start the Assistant

```bash
python app/rag/chat.py
```

### Example Queries

```
SOC Analyst > How does Sherlock perform username discovery?
SOC Analyst > Explain OSINT investigation workflow
SOC Analyst > What is the purpose of Maigret?
SOC Analyst > How can I analyze suspicious network activity?
SOC Analyst > What tools are used for Pass the Hash attacks?
```

---

## Knowledge Base Structure

Documents are organized by security category:

```
data/documents/redteam-kb/
├── cves/        # CVE advisories and vulnerability data
├── exploits/    # Exploit techniques and writeups
├── payloads/    # Payload references
├── scripts/     # Security automation scripts
└── tools/       # Tool documentation (Sherlock, Maigret, etc.)
```

Supported file types: `.md`, `.txt`, `.py`, `.sh`, `.yaml`, `.json`, `.html`, `.csv`, `.xml`

---

## Security Domain Auto-Detection

The loader automatically tags documents:

| Keyword in path | Domain |
|---|---|
| sherlock, maigret, osint-framework | OSINT |
| recon | Reconnaissance |
| scanner | Vulnerability Management |
| scripts, fastapi | Security Automation |

---

## Document Ranking Logic

The search engine re-ranks results using a scoring boost system:

```python
# Boosted (higher priority)
README files:        +0.15
Markdown docs:       +0.08

# Penalized (lower priority)
AI prompt files:     -0.50
Template files:      -0.50
Example files:       -0.50
Test files:          -0.10
Python source:       -0.03
__pycache__:         -0.25
```

---

## Project Structure

```
CyberAI-SOC-Assistant/
├── app/
│   ├── rag/
│   │   ├── loader.py       # Document scanner + metadata
│   │   ├── chunker.py      # Overlapping text chunker
│   │   ├── embeddings.py   # Ollama embedding generator
│   │   ├── vectorstore.py  # Qdrant batch uploader
│   │   ├── search.py       # Semantic search + re-ranking
│   │   ├── generator.py    # SOC analyst response generator
│   │   └── chat.py         # Terminal chat interface
│   ├── api/                # FastAPI endpoints (planned)
│   └── models/             # Pydantic models (planned)
├── data/
│   ├── documents/
│   │   └── redteam-kb/     # Your security knowledge base
│   └── embeddings/
│       └── cyberai_embeddings.json   # Pre-generated vectors (44MB)
├── config/                 # Configuration files
├── docs/                   # Additional documentation
├── scripts/                # Utility scripts
├── tests/                  # Test suite
└── requirements.txt
```

---

## Built As Part Of

[cahall-Cybersecurity-Portfolio](https://github.com/cahallchristopher/cahall-Cybersecurity-Portfolio)

See also:
- [OSINT People & Identity Lookup Tool](../osint-tool/)
- [PrivateGPT Red Team Knowledge Base](../privategpt-kb/)

---

## License

MIT — for authorized security research and penetration testing only.
