# Build Journal

> How this tool was built from scratch -- every decision, failure, and fix documented.

---

## Session 1 -- Project Setup

**Objective:** Create a working FastAPI app with stub OSINT logic

```bash
mkdir ~/osint-tool && cd ~/osint-tool
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic requests python-multipart
```

Why venv? Sherlock and Maigret install CLI tools alongside Python packages.
A venv keeps them isolated from system Python and PrivateGPT.

First version included:
- FastAPI app with CORS middleware
- SQLite osint_results table (id, query, source, result, timestamp)
- Stub perform_lookup() returning placeholder findings
- Routes: POST /api/lookup, GET /api/history, GET /api/stats, DELETE /api/history/{id}
- Dark terminal-themed single-page HTML frontend with Chart.js

Confirmed working at http://localhost:8000.

---

## Session 2 -- Sherlock Integration

**Objective:** Replace stub username logic with real Sherlock output

```bash
pip install sherlock-project
sherlock testuser123 --print-found
# Result: 131 platforms found
```

Integrated via subprocess:

```python
proc = subprocess.run(
    ["sherlock", username, "--print-found", "--timeout", "10"],
    capture_output=True, text=True, timeout=120,
)
```

Parsed output lines matching `[+] Platform: URL` with regex:

```python
match = re.match(r"\[\+\]\s+(.+?):\s+(https?://\S+)", line)
```

Error handling added for: TimeoutExpired, FileNotFoundError, generic Exception.

---

## Session 3 -- Maigret Integration

**Objective:** Add Maigret for richer username intelligence

```bash
pip install maigret
maigret testuser123 --print-found   # WRONG -- Sherlock flag, not Maigret
```

First failure: --print-found does not exist in Maigret.
Maigret shows found accounts by default.

```bash
maigret testuser123 --top-sites 50  # Correct
```

Output included countries, interests, alternate IDs -- much richer than Sherlock.

Parsed Maigret text report with regex for:
- Account count: Search by username returning N accounts
- Countries, Interests, Extracted IDs

Bot protection errors observed:
```
[!] Too many errors of type "Bot protection" (5.17%)
```
This led directly to Tor integration in Session 5.

---

## Session 4 -- Parallel Execution

**Objective:** Run Sherlock and Maigret simultaneously

Without parallelism: ~210s total
With ThreadPoolExecutor: ~120s

```python
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {
        executor.submit(run_sherlock, username):           "sherlock",
        executor.submit(run_maigret,  username, use_tor): "maigret",
    }
```

Result merging order:
1. Maigret meta (tor_status, summary, geo) -- context first
2. Sherlock platform hits -- bulk of findings
3. Maigret tail (interests, alternate IDs) -- enrichment last

Risk scoring:
```python
total_hits = max(sherlock_hits, maigret_hits)  # max() avoids double-counting
risk_score = min(100, total_hits * 3)
```

---

## Session 5 -- Tor Integration

**Objective:** Route Maigret through Tor to bypass bot protection

```bash
sudo apt install tor torsocks -y
sudo systemctl start tor@default
sudo systemctl enable tor@default
```

Critical discovery: tor.service runs /bin/true and exits immediately.
The actual daemon is tor@default.service.

```bash
sudo systemctl status tor@default
# Active: active (running)
# Bootstrapped 100% (done)
```

Tor verified:
```bash
curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip
# {"IsTor":true,"IP":"45.84.107.76"}
```

check_tor() added -- verifies Tor before every Maigret run.
If Tor is down, Maigret falls back to direct with a UI warning.

Maigret Tor flag:
```python
cmd += ["--tor-proxy", TOR_PROXY]
# maigret username --tor-proxy socks5://127.0.0.1:9050 --top-sites 100
```

UI additions:
- Live Tor badge in header (purple check / gray x)
- Per-lookup Tor toggle checkbox
- Exit IP shown in results output
- Onion icon on history cards for Tor-routed lookups
- /api/tor-status endpoint polled on page load

---

## Session 6 -- HIBP and NumVerify

HaveIBeenPwned response codes:
- 200 -- breaches found
- 404 -- clean (no breaches)
- 401 -- invalid API key
- 429 -- rate limited (wait 1 minute)

Risk: min(100, 20 + breach_count * 15)

NumVerify note: Free tier uses HTTP not HTTPS.
API key is exposed in transit -- noted as future improvement.

---

## Session 7 -- Deployment Fixes

Port conflict on restart:
```
ERROR: [Errno 98] Address already in use
```
Fix: sudo fuser -k 8000/tcp

Cannot overwrite files:
```
bash: start.sh: cannot overwrite existing file
```
Fix: use tee instead of cat >

Old UI after code update:
Hard refresh with Ctrl+Shift+R after restarting uvicorn.
