# PrivateGPT Local — SOC Intelligence Mode
### Build Notes by Christopher
---

## What I Built

A fully local, private AI assistant that can read and reason over documents — no internet connection required, nothing leaves the machine. Upgraded with SOC (Security Operations Center) intelligence features including MITRE ATT&CK auto-tagging and structured incident analysis.

**Stack:**
- **LLM:** Ollama running `dolphin-llama3` locally
- **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`) running locally
- **Vector Store:** ChromaDB (persistent local database)
- **RAG Pipeline:** Custom Python — no LangChain dependency in final version
- **UI:** Gradio web interface at `localhost:7860`
- **Document Support:** PDF, DOCX, TXT, MD, logs, URLs

---

## Why I Built It

Inspired by the PrivateGPT project (ODSC conference video). Wanted a 100% local alternative to ChatGPT that could reason over my own documents — security notes, threat intel, job research — without sending data to any external API.

---

## Environment

- **OS:** Ubuntu Linux (Desktop)
- **GPU:** NVIDIA (detected and used automatically by Ollama)
- **Python:** 3.11 via Miniconda
- **Conda env:** `privategpt` (isolated — no interference with other projects)

---

## Phase 1 — Wipe Ollama and Start Clean

The goal was a completely fresh Ollama install with no leftover models.

### Problem
Running `ollama list` showed 7 models (~38GB total) from previous experiments. Standard `rm -rf ~/.ollama` didn't work because the systemd service installs Ollama as its own user and stores models at a different path.

### Solution
```bash
# Stop the service
sudo systemctl stop ollama

# Remove binary and service file
sudo rm -f /usr/local/bin/ollama
sudo rm -f /etc/systemd/system/ollama.service

# This didn't work — models were NOT in ~/.ollama
rm -rf ~/.ollama

# Fresh install
curl -fsSL https://ollama.com/install.sh | sh
```

### Key Discovery
When Ollama is installed as a **systemd service**, it runs as the `ollama` system user and stores models at:
```
/usr/share/ollama/.ollama/models
```
NOT at `~/.ollama/models` as you'd expect.

```bash
# Correct wipe command
sudo rm -rf /usr/share/ollama/.ollama/models
sudo systemctl restart ollama
ollama list  # now blank
```

### Reinstall confirmed NVIDIA GPU
```
>>> NVIDIA GPU installed.
```
Ollama automatically uses the GPU — no configuration needed.

---

## Phase 2 — Pull Only the Models Needed

```bash
ollama serve &
ollama pull dolphin-llama3      # 4.7GB — the LLM
ollama pull nomic-embed-text    # 274MB — embeddings (later replaced)
```

**Why `dolphin-llama3`?**
- Based on Llama 3.1 8B — same architecture the PrivateGPT tutorial uses
- Uncensored variant — better for security research use cases
- Runs fully on the NVIDIA GPU

---

## Phase 3 — Project Folder and Python Environment

```bash
# Create isolated project folder
mkdir -p ~/privategpt-local && cd ~/privategpt-local

# Create a clean conda environment — Python 3.11 only
conda create -n privategpt python=3.11 -y
conda activate privategpt
```

**Why a separate conda env?**
Keeps all project dependencies isolated. Doesn't touch the base conda install or any other project environments.

---

## Phase 4 — Install Dependencies

### Problem 1 — Wrong requirements.txt
The first `cp ~/Downloads/requirements.txt .` grabbed the wrong file — a Flask authentication project that had also been in Downloads. Installed `flask-limiter`, `webauthn`, `qrcode` etc. — completely wrong packages.

### Fix
Wrote the correct `requirements.txt` directly:
```bash
cat > requirements.txt << 'EOF'
langchain>=0.2.0
langchain-community>=0.2.0
langchain-ollama>=0.1.0
chromadb>=0.5.0
pypdf>=4.0.0
python-docx>=1.1.0
beautifulsoup4>=4.12.0
requests>=2.31.0
lxml>=5.0.0
gradio>=4.40.0
rich>=13.0.0
tqdm>=4.66.0
EOF

pip install -r requirements.txt
```

Later added:
```bash
pip install sentence-transformers
```

---

## Phase 5 — The Five Core Scripts

### `config.py`
Single file for all settings. Change models, chunk sizes, ports, prompts — all in one place.

Key settings:
```python
LLM_MODEL    = "dolphin-llama3"
EMBED_MODEL  = "nomic-embed-text"
CHROMA_DIR   = "./chroma_db"
CHUNK_SIZE   = 1000
CHUNK_OVERLAP = 200
NUM_CHUNKS   = 4
```

### `ingest.py`
Loads documents into ChromaDB. Supports:
- **PDF** — via `pypdf`
- **DOCX** — via `python-docx`
- **TXT / MD** — plain text read
- **URLs** — fetched with `requests`, parsed with `BeautifulSoup`

Splits text into overlapping chunks, embeds them, stores in ChromaDB.

```bash
# Usage
python ingest.py --source ./docs/         # folder
python ingest.py --source ./file.pdf      # single file
python ingest.py --url https://example.com
python ingest.py --list                   # see what's stored
python ingest.py --reset                  # wipe everything
```

### `chat.py`
Terminal-based chat. No browser needed. Uses `rich` for formatted markdown output in the terminal. Maintains conversation history (last 10 turns).

### `app.py`
Gradio web UI at `http://localhost:7860`.

