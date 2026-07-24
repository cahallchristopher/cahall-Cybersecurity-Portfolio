#!/bin/bash
# ============================================================
# OSINT Tool — One-Command Setup Script
# Tested on Ubuntu 24 / Debian / Linux x86_64
#
# Usage:
#   git clone https://github.com/cahallchristopher/cahall-Cybersecurity-Portfolio.git
#   cd cahall-Cybersecurity-Portfolio/projects/osint-tool
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh
# ============================================================

set -e  # Exit immediately on any error

echo ""
echo "============================================"
echo "  OSINT Tool — Setup"
echo "============================================"
echo ""

# ── Step 1: Install Tor ───────────────────────────────────
echo "[1/4] Installing Tor..."
sudo apt update -q
sudo apt install -y tor torsocks

# Start the actual Tor daemon (not the master launcher)
# Note: tor.service runs /bin/true and is NOT the daemon
# The real daemon is tor@default.service
sudo systemctl start tor@default
sudo systemctl enable tor@default

# Wait for Tor to bootstrap
echo "  Waiting for Tor to bootstrap..."
sleep 5

# Verify Tor is routing traffic
TOR_CHECK=$(curl -s --socks5 127.0.0.1:9050 \
  https://check.torproject.org/api/ip --max-time 15 2>/dev/null || echo "{}")

if echo "$TOR_CHECK" | grep -q '"IsTor":true'; then
  TOR_IP=$(echo "$TOR_CHECK" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4)
  echo "  ✓ Tor verified — exit IP: $TOR_IP"
else
  echo "  ⚠ Tor check failed — verify manually:"
  echo "    sudo systemctl status tor@default"
  echo "    curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip"
fi

echo ""

# ── Step 2: Create Python virtual environment ─────────────
echo "[2/4] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "  ✓ venv created with $(python3 --version)"

echo ""

# ── Step 3: Install Python dependencies ──────────────────
echo "[3/4] Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Verify key CLI tools installed correctly
echo ""
echo "  Verifying tool installations:"

if command -v sherlock &> /dev/null; then
  echo "  ✓ Sherlock installed"
else
  echo "  ✗ Sherlock not found — try: pip install sherlock-project"
fi

if command -v maigret &> /dev/null; then
  echo "  ✓ Maigret installed"
else
  echo "  ✗ Maigret not found — try: pip install maigret"
fi

echo ""

# ── Step 4: Configure environment ────────────────────────
echo "[4/4] Setting up environment..."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "  ✓ Created .env from template"
  echo ""
  echo "  ┌─────────────────────────────────────────────────┐"
  echo "  │  Optional: add API keys to .env for full power  │"
  echo "  │                                                 │"
  echo "  │  HIBP_API_KEY=      haveibeenpwned.com/API/Key  │"
  echo "  │  NUMVERIFY_API_KEY= numverify.com (free tier)   │"
  echo "  └─────────────────────────────────────────────────┘"
else
  echo "  .env already exists — skipping (your keys are safe)"
fi

chmod +x start.sh

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  To start the OSINT tool:"
echo "    source venv/bin/activate"
echo "    ./start.sh"
echo ""
echo "  Then open: http://localhost:8000"
echo "============================================"
echo ""
