"""
OSINT People & Identity Lookup Tool
Integrations:
  - Sherlock  : username hunting across 400+ platforms (no API key, direct)
  - Maigret   : username hunting with enriched data, routed through Tor
  - HIBP      : email breach check (requires HIBP_API_KEY in .env)
  - NumVerify : phone number lookup (requires NUMVERIFY_API_KEY in .env)

Run with:
    source venv/bin/activate
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Requirements:
    sudo systemctl start tor@default
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
import os
import subprocess
import re
import requests as http_requests
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Load .env file ────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

HIBP_API_KEY      = os.getenv("HIBP_API_KEY", "")
NUMVERIFY_API_KEY = os.getenv("NUMVERIFY_API_KEY", "")

# Tor SOCKS5 proxy — Maigret routes all requests through this
TOR_PROXY         = os.getenv("TOR_PROXY", "socks5://127.0.0.1:9050")

# ── Constants ─────────────────────────────────────────────────────────────────
DB_PATH   = os.path.join(os.path.dirname(__file__), "osint.db")
APP_TITLE = "OSINT People & Identity Lookup"

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    """Return a SQLite connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    """Create the results table on first run."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS osint_results (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            query     TEXT NOT NULL,
            source    TEXT NOT NULL,
            result    TEXT,
            timestamp TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


create_database()


# ── Pydantic models ───────────────────────────────────────────────────────────
class LookupRequest(BaseModel):
    query:   str
    source:  str                   # "email" | "username" | "phone" | "name"
    notes:   Optional[str] = None
    use_tor: bool = True           # route Maigret through Tor by default


# ── Tor health check ──────────────────────────────────────────────────────────
def check_tor() -> dict:
    """
    Verify Tor is reachable and returning an anonymous IP.
    Uses the Tor Project's own check API via the SOCKS5 proxy.
    """
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
        return {"running": False, "ip": None, "proxy": TOR_PROXY, "error": str(e)}


# ── Sherlock integration ──────────────────────────────────────────────────────
def run_sherlock(username: str) -> list:
    """
    Run Sherlock directly (no proxy) — fast enough without Tor.
    Parses '[+] Platform: URL' lines from stdout.
    Returns list of {tool, type, platform, url} dicts.
    """
    findings = []
    try:
        proc = subprocess.run(
            ["sherlock", username, "--print-found", "--timeout", "10"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        for line in proc.stdout.splitlines():
            match = re.match(r"\[\+\]\s+(.+?):\s+(https?://\S+)", line)
            if match:
                findings.append({
                    "tool":     "sherlock",
                    "type":     "username_found",
                    "platform": match.group(1).strip(),
                    "url":      match.group(2).strip(),
                })
    except subprocess.TimeoutExpired:
        findings.append({
            "tool": "sherlock", "type": "error",
            "status": "Timed out after 120s",
        })
    except FileNotFoundError:
        findings.append({
            "tool": "sherlock", "type": "error",
            "status": "Not installed — pip install sherlock-project",
        })
    except Exception as e:
        findings.append({"tool": "sherlock", "type": "error", "status": str(e)})

    return findings


# ── Maigret integration (with Tor) ────────────────────────────────────────────
def run_maigret(username: str, use_tor: bool = True) -> dict:
    """
    Run Maigret with optional Tor proxy routing.
    --tor-proxy routes ALL Maigret HTTP requests through Tor SOCKS5,
    bypassing Cloudflare and bot protection.
    --top-sites 100 balances speed vs coverage.
    --no-color / --no-progressbar for clean parseable output.
    """
    findings = []
    meta     = {}

    # Build base Maigret command
    cmd = [
        "maigret", username,
        "--top-sites", "100",
        "--no-color",
        "--no-progressbar",
        "--timeout", "15",
    ]

    # Add Tor proxy if enabled and Tor is reachable
    if use_tor:
        tor_status = check_tor()
        if tor_status["running"]:
            cmd += ["--tor-proxy", TOR_PROXY]
            meta["tor_ip"]      = tor_status["ip"]
            meta["tor_enabled"] = True
            findings.append({
                "tool":   "maigret",
                "type":   "tor_status",
                "status": f"Routing through Tor — exit IP: {tor_status['ip']}",
            })
        else:
            # Tor not reachable — fall back to direct with warning
            meta["tor_enabled"] = False
            findings.append({
                "tool":   "maigret",
                "type":   "tor_status",
                "status": f"Tor not reachable ({tor_status.get('error', 'unknown')}) — running direct",
            })
    else:
        meta["tor_enabled"] = False
        findings.append({
            "tool":   "maigret",
            "type":   "tor_status",
            "status": "Tor disabled for this lookup",
        })

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=240,  # longer timeout when routing through Tor
        )
        output = proc.stdout + proc.stderr

        # Parse: "Search by username X returned N accounts"
        count_match = re.search(
            r"Search by username \S+ returned (\d+) accounts", output
        )
        if count_match:
            meta["maigret_accounts"] = int(count_match.group(1))

        # Parse: "Countries: us, ru, de"
        country_match = re.search(r"Countries:\s+(.+)", output)
        if country_match:
            meta["countries"] = [c.strip() for c in country_match.group(1).split(",")]
            findings.append({
                "tool":   "maigret",
                "type":   "geo_data",
                "status": f"Countries: {', '.join(meta['countries']).upper()}",
            })

        # Parse: "Interests (tags): social, gaming, coding..."
        interest_match = re.search(r"Interests \(tags\):\s+(.+)", output)
        if interest_match:
            meta["interests"] = [i.strip() for i in interest_match.group(1).split(",")]
            findings.append({
                "tool":   "maigret",
                "type":   "interests",
                "status": ", ".join(meta["interests"]),
            })

        # Parse: "Extracted IDs: {'altuser': 'username'}"
        id_match = re.search(r"Extracted IDs:\s+(\{.+?\})", output)
        if id_match:
            try:
                extracted = json.loads(id_match.group(1).replace("'", '"'))
                alt_ids   = [uid for uid in extracted if uid != username]
                if alt_ids:
                    meta["alternate_ids"] = alt_ids
                    for uid in alt_ids:
                        findings.append({
                            "tool":   "maigret",
                            "type":   "extracted_id",
                            "status": f"Alternate ID discovered: {uid} ({extracted[uid]})",
                        })
            except Exception:
                pass

        # Parse bot protection warnings
        if "Bot protection" in output or "Access denied" in output:
            bp_match = re.search(
                r'Too many errors of type "Bot protection" \((.+?)\%\)', output
            )
            if bp_match:
                pct = bp_match.group(1)
                if use_tor and meta.get("tor_enabled"):
                    findings.append({
                        "tool":   "maigret",
                        "type":   "warning",
                        "status": f"Bot protection on {pct}% of sites (Tor helped reduce this)",
                    })
                else:
                    findings.append({
                        "tool":   "maigret",
                        "type":   "warning",
                        "status": f"Bot protection on {pct}% of sites — enable Tor to bypass",
                    })

        # Insert summary finding after tor_status
        if "maigret_accounts" in meta:
            findings.insert(1, {
                "tool":   "maigret",
                "type":   "summary",
                "status": f"Found {meta['maigret_accounts']} accounts across checked platforms",
            })

    except subprocess.TimeoutExpired:
        findings.append({
            "tool": "maigret", "type": "error",
            "status": "Timed out after 240s",
        })
    except FileNotFoundError:
        findings.append({
            "tool": "maigret", "type": "error",
            "status": "Not installed — pip install maigret",
        })
    except Exception as e:
        findings.append({"tool": "maigret", "type": "error", "status": str(e)})

    return {"findings": findings, "meta": meta}


# ── Combined username lookup ──────────────────────────────────────────────────
def lookup_username(username: str, use_tor: bool = True) -> dict:
    """
    Run Sherlock (direct) and Maigret (via Tor) in parallel.
    Merge results and compute combined risk score.
    """
    sherlock_findings = []
    maigret_result    = {"findings": [], "meta": {}}

    # Run both tools concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_sherlock, username):           "sherlock",
            executor.submit(run_maigret,  username, use_tor): "maigret",
        }
        for future in as_completed(futures):
            tool = futures[future]
            try:
                result = future.result()
                if tool == "sherlock":
                    sherlock_findings = result
                else:
                    maigret_result = result
            except Exception:
                pass

    # Merge order: Maigret meta → Sherlock hits → Maigret tail
    maigret_meta = [
        f for f in maigret_result["findings"]
        if f.get("type") in ("tor_status", "summary", "geo_data")
    ]
    maigret_tail = [
        f for f in maigret_result["findings"]
        if f.get("type") not in ("tor_status", "summary", "geo_data")
    ]
    all_findings = maigret_meta + sherlock_findings + maigret_tail

    # Risk score — use max() to avoid double-counting platforms found by both tools
    sherlock_hits = len([f for f in sherlock_findings if f.get("type") == "username_found"])
    maigret_hits  = maigret_result["meta"].get("maigret_accounts", 0)
    total_hits    = max(sherlock_hits, maigret_hits)
    risk_score    = min(100, total_hits * 3)

    meta      = maigret_result["meta"]
    countries = meta.get("countries", [])
    alt_ids   = meta.get("alternate_ids", [])
    tor_ip    = meta.get("tor_ip", None)

    summary_parts = [f"{total_hits} platforms found"]
    if countries:
        summary_parts.append(f"geo: {', '.join(countries).upper()}")
    if alt_ids:
        summary_parts.append(f"alt IDs: {', '.join(alt_ids)}")
    if tor_ip:
        summary_parts.append(f"via Tor {tor_ip}")

    return {
        "query":      username,
        "source":     "username",
        "findings":   all_findings,
        "risk_score": risk_score,
        "summary":    " · ".join(summary_parts),
        "meta": {
            "sherlock_hits":  sherlock_hits,
            "maigret_hits":   maigret_hits,
            "countries":      countries,
            "interests":      meta.get("interests", []),
            "alternate_ids":  alt_ids,
            "tor_enabled":    meta.get("tor_enabled", False),
            "tor_ip":         tor_ip,
        },
    }


# ── HIBP email lookup ─────────────────────────────────────────────────────────
def lookup_email_hibp(email: str) -> dict:
    """Check email against HaveIBeenPwned breach database."""
    findings = []
    is_valid = bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
    findings.append({
        "type":   "email_format",
        "status": "valid" if is_valid else "invalid format",
    })

    if not is_valid:
        return {
            "query": email, "source": "email",
            "findings": findings, "risk_score": 0,
            "summary": "Invalid email format",
        }

    if not HIBP_API_KEY:
        findings.append({
            "type":   "breach_check",
            "status": "Add HIBP_API_KEY to .env to enable breach checking",
        })
        return {
            "query": email, "source": "email",
            "findings": findings, "risk_score": 10,
            "summary": "No API key — format check only",
        }

    try:
        resp = http_requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers={
                "hibp-api-key": HIBP_API_KEY,
                "user-agent":   "OSINT-Tool/1.0",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            breaches = resp.json()
            for b in breaches:
                findings.append({
                    "type":         "breach",
                    "name":         b.get("Name", "Unknown"),
                    "date":         b.get("BreachDate", "Unknown"),
                    "pwn_count":    b.get("PwnCount", 0),
                    "data_classes": b.get("DataClasses", []),
                })
            risk    = min(100, 20 + len(breaches) * 15)
            summary = f"Found in {len(breaches)} breach(es)"
        elif resp.status_code == 404:
            findings.append({"type": "breach_check", "status": "No breaches found ✓"})
            risk    = 5
            summary = "Clean — no breaches found"
        elif resp.status_code == 401:
            findings.append({"type": "error", "status": "Invalid HIBP API key"})
            risk    = 0
            summary = "Auth error"
        elif resp.status_code == 429:
            findings.append({"type": "error", "status": "Rate limited — wait 1 minute"})
            risk    = 0
            summary = "Rate limited"
        else:
            findings.append({"type": "error", "status": f"HTTP {resp.status_code}"})
            risk    = 0
            summary = f"HTTP error {resp.status_code}"
    except http_requests.RequestException as e:
        findings.append({"type": "error", "status": f"Network error: {e}"})
        risk    = 0
        summary = "Network error"

    return {
        "query": email, "source": "email",
        "findings": findings, "risk_score": risk, "summary": summary,
    }


# ── NumVerify phone lookup ────────────────────────────────────────────────────
def lookup_phone_numverify(phone: str) -> dict:
    """Validate and enrich a phone number via NumVerify API."""
    findings = []
    clean    = re.sub(r"[\s\-\(\)\.]", "", phone)
    findings.append({"type": "phone_input", "value": clean})

    if not NUMVERIFY_API_KEY:
        findings.append({
            "type":   "carrier_lookup",
            "status": "Add NUMVERIFY_API_KEY to .env to enable",
        })
        return {
            "query": phone, "source": "phone",
            "findings": findings, "risk_score": 10,
            "summary": "No API key configured",
        }

    try:
        resp = http_requests.get(
            "http://apilayer.net/api/validate",
            params={"access_key": NUMVERIFY_API_KEY, "number": clean, "format": 1},
            timeout=10,
        )
        data = resp.json()
        if data.get("valid"):
            findings += [
                {"type": "valid",       "status": "valid number"},
                {"type": "country",     "value": data.get("country_name", "Unknown")},
                {"type": "carrier",     "value": data.get("carrier", "Unknown")},
                {"type": "line_type",   "value": data.get("line_type", "Unknown")},
                {"type": "location",    "value": data.get("location", "Unknown")},
                {"type": "intl_format", "value": data.get("international_format", clean)},
            ]
            risk    = 60 if data.get("line_type") == "mobile" else 35
            summary = (
                f"{data.get('country_name')} · "
                f"{data.get('carrier')} · "
                f"{data.get('line_type')}"
            )
        else:
            findings.append({"type": "valid", "status": "invalid or unrecognised number"})
            risk    = 5
            summary = "Invalid number"
    except http_requests.RequestException as e:
        findings.append({"type": "error", "status": f"Network error: {e}"})
        risk    = 0
        summary = "Network error"

    return {
        "query": phone, "source": "phone",
        "findings": findings, "risk_score": risk, "summary": summary,
    }


# ── Name lookup ───────────────────────────────────────────────────────────────
def lookup_name(name: str) -> dict:
    """Generate manual investigation search links for a full name."""
    q = name.replace(" ", "+")
    findings = [
        {"type": "search_google",   "url": f"https://www.google.com/search?q=%22{q}%22"},
        {"type": "search_linkedin", "url": f"https://www.linkedin.com/search/results/people/?keywords={q}"},
        {"type": "search_pipl",     "url": f"https://pipl.com/search/?q={q}"},
        {"type": "search_peekyou",  "url": f"https://www.peekyou.com/{name.replace(' ', '_').lower()}"},
        {"type": "note", "status":  "Integrate Spokeo/PeekYou API for automated enrichment"},
    ]
    return {
        "query": name, "source": "name",
        "findings": findings, "risk_score": 15,
        "summary": f"Manual search links for '{name}'",
    }


# ── Router ────────────────────────────────────────────────────────────────────
def perform_lookup(query: str, source: str, use_tor: bool = True) -> dict:
    """Route lookup request to the correct integration."""
    if source == "username":
        return lookup_username(query, use_tor)
    elif source == "email":
        return lookup_email_hibp(query)
    elif source == "phone":
        return lookup_phone_numverify(query)
    elif source == "name":
        return lookup_name(query)
    else:
        return {
            "query": query, "source": source,
            "findings": [{"type": "error", "status": f"Unknown source: {source}"}],
            "risk_score": 0, "summary": "Unknown source",
        }


# ── API routes ────────────────────────────────────────────────────────────────
@app.post("/api/lookup")
def lookup(req: LookupRequest):
    """Run an OSINT lookup and persist the result."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result_data = perform_lookup(req.query.strip(), req.source.strip(), req.use_tor)

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO osint_results (query, source, result) VALUES (?, ?, ?)",
            (req.query, req.source, json.dumps(result_data)),
        )
        conn.commit()
        record_id = cursor.lastrowid
    finally:
        conn.close()

    return {
        "id":        record_id,
        "query":     req.query,
        "source":    req.source,
        "result":    result_data,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/tor-status")
def tor_status():
    """Check if Tor is running and return current exit IP."""
    return check_tor()


@app.get("/api/history")
def get_history(limit: int = 50):
    """Return the last N lookup results."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM osint_results ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
    finally:
        conn.close()
    return [
        {
            "id":        r["id"],
            "query":     r["query"],
            "source":    r["source"],
            "result":    json.loads(r["result"]) if r["result"] else {},
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]


@app.get("/api/stats")
def get_stats():
    """Return source breakdown counts for chart."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT source, COUNT(*) as count FROM osint_results GROUP BY source"
        )
        rows = cursor.fetchall()
    finally:
        conn.close()
    return {r["source"]: r["count"] for r in rows}


