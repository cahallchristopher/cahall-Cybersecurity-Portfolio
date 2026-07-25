#!/bin/bash
# ============================================================
# OSINT Tool -- One-Command Setup Script
# Tested on Ubuntu 24 / Debian / Linux x86_64
# ============================================================

set -e

echo ""
echo "============================================"
echo "  OSINT Tool -- Setup"
echo "============================================"
echo ""

echo "[1/4] Installing Tor..."
sudo apt update -q
sudo apt install -y tor torsocks
sudo systemctl start tor@default
sudo systemctl enable tor@default
sleep 5

TOR_CHECK=$(curl -s --socks5 127.0.0.1:9050 \
  https://check.torproject.org/api/ip --max-time 15 2>/dev/null || echo "{}")

if echo "$TOR_CHECK" | grep -q '"IsTor":true'; then
  TOR_IP=$(echo "$TOR_CHECK" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4)
  echo "  Tor verified -- exit IP: $TOR_IP"
else
  echo "  WARNING: Tor check failed -- verify manually"
fi

echo ""
echo "[2/4] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "  venv created"

echo ""
echo "[3/4] Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "[4/4] Setting up environment..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  Created .env from template"
  echo "  Add your API keys to .env:"
  echo "    HIBP_API_KEY=      (haveibeenpwned.com/API/Key)"
  echo "    NUMVERIFY_API_KEY= (numverify.com)"
else
  echo "  .env already exists -- skipping"
fi

chmod +x start.sh

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Run: ./start.sh"
echo "  Open: http://localhost:8000"
echo "============================================"
echo ""
