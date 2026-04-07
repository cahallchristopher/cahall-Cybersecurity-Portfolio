import urllib.request
import json
import logging
from functools import lru_cache

logger = logging.getLogger("ids.geoip")
_API = "http://ip-api.com/json/{ip}?fields=status,country,regionName,city,org,query"

@lru_cache(maxsize=1024)
def lookup(ip):
    if _is_private(ip):
        return {"ip": ip, "country": "Private", "region": "", "city": "", "isp": "", "status": "private"}
    try:
        with urllib.request.urlopen(_API.format(ip=ip), timeout=3) as r:
            d = json.loads(r.read().decode())
        return {
            "ip":      d.get("query", ip),
            "country": d.get("country", "Unknown"),
            "region":  d.get("regionName", ""),
            "city":    d.get("city", ""),
            "isp":     d.get("org", ""),
            "status":  d.get("status", "fail"),
        }
    except Exception as e:
        logger.debug(f"GeoIP failed for {ip}: {e}")
        return {"ip": ip, "country": "Unknown", "region": "", "city": "", "isp": "", "status": "error"}

def _is_private(ip):
    return any(ip.startswith(p) for p in (
        "10.", "192.168.", "127.", "172.16.", "172.17.", "172.18.",
        "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
        "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
        "172.29.", "172.30.", "172.31.", "169.254.",
    ))

def format_location(geo):
    parts = [p for p in [geo.get("city"), geo.get("region"), geo.get("country")] if p]
    return ", ".join(parts) if parts else "Unknown"

