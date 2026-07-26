# Command Reference

---

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Qdrant
docker run -d --name qdrant --restart unless-stopped \
  -p 6333:6333 -p 6334:6334 \
  -v ~/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Pull models
ollama pull nous-hermes2:10.7b
ollama pull mxbai-embed-large
```

---

## Pipeline Commands

Run these in order on first setup:

```bash
# Step 1 -- Scan and load documents (test only)
python app/rag/loader.py

# Step 2 -- Test chunking
python app/rag/chunker.py

# Step 3 -- Generate embeddings (takes time)
python app/rag/embeddings.py

# Step 4 -- Upload to Qdrant
python app/rag/vectorstore.py

# Step 5 -- Test search
python app/rag/search.py

# Step 6 -- Test response generation
python app/rag/generator.py

# Step 7 -- Start the full assistant
python app/rag/chat.py
```

---

## Useful Qdrant Commands

```bash
# Check Qdrant is running
curl http://localhost:6333/healthz

# List collections
curl http://localhost:6333/collections

# Collection info
curl http://localhost:6333/collections/cyberai_security_kb

# Count vectors
curl http://localhost:6333/collections/cyberai_security_kb/points/count
```

---

## Useful Ollama Commands

```bash
# List available models
ollama list

# Check model is loaded
ollama ps

# Test embedding
curl http://localhost:11434/api/embeddings \
  -d "{\"model\": \"mxbai-embed-large:latest\", \"prompt\": \"test\"}"

# Test generation
curl http://localhost:11434/api/generate \
  -d "{\"model\": \"nous-hermes2:10.7b\", \"prompt\": \"Hello\", \"stream\": false}"
```

---

## Debug Commands

```bash
# Check embeddings file size
wc -c data/embeddings/cyberai_embeddings.json

# Count embedded chunks
python -c "import json; e=json.load(open('data/embeddings/cyberai_embeddings.json')); print(len(e))"

# Check vector dimensions
python -c "import json; e=json.load(open('data/embeddings/cyberai_embeddings.json')); print(len(e[0]['embedding']))"

# Verify Qdrant collection
curl http://localhost:6333/collections/cyberai_security_kb | python3 -m json.tool
```
