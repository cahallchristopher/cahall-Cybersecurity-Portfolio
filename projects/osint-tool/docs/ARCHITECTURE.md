# Architecture

> Design decisions, data flow, and system structure.

---

## Design Philosophy

Single-file FastAPI application. Everything -- API routes, OSINT logic,
database, HTML frontend, CSS, and JavaScript -- lives in main.py.
Easy to deploy, version, and read end-to-end.

Local-first, privacy-first. No data leaves the machine except the
lookup queries themselves.

---

## Component Map

```
main.py
|
|-- Config & Constants
|   |-- DB_PATH, HIBP_API_KEY, NUMVERIFY_API_KEY, TOR_PROXY
|
|-- Database Layer
|   |-- get_db()          -- connection with row_factory
|   `-- create_database() -- idempotent table creation
|
|-- Pydantic Models
|   `-- LookupRequest     -- query, source, notes, use_tor
|
|-- OSINT Integrations
|   |-- check_tor()           -- verify Tor before Maigret
|   |-- run_sherlock()        -- subprocess, regex parse [+] lines
|   |-- run_maigret()         -- subprocess + Tor, parse text report
|   |-- lookup_username()     -- parallel ThreadPoolExecutor, merge
|   |-- lookup_email_hibp()   -- HIBP API v3
|   |-- lookup_phone_numverify() -- NumVerify API
|   `-- lookup_name()         -- generate search links
|
|-- Router
|   `-- perform_lookup()  -- dispatch by source type
|
|-- FastAPI Routes
|   |-- POST   /api/lookup
|   |-- GET    /api/history
|   |-- GET    /api/stats
|   |-- GET    /api/tor-status
|   `-- DELETE /api/history/{id}
|
`-- Frontend (inline HTML string)
    |-- CSS  -- dark terminal theme
    |-- HTML -- two-column layout
    `-- JS   -- fetch API, Chart.js, Tor toggle
```

---

## Data Flow -- Username Lookup

```
POST /api/lookup {query: "target", source: "username", use_tor: true}
        |
        v
perform_lookup() --> lookup_username()
        |
        v
ThreadPoolExecutor(max_workers=2)
    |                           |
    v                           v
run_sherlock("target")      run_maigret("target", use_tor=True)
    |                           |
    |                      check_tor() --> verify via Tor Project API
    |                           |
    |                      maigret --tor-proxy socks5://127.0.0.1:9050
    |                           |
    v                           v
Parse [+] Platform: URL     Parse text report:
                            accounts, countries,
                            interests, alt IDs
    |                           |
    `-----------+---------------'
                |
                v
        merge_results()
        risk_score = min(100, max(sherlock, maigret) * 3)
                |
                v
        INSERT INTO osint_results
                |
                v
        return JSON to browser
```

---

## Concurrency Model

ThreadPoolExecutor with max_workers=2 is correct here because:
1. Both tasks are I/O bound (subprocess + network) not CPU bound
2. Python GIL does not block I/O threads
3. as_completed() processes results as they finish

Time saved: ~90s per lookup (210s sequential --> 120s parallel)

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS osint_results (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    query     TEXT NOT NULL,
    source    TEXT NOT NULL,
    result    TEXT,              -- full JSON blob
    timestamp TEXT DEFAULT (datetime("now"))
);
```

The result column stores complete findings as JSON.
No schema migrations needed as findings structure evolves.

---

## Risk Scoring

Username:  risk_score = min(100, max(sherlock_hits, maigret_hits) * 3)
Email:     risk_score = min(100, 20 + breach_count * 15)
Phone:     risk_score = 60 if mobile else 35
Name:      risk_score = 15 (manual links only)

Thresholds: LOW 0-29 | MEDIUM 30-59 | HIGH 60-100

---

## Engineering Decisions

| Decision | Reason |
|---|---|
| FastAPI over Flask | Pydantic validation, auto /docs |
| SQLite over PostgreSQL | Zero infrastructure, single-user |
| Single main.py | Easy to deploy and read |
| ThreadPoolExecutor | Correct for blocking subprocesses |
| max() for deduplication | Prevents score inflation |
| Sherlock direct, Maigret via Tor | Speed vs anonymization tradeoff |
| check_tor() before every run | No silent fallback to direct |
| Inline HTML | No build step, fully portable |
