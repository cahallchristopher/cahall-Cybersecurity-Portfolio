# Build Journal

> How the CyberAI SOC Assistant was built from scratch.

---

## Session 1 -- Project Design

**Objective:** Build a local SOC analyst assistant using a custom RAG pipeline.

Decision: build every component from scratch instead of using PrivateGPT or
LangChain. The goal was to understand exactly what happens at each step of
the RAG pipeline and have full control over the logic.

Pipeline design:
```
loader --> chunker --> embeddings --> vectorstore --> search --> generator --> chat
```

Each module is independently runnable with a __main__ block for testing.

---

## Session 2 -- loader.py

Built the document scanner first. Key design decisions:

Security domain auto-detection:
- Keywords in file paths map to domains (sherlock --> OSINT, recon --> Reconnaissance)
- Falls back to "General Security" if no keyword matches

Document type detection:
- Checks filename and extension
- Handles edge cases: Dockerfile, Makefile, docker-compose.yml

Metadata per document:
- source, filename, category, security_domain, document_type
- extension, size, modified timestamp
- tool name (extracted from path if under tools/ directory)

Ignored directories: .git, __pycache__, node_modules, venv
Ignored files: package-lock.json, data.schema.json

Supported extensions: .md, .txt, .py, .sh, .yaml, .yml, .conf,
.cfg, .ini, .html, .json, .toml, .xml, .csv

---

## Session 3 -- chunker.py

Simple overlapping chunker:
- chunk_size=1000 characters
- overlap=200 characters

Overlap preserves context across chunk boundaries.
Each chunk gets a chunk_id added to its metadata copy.

Decision: character-based chunking over token-based for simplicity.
Token-based would be more accurate but adds a tokenizer dependency.

---

## Session 4 -- embeddings.py

Calls Ollama /api/embeddings endpoint directly via requests.
No external embedding library needed.

Model: mxbai-embed-large:latest
- 1024 dimensions
- Trained for retrieval tasks

Retry logic: 3 attempts per chunk before skipping.
Saves embeddings to data/embeddings/cyberai_embeddings.json.
Load/save pattern avoids regenerating on every run.

Result: 44MB JSON file with vectors for all knowledge base chunks.

---

## Session 5 -- vectorstore.py

Uploads embeddings to Qdrant in batches of 100.

Why batches? Qdrant limits request payload size.
Large uploads fail if sent all at once.

Uses upsert (not insert) so re-running is safe -- existing
vectors are updated rather than duplicated.

Collection config:
- Name: cyberai_security_kb
- Vector size: 1024
- Distance: COSINE

Each point stores:
- vector (1024 floats)
- payload: content + metadata

---

## Session 6 -- search.py

This was the most complex module.

Initial problem: search results were contaminated by AI prompt files,
templates, and example files that ranked highly due to keyword overlap
with security queries.

Solution: two-layer filtering:
1. Hard block: skip results where source path contains blocked terms
2. Soft boost: adjust score based on document quality signals

Boost logic:
- README files: +0.15 (most authoritative)
- Markdown docs: +0.08
- AI prompts: -0.50 (biggest contamination source)
- Templates/examples: -0.50
- Test files: -0.10
- Python source: -0.03
- __pycache__: -0.25

Score threshold: 0.65 (filters low-confidence matches)
Initial retrieval: limit * 4 results, then re-rank and return top limit.

---

## Session 7 -- generator.py

SOC analyst persona prompt:
- Instructs the LLM to use ONLY provided context
- Structures response as: Summary, Technical Details, Tools, Recommendations
- Temperature: 0.2 (more deterministic, less creative)
- Context window: 8192 tokens

Model: nous-hermes2:10.7b
- Uncensored -- no refusals on red team content
- Strong instruction following
- Good at structured output

---

## Session 8 -- chat.py

Terminal chat loop connecting search + generator.

Flow per question:
1. Input question
2. search() -- retrieve top 5 documents
3. display_sources() -- show what was retrieved
4. generate_response() -- send question + context to LLM
5. Print structured analyst response

Commands: exit, quit, q to close.
KeyboardInterrupt handled cleanly.