@app.delete("/api/history/{record_id}")
def delete_record(record_id: int):
    """Delete a specific lookup record."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM osint_results WHERE id = ?", (record_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")
    finally:
        conn.close()
    return {"deleted": record_id}


# ── Frontend ──────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OSINT Lookup</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root{--bg:#0d1117;--surface:#161b22;--border:#30363d;--accent:#58a6ff;
    --danger:#f85149;--success:#3fb950;--warn:#e3b341;--purple:#a371f7;
    --text:#e6edf3;--muted:#7d8590;--font:'Courier New',monospace;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;}
  header{border-bottom:1px solid var(--border);padding:1rem 2rem;display:flex;align-items:center;gap:1rem;}
  header h1{font-size:1.1rem;color:var(--accent);letter-spacing:.1em;}
  .badge{font-size:.6rem;padding:2px 6px;border-radius:3px;font-weight:bold;}
  .badge.red{background:var(--danger);color:#fff;}
  .badge.green{background:#1a3a2a;color:var(--success);}
  .badge.purple{background:#2a1a3a;color:var(--purple);}
  .badge.gray{background:#1f2937;color:var(--muted);}
  main{display:grid;grid-template-columns:420px 1fr;gap:1.5rem;padding:1.5rem 2rem;max-width:1400px;}
  .panel{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:1.25rem;}
  .panel h2{font-size:.75rem;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-bottom:1rem;}
  label{display:block;font-size:.75rem;color:var(--muted);margin-bottom:.3rem;margin-top:.75rem;}
  input,select{width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);
    padding:.5rem .75rem;border-radius:4px;font-family:var(--font);font-size:.85rem;}
  input:focus,select:focus{outline:none;border-color:var(--accent);}
  .toggle-row{display:flex;align-items:center;gap:.75rem;margin-top:.75rem;}
  .toggle-row label{margin:0;font-size:.8rem;color:var(--text);}
  input[type=checkbox]{width:auto;accent-color:var(--purple);}
  button{width:100%;margin-top:1rem;padding:.6rem;background:var(--accent);color:#0d1117;
    border:none;border-radius:4px;font-family:var(--font);font-weight:bold;font-size:.85rem;
    cursor:pointer;letter-spacing:.05em;}
  button:hover{opacity:.85;}
  .del-btn{background:none;border:none;color:var(--danger);cursor:pointer;width:auto;margin:0;padding:2px 6px;}
  .result-box{background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:1rem;
    min-height:220px;font-size:.78rem;white-space:pre-wrap;overflow-y:auto;max-height:440px;color:var(--success);}
  .risk{display:inline-block;padding:2px 8px;border-radius:3px;font-size:.7rem;font-weight:bold;}
  .risk.low{background:#1a3a2a;color:var(--success);}
  .risk.medium{background:#3a2a1a;color:var(--warn);}
  .risk.high{background:#3a1a1a;color:var(--danger);}
  .history-item{border-bottom:1px solid var(--border);padding:.6rem 0;
    display:flex;justify-content:space-between;align-items:center;font-size:.78rem;}
  .history-item:last-child{border-bottom:none;}
  .history-meta{color:var(--muted);font-size:.7rem;}
  canvas{max-height:180px;margin-top:1rem;}
  .right-col{display:flex;flex-direction:column;gap:1.5rem;}
  .spinner{display:none;color:var(--warn);padding:.5rem 0;font-size:.8rem;}
  .tag{display:inline-block;padding:1px 5px;border-radius:2px;font-size:.65rem;
    background:#1f2937;color:var(--muted);margin-right:.3rem;}
  .tor-indicator{font-size:.7rem;padding:3px 8px;border-radius:3px;margin-left:.5rem;}
  .tor-on{background:#2a1a3a;color:var(--purple);}
  .tor-off{background:#1f2937;color:var(--muted);}
  #tor-status-bar{font-size:.75rem;margin-top:.75rem;padding:.4rem .6rem;
    border-radius:4px;border:1px solid var(--border);color:var(--muted);}
</style>
</head>
<body>
<header>
  <h1>⬡ OSINT LOOKUP</h1>
  <span class="badge red">RED TEAM</span>
  <span class="badge green">Sherlock</span>
  <span class="badge purple">Maigret</span>
  <span id="tor-badge" class="badge gray">Tor ...</span>
</header>
<main>
  <div class="panel">
    <h2>New Lookup</h2>
    <label>Source Type</label>
    <select id="source">
      <option value="username">Username / Handle (Sherlock + Maigret)</option>
      <option value="email">Email Address (HIBP)</option>
      <option value="phone">Phone Number (NumVerify)</option>
      <option value="name">Full Name</option>
    </select>
    <label>Query</label>
    <input type="text" id="query" placeholder="Enter username, email, phone or name..." />
    <label>Notes (optional)</label>
    <input type="text" id="notes" placeholder="Case reference, target, etc." />
    <div class="toggle-row">
      <input type="checkbox" id="use-tor" checked />
      <label for="use-tor">Route Maigret through Tor
        <span class="tor-indicator tor-on">🧅 anonymous</span>
      </label>
    </div>
    <div id="tor-status-bar">Checking Tor status...</div>
    <button onclick="runLookup()">▶ RUN LOOKUP</button>
    <div class="spinner" id="spinner">
      ⏳ Sherlock + Maigret running in parallel... (90–120s via Tor)
    </div>
    <h2 style="margin-top:1.5rem;">Result</h2>
    <div class="result-box" id="result">// output will appear here</div>
  </div>
  <div class="right-col">
    <div class="panel">
      <h2>Lookup History</h2>
      <div id="history">Loading...</div>
    </div>
    <div class="panel">
      <h2>Source Breakdown</h2>
      <canvas id="chart"></canvas>
    </div>
  </div>
</main>

<script>
let chartInstance = null;

// ── Check Tor status on load ──────────────────────────────────────────────
async function checkTorStatus() {
  try {
    const resp  = await fetch('/api/tor-status');
    const data  = await resp.json();
    const bar   = document.getElementById('tor-status-bar');
    const badge = document.getElementById('tor-badge');
    if (data.running) {
      bar.innerHTML     = `🧅 Tor active — exit IP: <strong style="color:#a371f7">${data.ip}</strong> · proxy: ${data.proxy}`;
      badge.textContent = 'Tor ✓';
      badge.className   = 'badge purple';
    } else {
      bar.innerHTML     = `⚠ Tor not reachable — ${data.error || 'check systemctl status tor@default'}`;
      badge.textContent = 'Tor ✗';
      badge.className   = 'badge gray';
      document.getElementById('use-tor').checked = false;
    }
  } catch (e) {
    document.getElementById('tor-status-bar').textContent = '⚠ Could not check Tor status';
  }
}

// ── Run lookup ────────────────────────────────────────────────────────────
async function runLookup() {
  const query  = document.getElementById('query').value.trim();
  const source = document.getElementById('source').value;
  const notes  = document.getElementById('notes').value.trim();
  const useTor = document.getElementById('use-tor').checked;
  if (!query) { alert('Please enter a query.'); return; }

  const torMsg = useTor ? 'via Tor' : 'direct (Tor disabled)';
  document.getElementById('spinner').style.display = 'block';
  document.getElementById('result').textContent =
    `// running lookup ${torMsg}\n// Sherlock + Maigret running in parallel...`;

  try {
    const resp = await fetch('/api/lookup', {
      method:  'POST',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify({query, source, notes, use_tor: useTor}),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'Lookup failed');
    renderResult(data);
    await loadHistory();
    await loadChart();
  } catch (err) {
    document.getElementById('result').textContent = 'ERROR: ' + err.message;
  } finally {
    document.getElementById('spinner').style.display = 'none';
  }
}

// ── Render result ─────────────────────────────────────────────────────────
function renderResult(data) {
  const r   = data.result;
  const lvl = r.risk_score >= 60 ? 'HIGH' : r.risk_score >= 30 ? 'MEDIUM' : 'LOW';
  const m   = r.meta || {};

  let out = '';
  out += `QUERY:      ${data.query}\n`;
  out += `SOURCE:     ${data.source}\n`;
  out += `RISK SCORE: ${r.risk_score}/100 [${lvl}]\n`;
  out += `SUMMARY:    ${r.summary || ''}\n`;
  out += `TIMESTAMP:  ${data.timestamp}\n`;

  if (m.sherlock_hits !== undefined) {
    out += `\nTOOLS:\n`;
    out += `  Sherlock : ${m.sherlock_hits} platforms (direct)\n`;
    out += `  Maigret  : ${m.maigret_hits} platforms (${m.tor_enabled ? '🧅 via Tor ' + m.tor_ip : 'direct'})\n`;
    if (m.countries?.length)     out += `  Countries: ${m.countries.join(', ').toUpperCase()}\n`;
    if (m.interests?.length)     out += `  Interests: ${m.interests.join(', ')}\n`;
    if (m.alternate_ids?.length) out += `  Alt IDs  : ${m.alternate_ids.join(', ')}\n`;
  }

  out += `\n${'─'.repeat(58)}\n`;
  out += `FINDINGS (${r.findings.length}):\n\n`;

  r.findings.forEach(f => {
    const tool = f.tool ? `[${f.tool.toUpperCase().padEnd(8)}]` : '[        ]';
    if (f.type === 'username_found') {
      out += `  ${tool} [+] ${(f.platform || '').padEnd(22)} ${f.url}\n`;
    } else if (f.type === 'breach') {
      out += `  ${tool} [!] BREACH: ${f.name} (${f.date}) — ${(f.pwn_count || 0).toLocaleString()} pwned\n`;
      if (f.data_classes?.length) out += `           Data: ${f.data_classes.join(', ')}\n`;
    } else if (f.url) {
      out += `  ${tool} [>] ${(f.type || '').padEnd(22)} ${f.url}\n`;
    } else {
      const icon = f.type === 'tor_status' ? '🧅' : f.type === 'warning' ? '⚠' : '-';
      out += `  ${tool} [${icon}] ${(f.type || '').padEnd(22)} ${f.status || f.value || ''}\n`;
    }
  });

  document.getElementById('result').textContent = out;
}

// ── History ───────────────────────────────────────────────────────────────
async function loadHistory() {
  const resp = await fetch('/api/history?limit=20');
  const rows = await resp.json();
  const el   = document.getElementById('history');
  if (!rows.length) {
    el.innerHTML = '<div class="history-meta">No lookups yet.</div>';
    return;
  }
  el.innerHTML = rows.map(row => {
    const score = row.result?.risk_score ?? '?';
    const lvl   = score >= 60 ? 'high' : score >= 30 ? 'medium' : 'low';
    const m     = row.result?.meta || {};
    const hits  = m.sherlock_hits !== undefined
      ? `<span class="tag">S:${m.sherlock_hits}</span><span class="tag">M:${m.maigret_hits}</span>`
      : '';
    const tor = m.tor_enabled
      ? '<span class="tag" style="color:#a371f7">🧅</span>'
      : '';
    return `<div class="history-item">
      <div>
        <div>${row.query} <span class="risk ${lvl}">${score}</span> ${hits}${tor}</div>
        <div class="history-meta">${row.source} · ${row.timestamp}</div>
      </div>
      <button class="del-btn" onclick="deleteRecord(${row.id})">✕</button>
    </div>`;
  }).join('');
}

async function deleteRecord(id) {
  await fetch('/api/history/' + id, {method: 'DELETE'});
  await loadHistory();
  await loadChart();
}

// ── Chart ─────────────────────────────────────────────────────────────────
async function loadChart() {
  const resp   = await fetch('/api/stats');
  const stats  = await resp.json();
  const labels = Object.keys(stats);
  const values = Object.values(stats);
  const colors = ['#58a6ff', '#f85149', '#3fb950', '#e3b341', '#a371f7'];
  if (chartInstance) chartInstance.destroy();
  chartInstance = new Chart(document.getElementById('chart'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{data: values, backgroundColor: colors, borderWidth: 0}],
    },
    options: {
      plugins: {
        legend: {labels: {color: '#7d8590', font: {family: 'Courier New'}}},
      },
    },
  });
}

// ── Tor toggle label update ───────────────────────────────────────────────
document.getElementById('use-tor').addEventListener('change', function () {
  const span       = this.parentElement.querySelector('.tor-indicator');
  span.textContent = this.checked ? '🧅 anonymous' : '⚡ direct';
  span.className   = 'tor-indicator ' + (this.checked ? 'tor-on' : 'tor-off');
});

// ── Enter key submits lookup ──────────────────────────────────────────────
document.getElementById('query').addEventListener('keydown', e => {
  if (e.key === 'Enter') runLookup();
});

// ── Init ──────────────────────────────────────────────────────────────────
checkTorStatus();
loadHistory();
loadChart();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the single-page frontend."""
    return HTML


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
