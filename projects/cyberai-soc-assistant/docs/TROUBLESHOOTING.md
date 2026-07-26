# Troubleshooting Guide

> Errors encountered building the CyberAI SOC Assistant.

---

## Error 1 -- Search Results Contaminated by AI Prompt Files

**Symptom:**
Answers referenced AI prompt templates and example files
instead of real security documentation.

**Root cause:**
AI prompt files contain security keywords (attack, exploit, CVE)
which score highly on semantic similarity but contain no real knowledge.

**Fix:**
Two-layer filtering in search.py:

Layer 1 -- Hard block:
```python
blocked_files = ["ai_prompt", "prompt.txt", "template", "example"]
if any(item in source for item in blocked_files):
    continue
```

Layer 2 -- Score penalty:
```python
if "ai_prompt" in source or "/prompt" in source:
    boost -= 0.50
```

---

## Error 2 -- Embeddings Fail on Large Documents

**Symptom:**
```
[!] Embedding failed (attempt 1/3)
    Error: ReadTimeout
```

**Root cause:**
Very large chunks take longer than the default timeout for Ollama to process.

**Fix:**
Increased timeout in embeddings.py:
```python
response = requests.post(OLLAMA_URL, json=payload, timeout=180)
```

Also added retry logic with 3 attempts before skipping a chunk.

---

## Error 3 -- Qdrant Upload Fails on Large Batches

**Symptom:**
```
qdrant_client.http.exceptions.UnexpectedResponse: 413 Request Entity Too Large
```

**Root cause:**
Uploading all vectors in a single request exceeds Qdrant payload limits.

**Fix:**
Batch upload in groups of 100:
```python
for start in range(0, total, batch_size):
    batch = embeddings[start:start + batch_size]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
```

---

## Error 4 -- Collection Already Exists Error

**Symptom:**
```
qdrant_client.http.exceptions.UnexpectedResponse: 409 Conflict
```

**Root cause:**
Trying to create a collection that already exists.

**Fix:**
Check existing collections before creating:
```python
collections = [c.name for c in client.get_collections().collections]
if COLLECTION_NAME not in collections:
    client.create_collection(...)
```

---

## Error 5 -- generator.py Returns Empty Response

**Symptom:**
```
No response generated.
```

**Root cause:**
The generator was passing the raw search results list to the LLM
instead of extracting the text content from each result.

**Fix:**
Extract content from each result payload before building the prompt:
```python
context = ""
for result in results:
    payload = result.get("payload", {})
    content = payload.get("content", "")
    context += content + "

"
```

---

## Error 6 -- Module Import Errors in chat.py

**Symptom:**
```
ModuleNotFoundError: No module named "search"
```

**Root cause:**
Python cannot find sibling modules when running chat.py directly.

**Fix:**
Add the module directory to sys.path:
```python
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
from search import search
from generator import generate_response
```

---

## Error 7 -- Low Quality Search Results

**Symptom:**
Search returns results with score < 0.65 that are not relevant.

**Root cause:**
Score threshold too low, allowing poor matches through.

**Fix:**
Tuned score_threshold in search.py:
```python
score_threshold=0.65  # discard low-confidence matches
```

Also increased initial retrieval to limit*4 to give the re-ranker
more candidates to work with before returning the final top-K.
