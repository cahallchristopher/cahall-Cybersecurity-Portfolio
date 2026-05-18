"""
config.py — All settings for your local PrivateGPT setup.
Edit this file to change models, paths, and RAG parameters.
"""

# ── Ollama Settings ────────────────────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"

# The LLM used for answering questions
LLM_MODEL = "llama3.1"          # Options: "llama3.1", "mistral", "gemma2", etc.

# The model used to turn text into vectors (must match what's in Ollama)
EMBED_MODEL = "nomic-embed-text"

# LLM generation settings
LLM_TEMPERATURE = 0.1           # 0 = deterministic, 1 = creative
LLM_MAX_TOKENS = 1024


# ── Vector Store ───────────────────────────────────────────────────────────────

# Where ChromaDB stores its data (persists across sessions)
CHROMA_DIR = "./chroma_db"

# Collection name inside ChromaDB
CHROMA_COLLECTION = "privategpt_docs"


# ── Document Chunking ──────────────────────────────────────────────────────────

# How many characters per chunk (larger = more context, slower)
CHUNK_SIZE = 1000

# How much chunks overlap (helps avoid cutting mid-sentence)
CHUNK_OVERLAP = 200


# ── Retrieval ──────────────────────────────────────────────────────────────────

# How many chunks to retrieve per query
NUM_CHUNKS = 4

# Retrieval type: "similarity" or "mmr" (mmr = more diverse results)
RETRIEVAL_TYPE = "similarity"


# ── Prompts ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on
the provided context from the user's documents. 

Rules:
- Only use information from the provided context to answer.
- If the context doesn't contain the answer, say so clearly.
- Be concise and accurate.
- Cite which document or source the information came from when possible.
"""


# ── Web UI ─────────────────────────────────────────────────────────────────────

UI_TITLE = "PrivateGPT Local"
UI_DESCRIPTION = "Chat with your documents. 100% local. Nothing leaves your machine."
UI_PORT = 7860
UI_SHARE = False   # Set True to get a public Gradio link
