# Architecture

> Design decisions, data flow, and system structure for the OSINT People & Identity Lookup Tool.

---

## Design Philosophy

**Single-file FastAPI application.** Everything — API routes, OSINT logic, database, HTML frontend, CSS, and JavaScript — lives in one file (`main.py`). This makes the tool trivially easy to deploy (clone, install deps, run one command) and fully readable end-to-end without jumping between files.

**Local-first, privacy-first.** No data leaves the machine except the lookup queries themselves (which are the point). No cloud LLM, no remote database, no telemetry.

---

## Component Map

```
main.py
│
├── Config & Constants
│   ├── DB_PATH              ← SQLite file path
│   ├── HIBP_API_KEY         ← from .env
│   ├── NUMVERIFY_API_KEY    ← from .env
│   └── TOR_PROXY            ← socks5://127.0.0.1:9050 (from .env or default)
│
├── Database Layer
│   ├── get_db()             ← connection with row_factory for dict-like access
│   └── create_database()    ← idempotent table creation on startup
│
├── Pydantic Models
│   └── LookupRequest        ← query, source, notes, use_tor
│
├── OSINT Integrations
│   ├── check_tor()          ← verify Tor via Tor Project API before Maigret
│   ├── run_sherlock()       ← subprocess, parse [+] Platform: URL lines
│   ├── run_maigret()        ← subprocess + optional Tor, parse text report
│   ├── lookup_username()    ← parallel ThreadPoolExecutor, merge results
│   ├── lookup_email_hibp()  ← HIBP API v3 breach check
│   ├── lookup_phone_numverify() ← NumVerify carrier/country enrichment
│   └── lookup_name()        ← generate targeted search links
│
├── Router
│   └── perform_lookup()     ← dispatch by source type
│
├── FastAPI Routes
│   ├── POST   /api/lookup
│   ├── GET    /api/history
│   ├── GET    /api/stats
│   ├── GET    /api/tor-status
│   └── DELETE /api/history/{id}
│
└── Frontend (inline HTML string)
    ├── CSS    ← dark terminal theme, CSS variables
    ├── HTML   ← two-column layout, form, result box, history, chart
    └── JS     ← fetch API calls, renderResult(), Chart.js, Tor toggle
```

---

## Data Flow — Username Lookup

```
POST /api/lookup
  {"query": "target", "source": "username", "use_tor": true}
        │
        ▼
perform_lookup() → lookup_username()
        │
        ▼
ThreadPoolExecutor(max_workers=2)
    │                               │
    ▼                               ▼
run_sherlock("target")          run_maigret("target", use_tor=True)
    │                               │
    │                          check_tor()
    │                               │
    │                          GET https://check.torproject.org/api/ip
    │                               via socks5://127.0.0.1:9050
    │                               │
    │                          {"IsTor": true, "IP": "45.84.107.76"}
    │                               │
    │                          cmd = ["maigret", "target",
    │                                 "--tor-proxy", "socks5://...",
    │                                 "--top-sites", "100",
    │                                 "--no-color", "--no-progressbar"]
    │                               │
    ▼                               ▼
subprocess.run(                 subprocess.run(
  ["sherlock", "target",          cmd,
   "--print-found",               timeout=240
   "--timeout", "10"],          )
  timeout=120                       │
)                                   │ parse text report:
    │                               │   accounts, countries,
    │ parse stdout:                 │   interests, alt IDs
    │   [+] Platform: URL          │
    │                               │
    └──────────┬─────────────────── ┘
               │
               ▼
        merge_results()
          maigret_meta + sherlock_hits + maigret_tail
          risk_score = min(100, max(sherlock_hits, maigret_hits) * 3)
          summary = "N platforms · geo: US,RU · via Tor x.x.x.x"
               │
               ▼
        INSERT INTO osint_results (query, source, result JSON)
               │
               ▼
        return JSON response to browser
```

---

## Concurrency Model

`ThreadPoolExecutor` with `max_workers=2` is the correct tool here because:

1. Both tasks are **I/O-bound** (subprocess execution + network) not CPU-bound
2. Python's GIL doesn't block I/O threads
3. `as_completed()` processes results as they finish rather than waiting for both

```python
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {
        executor.submit(run_sherlock, username):           "sherlock",
        executor.submit(run_maigret,  username, use_tor): "maigret",
    }
    for future in as_completed(futures):
        tool   = futures[future]
        result = future.result()
```

**Why not asyncio?** Subprocesses are blocking. To use asyncio correctly you would need `asyncio.create_subprocess_exec` and `await proc.communicate()`. `ThreadPoolExecutor` achieves the same parallelism with simpler code.

