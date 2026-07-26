# Architecture

> System design and data flow for the CyberAI SOC Assistant.

---

## Overview

A custom RAG (Retrieval-Augmented Generation) pipeline built from scratch.
No LangChain. No LlamaIndex. No PrivateGPT wrapper.
Every component is a standalone Python module.

---

## Full Pipeline

```
Knowledge Base Documents
        |
        v
loader.py
  - Scans files recursively
  - Detects security domain, category, document type
  - Builds metadata per document
  - Returns: [{content, metadata}]
        |
        v
chunker.py
  - Splits documents into overlapping chunks
  - chunk_size=1000, overlap=200
  - Adds chunk_id to metadata
  - Returns: [{content, metadata}]
        |
        v
embeddings.py
  - Calls Ollama /api/embeddings
  - Model: mxbai-embed-large:latest (1024 dims)
  - Retry logic: 3 attempts per chunk
  - Saves to data/embeddings/cyberai_embeddings.json (44MB)
  - Returns: [{content, metadata, embedding}]
        |
        v
vectorstore.py
  - Connects to Qdrant (:6333)
  - Creates collection: cyberai_security_kb
  - Batch uploads in groups of 100
  - Uses upsert (safe to re-run)
        |
        v
Qdrant Vector Database
  Collection: cyberai_security_kb
  Vectors: 1024-dimensional COSINE similarity
        |
        v
search.py  <-- User query comes in here
  - Embeds query via Ollama (same model)
  - Queries Qdrant: initial limit * 4 results
  - Filters: hard block prompt/template files
  - Re-ranks: score + boost adjustments
  - Returns: top K ranked results
        |
        v
generator.py
  - Builds SOC analyst prompt with retrieved context
  - Calls Ollama /api/generate
  - Model: nous-hermes2:10.7b
  - Temperature: 0.2, context: 8192 tokens
  - Returns: structured analyst response
        |
        v
chat.py
  - Interactive terminal loop
  - Displays retrieved sources
  - Prints structured response
```

---

## Module Dependencies

```
chat.py
  |-- search.py
  |     |-- Qdrant client
  |     `-- Ollama (embeddings)
  `-- generator.py
        `-- Ollama (LLM)

embeddings.py (run once)
  |-- loader.py
  |-- chunker.py
  `-- Ollama (embeddings)

vectorstore.py (run once)
  |-- embeddings.py (loads saved JSON)
  `-- Qdrant client
```

---

## Search Re-Ranking

The search engine uses a two-pass approach:

Pass 1 -- Qdrant COSINE similarity
  Returns limit*4 candidates above score_threshold=0.65

Pass 2 -- Custom boost re-ranking
  Adjusts scores based on document quality:

  Hard blocks (skip entirely):
    ai_prompt, prompt.txt, template, example

  Soft boosts (score adjustment):
    README:        +0.15
    .md files:     +0.08
    .py files:     -0.03
    test files:    -0.10
    __pycache__:   -0.25
    prompts:       -0.50
    templates:     -0.50

  Final sort by adjusted score, return top K.

---

## SOC Analyst Prompt Structure

```
You are CyberAI, a cybersecurity SOC analyst assistant.
Use ONLY the provided knowledge context.
Structure your response as:
  1. Summary
  2. Technical Details
  3. Relevant Tools or Techniques
  4. Analyst Recommendations

Security Knowledge Context:
[retrieved chunks here]

User Question:
[user input here]

SOC Analyst Response:
```

---

## Data Flow Diagram

```
[Documents]
    |
    |-- loader.py ---------> [{content, metadata}]
    |
    |-- chunker.py --------> [{content, metadata, chunk_id}]
    |
    |-- embeddings.py -----> [{content, metadata, embedding[1024]}]
    |                              |
    |                              v
    |                    cyberai_embeddings.json (44MB)
    |                              |
    |-- vectorstore.py -----------> Qdrant
                                      |
[User Query] --> search.py ----------> Qdrant query
                    |
                    |-- re-rank
                    |
                    v
              generator.py --> Ollama --> Response
```

---

## Engineering Decisions

| Decision | Reason |
|---|---|
| Build from scratch vs LangChain | Full control, learning, no abstraction overhead |
| mxbai-embed-large | 1024-dim, better retrieval than nomic-embed-text |
| nous-hermes2:10.7b | Uncensored, strong structured output |
| Save embeddings to JSON | Avoid regenerating on every run (expensive) |
| Batch size 100 for Qdrant | Stays within Qdrant payload size limits |
| COSINE distance | Standard for semantic similarity search |
| Score threshold 0.65 | Filters low-confidence matches |
| Temperature 0.2 | More deterministic SOC responses |
| Hard block prompt files | Prevents AI meta-content from contaminating results |
| Overlapping chunks | Preserves context across chunk boundaries |
