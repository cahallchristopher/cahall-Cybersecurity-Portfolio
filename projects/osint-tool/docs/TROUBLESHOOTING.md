# Troubleshooting Guide

> Every error encountered during development with root cause and fix.

---

## Error 1 -- maigret: unrecognized arguments: --print-found

**Command run:** maigret testuser123 --print-found

**Root cause:** --print-found is a Sherlock flag. Maigret shows found accounts
by default and uses --print-not-found to show misses (opposite convention).

**Fix:**
```bash
# Wrong (Sherlock syntax):
maigret username --print-found

# Correct (Maigret syntax):
maigret username --top-sites 100 --no-color --no-progressbar
```

---

## Error 2 -- tor.service Shows active (exited)

**Symptom:**
```
Active: active (exited)
Process: ExecStart=/bin/true
```

**Root cause:** tor.service is a multi-instance master unit. Its ExecStart
is /bin/true -- it does nothing. The actual Tor daemon is tor@default.service.

**Fix:**
```bash
sudo systemctl start tor@default
sudo systemctl enable tor@default
```

**Verification:**
```bash
curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip
# {"IsTor":true,"IP":"45.84.107.76"}
```

---

## Error 3 -- [Errno 98] Address already in use

**Root cause:** uvicorn process still holding the socket after pkill.

**Fix:**
```bash
sudo fuser -k 8000/tcp
sleep 2
./start.sh
```

---

## Error 4 -- cannot overwrite existing file

**Root cause:** Shell noclobber option prevents > redirection from overwriting files.

**Fix:** Use tee which bypasses noclobber:
```bash
tee start.sh << EOF
...
EOF
```

---

## Error 5 -- Maigret Bot Protection Errors

**Symptom:**
```
[!] Too many errors of type "Bot protection" (5.17%)
```

**Root cause:** Platforms detect automated scraping and block requests.

**Fix:** Route Maigret through Tor:
```bash
maigret username --tor-proxy socks5://127.0.0.1:9050 --top-sites 100
```

---

## Error 6 -- Old UI After Code Update

**Root cause:** Stale uvicorn process started days earlier.

**Fix:**
```bash
sudo fuser -k 8000/tcp
sleep 2
./start.sh
# Then Ctrl+Shift+R in browser
```

---

## Error 7 -- JSON Encoding Error with curl

**Root cause:** Shell command substitution inlines literal newlines into JSON strings.

**Fix:** Use Python requests:
```python
with open("file.txt", "r") as f:
    content = f.read()
payload = {"input": {"type": "text", "value": content}}
requests.post(url, json=payload)
```