---

## Phase 6 — Gradio Compatibility Fix

### Problem
The scripts were written for Gradio 4.x but the installed version was **Gradio 6.x** which had breaking changes:

```
TypeError: Chatbot.__init__() got an unexpected keyword argument 'bubble_full_width'
UserWarning: theme parameter moved from Blocks to launch()
```

### Fixes Applied
1. Removed `bubble_full_width=False` from `gr.Chatbot()`
2. Moved `theme=gr.themes.Soft(primary_hue="emerald")` from `gr.Blocks()` to `demo.launch()`
3. Removed extra parameters from `gr.Blocks()` constructor

### Lesson
Always check Gradio version compatibility. Gradio 6.0 introduced breaking changes to several component APIs.

---

## Phase 7 — Wrong app.py (Again)

### Problem
A second wrong file from Downloads — another Flask app — got copied as `app.py`.

```
TypeError: Limiter.__init__() got multiple values for argument 'key_func'
```

### Fix
Opened `gedit` as root to directly edit the correct file:
```bash
sudo gedit /home/chris/privategpt-local/app.py
```
Replaced content with the correct Gradio-based `app.py`.

---

## Phase 8 — Upgrade to SOC Intelligence Mode

Upgraded `app.py` from basic RAG to a full SOC analyst assistant.

### Changes

**Replaced Ollama embedder with sentence-transformers:**
```python
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer("all-MiniLM-L6-v2")
```
Runs 100% locally, faster, no Ollama dependency for embeddings.

**Added MITRE ATT&CK Auto-Tagger:**
```python
MITRE_RULES = [
    (["phishing", "spear", "lure"],          "T1566 - Phishing"),
    (["powershell", "cmd", "script"],        "T1059 - Command & Scripting Interpreter"),
    (["credential", "password", "hash"],     "T1555 - Credentials from Password Stores"),
    (["lateral", "pivot", "smb", "rdp"],    "T1021 - Remote Services"),
    (["exfil", "c2", "beacon"],             "T1041 - Exfiltration Over C2 Channel"),
    (["privilege", "escalat", "sudo"],      "T1068 - Privilege Escalation"),
    (["persist", "cron", "registry"],       "T1547 - Boot/Logon Autostart Execution"),
    (["scan", "nmap", "recon"],             "T1046 - Network Service Discovery"),
    (["malware", "dropper", "inject"],      "T1055 - Process Injection"),
    (["ransomware", "encrypt", "ransom"],   "T1486 - Data Encrypted for Impact"),
]
```

**SOC-structured prompt:**
Every query returns:
1. Incident Summary
2. Security Analysis
3. MITRE ATT&CK Mapping
4. Recommended Actions

---

## Phase 9 — Profile Documents for Job Application

Created three 250-word profile documents and ingested them into the vector store to use the system itself for job application research.

| File | Contents |
|---|---|
| `christopher-skills.txt` | Full technical skill set |
| `christopher-projects.txt` | Vulnerability scanner, NMP hack, file detector, hardening guide |
| `christopher-match-analysis.txt` | Point-by-point match against Hiring.Cafe role |

```bash
python ingest.py --source ./docs/
```

Now the system can answer questions like:
- *"What makes Christopher a strong fit for this role?"*
- *"What security experience does Christopher have?"*
- *"How does Christopher's background match the Hiring.Cafe requirements?"*

---

## Final File Structure

```
~/privategpt-local/
├── app.py                          # Gradio web UI — SOC mode
├── chat.py                         # Terminal chat interface
├── config.py                       # All settings
├── ingest.py                       # Document ingestion pipeline
├── requirements.txt                # Python dependencies
├── chroma_db/                      # Persistent vector database
└── docs/
    ├── hiring-cafe-job.txt
    ├── christopher-skills.txt
    ├── christopher-projects.txt
    └── christopher-match-analysis.txt
```

---

## How to Run

```bash
# Terminal 1 — keep Ollama running
ollama serve

# Terminal 2 — activate env and launch
cd ~/privategpt-local
conda activate privategpt
python ingest.py --source ./docs/   # only needed once per new doc
python app.py                        # opens http://localhost:7860
```

---

## Key Lessons Learned

1. **Ollama systemd installs store models at `/usr/share/ollama/.ollama/models`** — not `~/.ollama`
2. **Always use a separate conda env** — prevents dependency conflicts with other projects
3. **Gradio 6.x has breaking API changes** from 4.x — `theme` moves to `launch()`, `bubble_full_width` removed
4. **Keep Downloads folder clean** — multiple projects' files with same names cause copy mistakes
5. **sentence-transformers is faster and simpler** than routing embeddings through Ollama
6. **MITRE ATT&CK tagging** can be done with simple keyword rules — no ML needed for baseline coverage
7. **heredoc (`<< EOF`) in terminal can mangle code** — use gedit or write files with Python instead

---

## What to Build Next

- [ ] Add PDF support to the SOC UI file uploader
- [ ] Add model switcher dropdown in UI (toggle between dolphin-llama3 and other installed models)
- [ ] Add conversation export (save chat sessions as markdown)
- [ ] Add IOC extractor (auto-pull IPs, domains, hashes from ingested docs)
- [ ] Add a `/search` endpoint so other tools can query the vector store via API
