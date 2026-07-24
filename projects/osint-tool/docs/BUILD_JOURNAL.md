# Build Journal

> Engineering diary documenting every session, decision, failure, and fix building this tool from scratch.

---

## Session 1 — Project Setup and Initial Scaffold

**Date:** 2026-07-22
**Objective:** Create a working FastAPI app with a dark terminal UI and stub OSINT logic

### What Was Done

```bash
mkdir ~/osint-tool && cd ~/osint-tool
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic requests python-multipart
```

**Why a virtual environment?**
Sherlock and Maigret install CLI executables alongside their Python packages. A venv keeps them isolated from system Python and from PrivateGPT's own environment, preventing version conflicts.

### Files Created

- `main.py` — FastAPI app with CORS middleware, SQLite setup, stub lookup logic, 4 API routes, full HTML frontend
- `start.sh` — launches uvicorn with `--reload`
- `.gitignore` — excludes venv/, osint.db, .env

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS osint_results (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    query     TEXT NOT NULL,
    source    TEXT NOT NULL,
    result    TEXT,
    timestamp TEXT DEFAULT (datetime('now'))
);
```

The `result` column stores the full findings as a JSON string. This avoids schema migrations as findings structure evolves — new fields just appear in the JSON blob.

### First Run

```
INFO: Uvicorn running on http://0.0.0.0:8000
```

Dashboard loaded. Dark terminal theme confirmed. Chart.js doughnut rendering. SQLite writing. All routes responding.

### Lessons

- `python-multipart` is required by FastAPI even when not using file uploads — include it in requirements from the start
- `conn.row_factory = sqlite3.Row` enables dict-like row access (`row["column"]`) — much cleaner than index-based access

---

## Session 2 — Sherlock Integration

**Date:** 2026-07-22
**Objective:** Replace stub username logic with real Sherlock output

### Installation and Test

```bash
pip install sherlock-project
sherlock testuser123 --print-found
```

Result: **131 platforms found** including YouTube, GitHub, WordPress, Reddit, Tumblr, and more.

### Integration Approach

Sherlock is a CLI tool. The cleanest integration is `subprocess.run()` with stdout parsing:

```python
proc = subprocess.run(
    ["sherlock", username, "--print-found", "--timeout", "10"],
    capture_output=True,
    text=True,
    timeout=120,
)
```

Every found account prints as `[+] Platform: URL`. Parse with regex:

```python
for line in proc.stdout.splitlines():
    match = re.match(r"\[\+\]\s+(.+?):\s+(https?://\S+)", line)
    if match:
        findings.append({
            "tool":     "sherlock",
            "type":     "username_found",
            "platform": match.group(1).strip(),
            "url":      match.group(2).strip(),
        })
```

### Error Handling

Three cases handled explicitly:

```python
except subprocess.TimeoutExpired:
    # Sherlock hung — 120s hard limit
except FileNotFoundError:
    # Sherlock not installed
except Exception as e:
    # Anything else
```

### What Worked Immediately

- `--print-found` suppresses negative results — output stays clean and parseable
- `--timeout 10` per-site timeout keeps total wall time reasonable
- `capture_output=True` prevents Sherlock's progress output from polluting the terminal

---

## Session 3 — Maigret Integration

**Date:** 2026-07-22
**Objective:** Add Maigret for richer username intelligence

### Installation

```bash
pip install maigret
```

### First Failure — Wrong Flag

```bash
maigret testuser123 --print-found
# maigret: error: unrecognized arguments: --print-found
```

`--print-found` is a Sherlock flag. Maigret shows found accounts by default. The equivalent in Maigret is `--print-not-found` to show misses (opposite convention).

### Correct Command

```bash
maigret testuser123 --top-sites 50 --no-color --no-progressbar
```

### What Maigret Returns (vs Sherlock)

Sherlock: list of `[+] Platform: URL` lines
Maigret: summary report with:

```
Search by username testuser123 returned 23 accounts.
Extended info extracted from 19 accounts.
Countries: in, us, ru, cn
Interests (tags): social, messaging, business, coding, gaming, streaming
Extracted IDs: {'testuser1231234': 'username'}
```

Maigret is significantly richer — geographic distribution, interest categories, and alternate IDs discovered through profile cross-referencing.

### Parsing the Text Report

```python
# Account count
count_match   = re.search(r"Search by username \S+ returned (\d+) accounts", output)

