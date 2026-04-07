import subprocess
import logging

logger = logging.getLogger("ids.ip_blocker")

def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def is_blocked(ip):
    rc, _, _ = _run(["iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"])
    return rc == 0

def block_ip(ip, reason=""):
    if ip in ("127.0.0.1", "::1", "0.0.0.0"):
        logger.warning(f"[BLOCK] Refused to block loopback: {ip}")
        return False
    if is_blocked(ip):
        logger.info(f"[BLOCK] Already blocked: {ip}")
        return False
    rc, _, err = _run(["iptables", "-I", "INPUT", "1", "-s", ip, "-j", "DROP"])
    if rc == 0:
        logger.warning(f"[BLOCK] Blocked {ip} — {reason}")
        return True
    logger.error(f"[BLOCK] Failed to block {ip}: {err}")
    return False

def unblock_ip(ip):
    if not is_blocked(ip):
        return False
    rc, _, _ = _run(["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"])
    return rc == 0

def list_blocked():
    rc, out, _ = _run(["iptables", "-L", "INPUT", "-n"])
    if rc != 0:
        return []
    blocked = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "DROP":
            blocked.append(parts[3])
    return blocked
