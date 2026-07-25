#!/bin/bash
# ============================================================
# OSINT Tool -- Start Script
# ============================================================
cd "$(dirname "$0")"

source venv/bin/activate

# Warn if Tor not running
if ! curl -s --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip \
     --max-time 5 | grep -q '"IsTor":true'; then
  echo ""
  echo "  WARNING: Tor not detected on port 9050"
  echo "  Maigret will fall back to direct connections."
  echo "  To enable Tor: sudo systemctl start tor@default"
  echo ""
fi

echo "Starting OSINT Tool at http://localhost:8000 ..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
