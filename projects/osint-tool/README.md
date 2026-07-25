# OSINT People & Identity Lookup Tool

> A fully local, privacy-focused OSINT web application for people and identity investigations.
> Built with FastAPI, Sherlock, Maigret, and Tor. No cloud dependencies. All data stays on your machine.

![Red Team](https://img.shields.io/badge/purpose-red%20team-red)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Tor](https://img.shields.io/badge/anonymized-Tor-purple)

---

## What This Is

A single-page web dashboard for running OSINT lookups against people and identities.
Type a username, email, phone number, or full name — the tool runs Sherlock and Maigret
in parallel, stores results locally in SQLite, and renders everything in a dark terminal-style UI.

Built for red team operations, penetration testing, and security research.

---

## Features

- **Username hunting** via Sherlock (400+ platforms) and Maigret (100+ platforms) running in **parallel**
- **Tor anonymization** — Maigret routes all requests through `socks5://127.0.0.1:9050`
- **Live Tor status** in the UI — shows exit IP, auto-disables if Tor is down
- **Per-lookup Tor toggle** — enable or disable anonymization per search
- **Email breach checking** via HaveIBeenPwned API v3
- **Phone number enrichment** via NumVerify (carrier, country, line type)
- **Full name lookup** — generates targeted search links (Google, LinkedIn, Pipl, PeekYou)
- **SQLite persistence** — all results stored locally with history and delete
- **Risk scoring** (0-100) based on platform exposure and breach severity
- **Chart.js doughnut chart** — source breakdown across all lookups
- **No cloud dependencies** — everything runs on localhost

---

## Architecture

```
Browser (http://localhost:8000)
        |
        v
FastAPI + Uvicorn (:8000)
        |
        |-- ThreadPoolExecutor (max_workers=2)
        |       |-- Sherlock --> direct HTTPS --> 400+ platforms
        |       `-- Maigret --> Tor :9050 --> 100+ platforms (anonymized)
        |
        |-- SQLite (osint.db) -- store all results locally
        |-- HIBP API          -- email breach check (keyed)
        `-- NumVerify API     -- phone enrichment (keyed)
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | FastAPI 0.115 |
| ASGI server | Uvicorn 0.30 |
| Username OSINT | Sherlock (400+ platforms, direct) |
| Username OSINT+ | Maigret (100+ platforms, enriched metadata) |
| Anonymization | Tor (tor@default.service, SOCKS5 :9050) |
| Email breach | HaveIBeenPwned API v3 |
| Phone lookup | NumVerify API |
| Database | SQLite (built-in, fully local) |
| Frontend | Vanilla JS + Chart.js (CDN) |
| Language | Python 3.11 (venv) |

---

## Quick Start

### 1. Install Tor

```bash
sudo apt install tor torsocks -y
sudo systemctl start tor@default
sudo systemctl enable tor@default
curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip
# Expected: {"IsTor":true,"IP":"..."}
```

### 2. Clone and Set Up

```bash
git clone https://github.com/cahallchristopher/cahall-Cybersecurity-Portfolio.git
cd cahall-Cybersecurity-Portfolio/projects/osint-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure API Keys (Optional)

```bash
cp .env.example .env
nano .env
```

### 4. Run

```bash
./start.sh
# Open http://localhost:8000
```

---

## API Keys

| Service | Required? | Cost | Get it at |
|---|---|---|---|
| HaveIBeenPwned | Optional | $3.50/mo | haveibeenpwned.com/API/Key |
| NumVerify | Optional | Free (250/mo) | numverify.com |
| Sherlock | No key needed | Free | pip install sherlock-project |
| Maigret | No key needed | Free | pip install maigret |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/lookup` | Run a lookup |
| `GET` | `/api/history` | Fetch past results |
| `GET` | `/api/stats` | Source breakdown for chart |
| `GET` | `/api/tor-status` | Live Tor health check |
| `DELETE` | `/api/history/{id}` | Delete a result |
| `GET` | `/docs` | Swagger API docs |

---

## Project Structure

```
osint-tool/
├── main.py              # FastAPI app + OSINT logic + HTML frontend
├── requirements.txt     # Pinned Python dependencies
├── start.sh             # Launch script with Tor check
├── .env.example         # API key template
├── .gitignore           # Excludes venv/, osint.db, .env, reports/
├── docs/
│   ├── BUILD_JOURNAL.md     # How this was built step by step
│   ├── TROUBLESHOOTING.md   # Every error encountered and fixed
│   └── ARCHITECTURE.md      # Design decisions and data flow
├── screenshots/
│   └── osint_lookup.png     # Dashboard screenshot
├── configs/
│   └── osint-tool.service   # systemd unit for auto-start on boot
└── scripts/
    └── setup.sh             # One-command fresh install script
```

---

## How It Was Built

1. **FastAPI scaffold** — routes, SQLite schema, stub OSINT logic, dark UI
2. **Sherlock integration** — subprocess + regex parsing of `[+] Platform: URL` output
3. **Maigret integration** — subprocess + text report parsing for countries, interests, alternate IDs
4. **Parallel execution** — ThreadPoolExecutor cuts runtime from ~210s to ~120s
5. **Tor integration** — check_tor() verifies exit IP, --tor-proxy flag passed to Maigret
6. **HIBP + NumVerify** — keyed API integrations for email and phone
7. **UI polish** — live Tor badge, per-lookup toggle, risk scoring, Chart.js

Full build notes: [docs/BUILD_JOURNAL.md](docs/BUILD_JOURNAL.md)

---

## Security Notes

- All results stay in local SQLite — nothing sent to cloud
- Maigret traffic anonymized via Tor — real IP not exposed to targets
- Sherlock runs direct — your IP is visible to checked platforms
- `.env` excluded from git — never commit API keys
- No authentication by default — restrict to loopback if on shared machine

---

## Built As Part Of

[cahall-Cybersecurity-Portfolio](https://github.com/cahallchristopher/cahall-Cybersecurity-Portfolio) — Red Team Tools

---

## License

MIT — use freely for authorized security research and penetration testing.

> **Do not use this tool to investigate individuals without legal authorization.**
