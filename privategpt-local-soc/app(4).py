"""
app.py — PrivateGPT Local with SOC Memory + MITRE ATT&CK tagging.
Run: python app.py
UI:  http://localhost:7860
"""

import requests
import gradio as gr
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import (
    OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    CHROMA_DIR, NUM_CHUNKS, UI_TITLE, UI_DESCRIPTION, UI_PORT, UI_SHARE
)

# ── Init ───────────────────────────────────────────────────────────────────────

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False)
)
collection = chroma_client.get_or_create_collection("soc_memory")
embedder   = SentenceTransformer("all-MiniLM-L6-v2")


# ── MITRE ATT&CK Tagger ────────────────────────────────────────────────────────

MITRE_RULES = [
    (["phishing", "spear", "lure", "attachment"],       "T1566 - Phishing"),
    (["powershell", "cmd", "bash", "script", "exec"],   "T1059 - Command & Scripting Interpreter"),
    (["credential", "password", "hash", "lsass"],       "T1555 - Credentials from Password Stores"),
    (["lateral", "pivot", "smb", "rdp", "wmi"],         "T1021 - Remote Services"),
    (["exfil", "upload", "dns tunnel", "c2", "beacon"], "T1041 - Exfiltration Over C2 Channel"),
    (["privilege", "escalat", "sudo", "token"],         "T1068 - Exploitation for Privilege Escalation"),
    (["persist", "cron", "registry", "startup"],        "T1547 - Boot/Logon Autostart Execution"),
    (["scan", "nmap", "recon", "enumerate"],            "T1046 - Network Service Discovery"),
    (["malware", "dropper", "payload", "inject"],       "T1055 - Process Injection"),
    (["ransomware", "encrypt", "lock", "ransom"],       "T1486 - Data Encrypted for Impact"),
]

def mitre_tag(text):
    text = text.lower()
    tags = [tag for keywords, tag in MITRE_RULES if any(k in text for k in keywords)]
    return tags if tags else ["No MITRE tags matched"]


# ── Document Ingestion ─────────────────────────────────────────────────────────

def extract_text(filepath):
    """Extract text from PDF, DOCX, or plain text files."""
    ext = filepath.lower().split(".")[-1]
    if ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(f"[Page {i+1}]\n{page_text}")
        return "\n\n".join(pages)
    elif ext == "docx":
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    else:
        return open(filepath, "r", encoding="utf-8", errors="ignore").read()


def ingest_files(files):
    if not files:
        return "No files selected."
    total_chunks = 0
    results = []
    for f in files:
        try:
            text = extract_text(f.name)
        except Exception as e:
            results.append(f"ERROR {f.name}: {e}")
            continue
        if not text.strip():
            results.append(f"WARNING {f.name}: no text extracted")
            continue
        chunks = [text[i:i+800] for i in range(0, len(text), 800)]
        for i, chunk in enumerate(chunks):
            emb = embedder.encode(chunk).tolist()
            collection.add(
                embeddings=[emb],
                documents=[chunk],
                metadatas=[{"source": f.name}],
                ids=[f"{f.name}-chunk-{i}"],
            )
        total_chunks += len(chunks)
        results.append(f"OK {f.name} -> {len(chunks)} chunks")
    results.append(f"\nTotal: {total_chunks} chunks stored in SOC memory.")
    return "\n".join(results)