**Time saved:** ~90s per lookup (210s sequential → 120s parallel)

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS osint_results (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    query     TEXT NOT NULL,
    source    TEXT NOT NULL,
    result    TEXT,              -- full JSON blob
    timestamp TEXT DEFAULT (datetime('now'))
);
```

The `result` column stores the complete findings as a JSON string. This is intentional — it avoids schema migrations as the findings structure evolves. New fields (e.g., `tor_ip`, `alternate_ids`) appear in the JSON without touching the table schema.

---

## Frontend Architecture

No build step. No framework. Vanilla ES6 with Chart.js from CDN.

```
Page Load
    ├── checkTorStatus() → GET /api/tor-status
    │       └── Update header badge + status bar text
    ├── loadHistory() → GET /api/history?limit=20
    │       └── Render history cards with risk badges + Tor icons
    └── loadChart() → GET /api/stats
            └── Render doughnut chart (source breakdown)

User submits lookup
    ├── POST /api/lookup (wait 90-120s)
    ├── renderResult(data) → populate result box with formatted output
    ├── loadHistory() → refresh history panel
    └── loadChart() → refresh chart
```

### Result Rendering

The result box uses a pre-formatted terminal-style output:

```
QUERY:      targetusername
SOURCE:     username
RISK SCORE: 63/100 [HIGH]
SUMMARY:    21 platforms found · geo: US,RU · via Tor 45.84.107.76

TOOLS:
  Sherlock : 18 platforms (direct)
  Maigret  : 21 platforms (🧅 via Tor 45.84.107.76)
  Countries: US, RU, DE
  Interests: social, coding, gaming

──────────────────────────────────────────────────────────
FINDINGS (45):

  [MAIGRET ] [🧅] tor_status             Routing through Tor — exit IP: 45.84.107.76
  [MAIGRET ] [-]  summary                Found 21 accounts across checked platforms
  [SHERLOCK] [+]  GitHub                 https://github.com/targetusername
  [SHERLOCK] [+]  Twitter               https://twitter.com/targetusername
  ...
```

---

## Risk Scoring

```
Username:  risk_score = min(100, max(sherlock_hits, maigret_hits) * 3)
Email:     risk_score = min(100, 20 + breach_count * 15)
Phone:     risk_score = 60 if mobile else 35
Name:      risk_score = 15 (manual links only, no automated check)
```

Thresholds:
- **LOW** — 0–29 (green)
- **MEDIUM** — 30–59 (amber)
- **HIGH** — 60–100 (red)

---

## Security Boundaries

```
┌─────────────────────────────────────────────────────────┐
│  YOUR MACHINE (localhost)                               │
│                                                         │
│  FastAPI :8000                                          │
│      │                                                  │
│      ├── Sherlock ──► direct HTTPS ──► target platforms │
│      │   (your real IP visible to platforms)            │
│      │                                                  │
│      ├── Maigret ──► socks5://127.0.0.1:9050            │
│      │                   │                              │
│      │              Tor Daemon                          │
│      │                   │                              │
│      │              Tor Network                         │
│      │                   │                              │
│      │              Exit Node ──► target platforms      │
│      │              (exit IP visible, not yours)        │
│      │                                                  │
│      ├── HIBP API ──► HTTPS ──► haveibeenpwned.com      │
│      │   (your IP + email visible to HIBP)              │
│      │                                                  │
│      └── NumVerify ──► HTTP ──► apilayer.net            │
│          (your IP + phone + API key in plaintext ⚠)    │
│                                                         │
│  SQLite ──► local file only, never transmitted          │
└─────────────────────────────────────────────────────────┘
```

---

## Engineering Decisions

| Decision | Reason | Trade-off |
|---|---|---|
| FastAPI over Flask | Pydantic validation, auto `/docs`, cleaner async | Slightly more verbose for simple routes |
| SQLite over PostgreSQL | Zero infrastructure, single-user | Not safe for concurrent writes |
| Single `main.py` | Easy to deploy and read | Harder to unit test in isolation |
| `ThreadPoolExecutor` | Correct for blocking subprocesses | More RAM than asyncio |
| `max()` for deduplication | Prevents score inflation | Undercounts if tools find different platforms |
| Sherlock direct, Maigret via Tor | Speed vs anonymization trade-off | Sherlock still exposes real IP |
| `check_tor()` before every run | No silent fallback to direct | Adds ~2s overhead per lookup |
| Inline HTML | No build step, fully portable | HTML/JS mixed with Python |
| JSON blob in SQLite | Schema-free findings evolution | No SQL queries on findings fields |
