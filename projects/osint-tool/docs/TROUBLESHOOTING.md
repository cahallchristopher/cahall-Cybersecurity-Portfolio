# Troubleshooting Guide

> Every error encountered during development with full terminal output, root cause, and fix.

---

## Issue 1 — `maigret: error: unrecognized arguments: --print-found`

### Symptom
```bash
maigret testuser123 --print-found
# maigret: error: unrecognized arguments: --print-found
```

### Root Cause
`--print-found` is a Sherlock-specific flag. Maigret uses the opposite convention — it shows found accounts by default and uses `--print-not-found` to show misses.

### Fix
```bash
# Wrong (Sherlock syntax):
maigret username --print-found

# Correct (Maigret syntax):
maigret username --top-sites 100 --no-color --no-progressbar
```

### Lesson
Always check `--help` output when switching between similar tools. CLI conventions are not consistent across the OSINT ecosystem.

---

## Issue 2 — `tor.service` Shows `active (exited)`

### Symptom
```bash
sudo systemctl start tor
sudo systemctl status tor

● tor.service - Anonymizing overlay network for TCP (multi-instance-master)
     Active: active (exited) since Wed 2026-07-22 15:02:46 CDT
    Process: ExecStart=/bin/true (code=exited, status=0/SUCCESS)
```

Port 9050 is not listening despite the service appearing "active".

### Root Cause
`tor.service` is a systemd multi-instance master unit. Its `ExecStart` is literally `/bin/true` — it runs, exits immediately with success, and does nothing. The actual Tor daemon runs as the template instance `tor@default.service`.

### Diagnosis
```bash
systemctl cat tor.service
# ExecStart=/bin/true  ← confirms this is a no-op launcher
```

### Fix
```bash
sudo systemctl start tor@default
sudo systemctl enable tor@default
sudo systemctl status tor@default
# Active: active (running)
# Bootstrapped 100% (done)
```

### Verification
```bash
curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip
# {"IsTor":true,"IP":"45.84.107.76"}
```

### Lesson
On systemd systems with template units (`service@instance`), the master unit is often a no-op launcher. Always verify the actual process is running with `ps aux | grep tor` and test the port directly.

---

## Issue 3 — `[Errno 98] Address already in use`

### Symptom
```
ERROR:    [Errno 98] Address already in use
```

Occurs when restarting uvicorn after a crash, `pkill`, or code update.

### Root Cause
The uvicorn process was killed but the kernel had not yet released the TCP socket binding. The OS holds the socket in a `TIME_WAIT` state briefly after process exit.

### Fix
```bash
# Find and kill whatever is holding port 8000
sudo fuser -k 8000/tcp
sleep 2
./start.sh
```

### Alternative
```bash
lsof -ti:8000 | xargs kill -9
```

### Lesson
`sudo fuser -k <port>/tcp` is more reliable than `pkill` for freeing ports because it targets the socket binding directly rather than the process name.

---

## Issue 4 — `bash: filename: cannot overwrite existing file`

### Symptom
```bash
cat > start.sh << 'EOF'
...
EOF
# bash: start.sh: cannot overwrite existing file
```

Also seen with `requirements.txt`, `.gitignore`, and other files.

### Root Cause
The shell `noclobber` option (`set -C`) is enabled, preventing `>` redirection from overwriting existing files. This is a common safety setting in `.bashrc`.

### Fix
Use `tee` which bypasses noclobber:
```bash
tee start.sh << 'EOF'
#!/bin/bash
...
EOF
```

For pip output:
```bash
pip freeze | tee requirements.txt
```

### Lesson
When redirection fails silently or with noclobber errors, `tee` is the reliable alternative. It writes to the file AND stdout simultaneously.

---

## Issue 5 — Maigret Bot Protection Errors

### Symptom
```
[!] Too many errors of type "Bot protection" (5.17%).
    Try to switch to another ip address
[!] Too many errors of type "Access denied" (5.17%).
    It's recommended to use --cloudflare-bypass or a proxy
```

### Root Cause
Platforms like Twitter/X and Cloudflare-protected sites detect automated scraping and block requests from data center IP ranges. Running from a residential or VPS IP without anonymization triggers these blocks.

### Fix
Route Maigret through Tor:

```python
# In run_maigret():
if use_tor and tor_status["running"]:
    cmd += ["--tor-proxy", TOR_PROXY]
```

```bash
# Command becomes:
maigret username --tor-proxy socks5://127.0.0.1:9050 --top-sites 100
```

Make sure Tor is running first:
```bash
sudo systemctl start tor@default
curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip
# {"IsTor":true}
```

### Lesson
Some platforms aggressively block scraping from known IP ranges. Tor exit nodes rotate IPs and bypass many of these restrictions. The `--tor-proxy` flag in Maigret routes all outbound HTTP through the SOCKS5 proxy.

---

## Issue 6 — Old UI Loading After Code Update

### Symptom
Updated `main.py` with new features (Tor toggle, Maigret badges) but the browser still shows the old version.

### Root Cause
The uvicorn process was a stale instance started days earlier. Even though `--reload` was enabled and the file changed, the process itself was the old one and the reload watcher had stopped.

### Fix
```bash
# Kill the stale process
sudo fuser -k 8000/tcp
sleep 2

# Start fresh
./start.sh

# Hard refresh in browser
# Ctrl + Shift + R
```

### Lesson
When a running service doesn't reflect file changes despite `--reload`, assume the process is stale. Kill it explicitly and restart rather than waiting for the reload watcher.

---

## Issue 7 — JSON Encoding Error with Inline File Content in curl

### Symptom
```bash
curl -X POST http://localhost:8080/v1/artifacts/ingest \
  -H "Content-Type: application/json" \
  -d '{"input": {"type": "text", "value": "'"$(cat file.txt)"'"}}'

# Response:
# {"msg": "JSON decode error", "ctx": {"error": "Invalid control character at"}}
```

### Root Cause
Shell command substitution `$(cat file.txt)` inlines the file content including literal newline characters (`\n`) directly into the JSON string. JSON strings cannot contain unescaped literal newlines — they must be encoded as `\n`.

### Fix
Use Python `requests` which handles JSON serialization correctly:

```python
import requests

with open('file.txt', 'r') as f:
    content = f.read()

payload = {"input": {"type": "text", "value": content}}
r = requests.post(url, json=payload)  # json= parameter handles escaping
```

### Lesson
Never interpolate multi-line file content into JSON via shell string substitution. Use a proper HTTP client library that handles encoding.

---

## Issue 8 — `ValueError: Default model 'mxbai-embed-large' not found`

### Symptom
```
ValueError: Default model 'mxbai-embed-large' not found in registered models
Application startup failed. Exiting.
```

*(PrivateGPT context — documented here for completeness)*

### Root Cause
Ollama registers models with their full tag. The model name `mxbai-embed-large` (without tag) does not match the registered name `mxbai-embed-large:latest`.

### Diagnosis
```bash
ollama list | grep mxbai
# mxbai-embed-large:latest    468836162de7    669 MB
```

### Fix
```bash
export PGPT_EMBEDDING_DEFAULT=mxbai-embed-large:latest
```

### Lesson
Always use the full model name including tag when configuring Ollama-backed services. Run `ollama list` to get the exact registered name.