def ingest_url(url):
    if not url.strip():
        return "Please enter a URL."
    try:
        import requests as req
        from bs4 import BeautifulSoup
        r = req.get(url.strip(), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script","style","nav","footer","header"]):
            tag.decompose()
        text = "\n".join(l for l in soup.get_text(separator="\n").splitlines() if l.strip())
        chunks = [text[i:i+800] for i in range(0, len(text), 800)]
        for i, chunk in enumerate(chunks):
            emb = embedder.encode(chunk).tolist()
            collection.add(
                embeddings=[emb],
                documents=[chunk],
                metadatas=[{"source": url}],
                ids=[f"url-{abs(hash(url))}-{i}"],
            )
        return f"Stored {len(chunks)} chunks from {url}"
    except Exception as e:
        return f"Error: {e}"


# ── Memory Search ──────────────────────────────────────────────────────────────

def search_memory(query):
    if collection.count() == 0:
        return "", ["No documents ingested yet"]
    emb = embedder.encode(query).tolist()
    results = collection.query(
        query_embeddings=[emb],
        n_results=min(NUM_CHUNKS, collection.count()),
        include=["documents", "metadatas"],
    )
    docs  = results["documents"][0]
    metas = results["metadatas"][0]
    context = "\n\n---\n\n".join(
        f"[Source: {m.get('source','?')}]\n{d}" for d, m in zip(docs, metas)
    )
    tags = mitre_tag(query + " " + context)
    return context, tags


# ── Ollama Chat ────────────────────────────────────────────────────────────────

def call_ollama(prompt):
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": LLM_TEMPERATURE, "num_predict": LLM_MAX_TOKENS}},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        return f"Ollama error: {e}"


# ── Main Chat Function ─────────────────────────────────────────────────────────

def chat(message, history):
    if not message.strip():
        return "", history

    context, tags = search_memory(message)

    prompt = f"""You are a SOC analyst assistant with access to internal intelligence documents.

RETRIEVED CONTEXT:
{context if context else "No relevant documents found."}

MITRE ATT&CK TAGS DETECTED:
{chr(10).join(f"  - {t}" for t in tags)}

ANALYST QUESTION:
{message}

Provide a structured response with:
1. Incident Summary
2. Security Analysis
3. MITRE ATT&CK Mapping
4. Recommended Actions
"""
    answer = call_ollama(prompt)
    tag_block = "\n".join(f"  `{t}`" for t in tags)
    full_answer = f"{answer}\n\n---\n**MITRE Tags:**\n{tag_block}"
    history.append((message, full_answer))
    return "", history


# ── Status ─────────────────────────────────────────────────────────────────────

def get_status():
    count = collection.count()
    if count == 0:
        return "SOC memory empty — upload documents to get started."
    return f"{count} chunks in SOC memory | Model: {LLM_MODEL} | Embedder: all-MiniLM-L6-v2"


# ── UI ─────────────────────────────────────────────────────────────────────────

with gr.Blocks(title=UI_TITLE) as demo:
    gr.Markdown(f"# SOC Intelligence Mode\n{UI_DESCRIPTION}")

    with gr.Tabs():

        with gr.Tab("SOC Chat"):
            gr.Markdown(get_status())
            chatbot = gr.Chatbot(height=520, render_markdown=True, label="SOC Analyst AI")
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Describe an incident, paste an IOC, or ask about your documents...",
                    show_label=False, scale=5
                )
                send_btn = gr.Button("Analyze", variant="primary", scale=1)
            gr.ClearButton([msg, chatbot], value="Clear session")
            send_btn.click(chat, [msg, chatbot], [msg, chatbot])
            msg.submit(chat, [msg, chatbot], [msg, chatbot])

        with gr.Tab("Add Intelligence"):
            gr.Markdown("### Upload SOC Documents\nSOC notes, incident reports, text logs, threat intel.")
            file_input = gr.File(
                label="Select files",
                file_count="multiple",
                file_types=[".pdf", ".txt", ".md", ".docx", ".log", ".csv"],
            )
            file_btn = gr.Button("Store in SOC Memory", variant="primary")
            file_status = gr.Textbox(label="Status", interactive=False)
            file_btn.click(ingest_files, [file_input], [file_status])

            gr.Markdown("---\n### Ingest a URL")
            url_input = gr.Textbox(label="URL", placeholder="https://example.com/threat-report")
            url_btn = gr.Button("Ingest URL", variant="secondary")
            url_status = gr.Textbox(label="Status", interactive=False)
            url_btn.click(ingest_url, [url_input], [url_status])

        with gr.Tab("Config"):
            gr.Markdown(f"""
| Setting | Value |
|---|---|
| LLM Model | `{LLM_MODEL}` |
| Embedder | `all-MiniLM-L6-v2` |
| Ollama URL | `{OLLAMA_BASE_URL}` |
| Chunks retrieved | `{NUM_CHUNKS}` |
| Vector DB path | `{CHROMA_DIR}` |
            """)

if __name__ == "__main__":
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        print(f"Ollama running at {OLLAMA_BASE_URL}")
    except Exception:
        print("WARNING: Ollama not reachable — run: ollama serve")
    print(f"SOC memory loaded: {collection.count()} chunks")
    demo.launch(
        server_port=UI_PORT,
        share=UI_SHARE,
        inbrowser=True,
        theme=gr.themes.Soft(primary_hue="emerald"),
    )