# Countries
country_match = re.search(r"Countries:\s+(.+)", output)

# Interests
interest_match = re.search(r"Interests \(tags\):\s+(.+)", output)

# Alternate IDs (Maigret discovers linked usernames automatically)
id_match = re.search(r"Extracted IDs:\s+(\{.+?\})", output)
```

### Bot Protection Errors Observed

```
[!] Too many errors of type "Bot protection" (5.17%)
[!] Too many errors of type "Access denied" (5.17%)
```

This is what led directly to Tor integration in Session 5.

---

## Session 4 — Parallel Execution

**Date:** 2026-07-22
**Objective:** Run Sherlock and Maigret simultaneously instead of sequentially

### The Problem

Running sequentially:
- Sherlock: ~60–90s
- Maigret: ~90–120s
- Total: ~210s

That's too slow for an interactive tool.

### Solution — ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {
        executor.submit(run_sherlock, username):           "sherlock",
        executor.submit(run_maigret,  username, use_tor): "maigret",
    }
    for future in as_completed(futures):
        tool   = futures[future]
        result = future.result()
        if tool == "sherlock":
            sherlock_findings = result
        else:
            maigret_result = result
```

**Why ThreadPoolExecutor instead of asyncio?**
Both Sherlock and Maigret run as subprocesses — they are blocking operations. `asyncio` won't help with blocking calls unless you use `asyncio.create_subprocess_exec`. `ThreadPoolExecutor` is simpler and correct for this use case.

**Result:** Total wall time dropped to ~120s — limited by whichever tool finishes last.

### Result Merging

Results are ordered intentionally:

```
1. Maigret meta findings (tor_status, summary, geo)  ← context first
2. Sherlock platform hits                             ← bulk of findings
3. Maigret tail (interests, alternate IDs)            ← enrichment last
```

### Risk Scoring

```python
total_hits = max(sherlock_hits, maigret_hits)  # max() avoids double-counting
risk_score = min(100, total_hits * 3)           # cap at 100
```

Using `max()` instead of addition prevents inflating the score when both tools find the same platform.

---

## Session 5 — Tor Integration

**Date:** 2026-07-22
**Objective:** Route Maigret through Tor to bypass bot protection and anonymize lookups

### Tor Installation

```bash
sudo apt install tor torsocks -y
sudo systemctl start tor@default
sudo systemctl enable tor@default
```

### Critical Discovery — Wrong Service Unit

```bash
sudo systemctl status tor
# Active: active (exited)
# Process: ExecStart=/bin/true
```

`tor.service` is a multi-instance master unit. Its `ExecStart` is literally `/bin/true` — it does nothing. The actual Tor daemon runs as `tor@default.service`:

```bash
sudo systemctl status tor@default
# Active: active (running)
# Bootstrapped 100% (done)
```

### Tor Verification

```bash
curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip
# {"IsTor":true,"IP":"45.84.107.76"}
```

Confirmed anonymous exit IP.

### check_tor() Function

Before every Maigret run, verify Tor is actually routing traffic:

```python
def check_tor() -> dict:
    try:
        resp = http_requests.get(
            "https://check.torproject.org/api/ip",
            proxies={"https": TOR_PROXY, "http": TOR_PROXY},
            timeout=15,
        )
        data = resp.json()
        return {
            "running": data.get("IsTor", False),
            "ip":      data.get("IP", "unknown"),
            "proxy":   TOR_PROXY,
        }
    except Exception as e:
        return {"running": False, "ip": None, "error": str(e)}
```

