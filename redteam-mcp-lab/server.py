#!/usr/bin/env python3
"""Red Team Practice MCP Server — compact edition."""

import asyncio, ipaddress, json, logging, os, re, shlex, sys
from datetime import datetime
from pathlib import Path
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
os.environ.setdefault("HOME", "/home/chris")
LOG = Path.home() / "mcp-redteam" / "logs"
LOG.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, handlers=[
    logging.FileHandler(LOG / "server.log"), logging.StreamHandler(sys.stderr)])
log = logging.getLogger("mcp-rt")

SUBNET  = ipaddress.ip_network("192.168.56.0/24")
OLLAMA  = os.getenv("OLLAMA_HOST", "192.168.56.101:11434")
TIMEOUT = 60
TOOLS   = {
    "nmap":"port scanner", "ping":"ICMP check", "nc":"netcat",
    "curl":"HTTP client", "gobuster":"dir brute-forcer",
    "nikto":"web vuln scanner", "hydra":"login brute-forcer",
    "sqlmap":"SQLi scanner", "whatweb":"web fingerprinter",
    "dig":"DNS query", "whois":"WHOIS lookup", "ffuf":"web fuzzer",
    "enum4linux":"SMB enum", "crackmapexec":"AD enum",
    "masscan":"fast port scanner", "arp-scan":"ARP discovery",
}

def _host_ok(h):
    if h == "127.0.0.1": return True
    try: return ipaddress.ip_address(h) in SUBNET
    except ValueError: return False

def _validate(cmd):
    BLOCKED = [";","&&","||","`","$(","!",">","<","|"]
    if any(b in cmd for b in BLOCKED): return False, "Shell metacharacter blocked."
    try:    parts = shlex.split(cmd)
    except: return False, "Cannot parse command."
    if not parts: return False, "Empty command."
    binary = Path(parts[0]).name
    if binary not in TOOLS:
        return False, f"'{binary}' not allowed. Permitted: {', '.join(sorted(TOOLS))}"
    for ip in re.findall(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', cmd):
        if not _host_ok(ip): return False, f"{ip} outside allowed subnet {SUBNET}."
    return True, ""

def _audit(action, detail, result):
    with (LOG / "audit.jsonl").open("a") as f:
        f.write(json.dumps({"ts": datetime.utcnow().isoformat()+"Z",
                            "action": action, "detail": detail, "result": result}) + "\n")

async def _run_shell(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        return (out + err).decode(errors="replace").strip() or "(no output)"
    except asyncio.TimeoutError:
        proc.kill(); return f"Timed out after {TIMEOUT}s."

def txt(s): return [TextContent(type="text", text=s)]

app = Server("redteam-mcp")

@app.list_tools()
async def list_tools():
    def t(name, desc, props=None):
        return Tool(name=name, description=desc,
                    inputSchema={"type":"object","properties": props or {}})
    return [
        t("run_command",  "Run a whitelisted red-team command against the lab subnet.",
          {"command": {"type":"string","description":"e.g. 'nmap -sV 192.168.56.102'"}}),
        t("ask_ollama",   "Query local Ollama LLM for red-team guidance (100% local).",
          {"prompt": {"type":"string"}, "model": {"type":"string","default":"dolphin-llama3"}}),
        t("scan_subnet",  f"Quick nmap ping-sweep of {SUBNET}."),
        t("list_tools",   "Show security policy and permitted binaries."),
        t("audit_log",    "Show last N lines of the audit log.",
          {"lines": {"type":"integer","default":20}}),
    ]

@app.call_tool()
async def call_tool(name, arguments):
    if name == "run_command":
        cmd = arguments.get("command","").strip()
        ok, reason = _validate(cmd)
        if not ok:
            _audit("run_command", cmd, f"BLOCKED: {reason}")
            return txt(f"BLOCKED\n{reason}")
        _audit("run_command", cmd, "EXECUTING")
        try:
            out = await _run_shell(cmd)
            _audit("run_command", cmd, "OK")
            return txt(f"$ {cmd}\n{'─'*60}\n{out}")
        except Exception as e:
            _audit("run_command", cmd, f"ERROR:{e}")
            return txt(f"Error: {e}")

    elif name == "ask_ollama":
        prompt = arguments.get("prompt","")
        model  = arguments.get("model","dolphin-llama3")
        _audit("ask_ollama", prompt[:100], "REQUESTING")
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(f"http://{OLLAMA}/api/generate",
                                 json={"model":model,"prompt":prompt,"stream":False})
                r.raise_for_status()
                _audit("ask_ollama", prompt[:100], "OK")
                return txt(f"[{model}]\n\n{r.json().get('response','(empty)')}")
        except httpx.ConnectError:
            return txt(f"Cannot reach Ollama at {OLLAMA}.\n"
                       f"Run: OLLAMA_HOST={OLLAMA} ollama serve")
        except Exception as e:
            return txt(f"Ollama error: {e}")

    elif name == "scan_subnet":
        out = await _run_shell(f"nmap -sn {SUBNET} --open")
        hosts = [l for l in out.splitlines() if "Nmap scan report" in l]
        return txt(f"Live hosts in {SUBNET}:\n" + ("\n".join(hosts) or "None found."))

    elif name == "list_tools":
        rows = "\n".join(f"  {k:<18} {v}" for k,v in sorted(TOOLS.items()))
        return txt(f"Subnet : {SUBNET}\nOllama : {OLLAMA}\nTimeout: {TIMEOUT}s\n\n{rows}")

    elif name == "audit_log":
        n = int(arguments.get("lines", 20))
        path = LOG / "audit.jsonl"
        if not path.exists(): return txt("No audit log yet.")
        lines = path.read_text().splitlines()[-n:]
        out = []
        for l in lines:
            try:
                e = json.loads(l)
                out.append(f"{e['ts']}  {e['action']:<14} {e['result']}\n  {e['detail']}")
            except: out.append(l)
        return txt("\n\n".join(out))

    return txt(f"Unknown tool: {name}")

async def main():
    log.info("Starting | subnet=%s | ollama=%s | tools=%s", SUBNET, OLLAMA, len(TOOLS))
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