If Tor is unreachable — Maigret falls back to direct connection and the UI shows a warning badge.

### Passing Tor to Maigret

```python
if use_tor and tor_status["running"]:
    cmd += ["--tor-proxy", TOR_PROXY]
    # Final command: maigret username --tor-proxy socks5://127.0.0.1:9050 --top-sites 100
```

### UI Additions

- **Header badge** — `Tor ✓` (purple) or `Tor ✗` (gray) with live exit IP
- **Per-lookup toggle** — checkbox to enable/disable Tor per search
- **Results output** — shows `🧅 via Tor 45.84.107.76` next to Maigret hit count
- **History cards** — `🧅` icon on lookups that used Tor
- **`/api/tor-status` endpoint** — polled on page load to populate the badge

### python-dotenv Added

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()
HIBP_API_KEY      = os.getenv("HIBP_API_KEY", "")
NUMVERIFY_API_KEY = os.getenv("NUMVERIFY_API_KEY", "")
TOR_PROXY         = os.getenv("TOR_PROXY", "socks5://127.0.0.1:9050")
```

---

## Session 6 — HIBP and NumVerify Integrations

**Date:** 2026-07-22
**Objective:** Add real email breach and phone number lookups

### HaveIBeenPwned

API v3 requires a paid key ($3.50/mo). Response codes:

| Code | Meaning |
|---|---|
| 200 | Breaches found — returns JSON array |
| 404 | Clean — no breaches |
| 401 | Invalid API key |
| 429 | Rate limited — one request per 1500ms enforced server-side |

```python
resp = http_requests.get(
    f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
    headers={"hibp-api-key": HIBP_API_KEY, "user-agent": "OSINT-Tool/1.0"},
    timeout=10,
)
```

Risk score formula: `min(100, 20 + breach_count * 15)` — each breach adds 15 points.

### NumVerify

Free tier (250 req/month) uses HTTP not HTTPS — the API key is transmitted in plaintext. Noted as a future improvement to replace with a HTTPS-capable alternative.

```python
resp = http_requests.get(
    "http://apilayer.net/api/validate",
    params={"access_key": NUMVERIFY_API_KEY, "number": clean_phone, "format": 1},
    timeout=10,
)
```

Returns: country, carrier, line type (mobile/landline/voip), location, international format.

Risk: 60 for mobile (more OSINT-valuable), 35 for landline/voip.

---

## Session 7 — Deployment Fixes

**Date:** 2026-07-22
**Objective:** Resolve port conflicts and file overwrite issues during iterative development

### Port Already in Use

```
ERROR: [Errno 98] Address already in use
```

Cause: uvicorn process still holding the socket after `pkill`. The kernel holds the binding briefly after process exit.

Fix:
```bash
sudo fuser -k 8000/tcp
sleep 2
./start.sh
```

### Cannot Overwrite Existing Files

```bash
cat > start.sh << 'EOF'
# bash: start.sh: cannot overwrite existing file
```

Cause: Shell `noclobber` option (`set -C`) prevents `>` redirection from overwriting files.

Fix: Use `tee` which bypasses noclobber:
```bash
tee start.sh << 'EOF'
...
EOF
```

### Old UI Showing After Code Update

Cause: uvicorn process was still the old instance started days earlier. The `--reload` flag watches for file changes but the process itself was stale.

Fix:
```bash
sudo fuser -k 8000/tcp  # kill the old process
sleep 2
./start.sh              # start fresh
# Then Ctrl+Shift+R in browser for hard refresh
```

---

## Final Stack

| Service | Port | Status |
|---|---|---|
| OSINT Tool (uvicorn) | 8000 | Manual start via `./start.sh` |
| Tor daemon | 9050 | Auto-start via `tor@default.service` |
| PrivateGPT (separate project) | 8080 | Manual start |
| Qdrant Docker (separate project) | 6333/6334 | Auto-start via Docker |
| Ollama (separate project) | 11434 | System service |
