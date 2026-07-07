#!/bin/bash
# ============================================================
# install-services.sh
# Run on gw-dmz as: sudo bash install-services.sh
#
# Installs and enables:
#   1. rl-firewall.service        — main RL firewall process
#   2. rl-firewall-metrics.service — Prometheus metrics exporter
#
# After this script, both services start automatically on boot.
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'
BLD='\033[1m'; RST='\033[0m'
log()  { echo -e "${GRN}[install]${RST} $*"; }
warn() { echo -e "${YLW}[warn]${RST}   $*"; }
die()  { echo -e "${RED}[error]${RST}  $*"; exit 1; }

[[ $EUID -ne 0 ]] && die "Run with sudo: sudo bash $0"

BASE="/home/adam/rl-firewall"

# ── Verify the RL firewall directory exists ───────────────────
[[ -d "$BASE" ]] || die "RL firewall directory not found: $BASE"
[[ -f "$BASE/rl_firewall.py" ]] || die "rl_firewall.py not found in $BASE"
[[ -f "$BASE/venv/bin/python" ]] || die "Python venv not found in $BASE/venv"

log "Installing systemd services..."

# ── Copy service files ────────────────────────────────────────
cp "$BASE/rl-firewall.service"         /etc/systemd/system/
cp "$BASE/rl-firewall-metrics.service" /etc/systemd/system/

log "  ✓ Service files copied to /etc/systemd/system/"

# ── Ensure log directory exists and is writable ───────────────
mkdir -p "$BASE/logs"
mkdir -p "$BASE/models"
log "  ✓ Log and model directories verified"

# ── Make scripts executable ───────────────────────────────────
chmod +x "$BASE/rules/setup_nfqueue.sh"
chmod +x "$BASE/rules/teardown_nfqueue.sh"
log "  ✓ Scripts made executable"

# ── Reload systemd and enable services ───────────────────────
systemctl daemon-reload
systemctl enable rl-firewall.service
systemctl enable rl-firewall-metrics.service
log "  ✓ Services enabled for autostart"

# ── Ensure nfqueue module loads on boot ──────────────────────
echo "nfnetlink_queue" > /etc/modules-load.d/nfqueue.conf
log "  ✓ nfnetlink_queue module set to load on boot"

# ── Start services now ────────────────────────────────────────
log "Starting services..."

# Kill any existing manual runs first
pkill -f rl_firewall.py 2>/dev/null || true
pkill -f exporter.py    2>/dev/null || true
sleep 2

systemctl start rl-firewall.service
sleep 5
systemctl start rl-firewall-metrics.service
sleep 3

# ── Verify ───────────────────────────────────────────────────
echo ""
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
echo -e "${GRN}  Service Status${RST}"
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
echo ""

for svc in rl-firewall rl-firewall-metrics; do
    state=$(systemctl is-active "$svc.service" 2>/dev/null || echo "unknown")
    if [[ "$state" == "active" ]]; then
        echo -e "  ${GRN}✓${RST} $svc.service — ${GRN}running${RST}"
    else
        echo -e "  ${RED}✗${RST} $svc.service — ${RED}$state${RST}"
        echo -e "    Check: journalctl -u $svc.service -n 20"
    fi
done

echo ""

# Check Prometheus metrics are available
if curl -s http://localhost:9101/metrics | grep -q rl_firewall_packets; then
    echo -e "  ${GRN}✓${RST} Prometheus metrics available at http://localhost:9101/metrics"
else
    warn "  Prometheus metrics not yet available — metrics exporter may still be starting"
fi

echo ""
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
echo -e "  Useful commands:"
echo -e "  ${BLD}sudo systemctl status rl-firewall${RST}          — check status"
echo -e "  ${BLD}sudo journalctl -u rl-firewall -f${RST}          — live logs"
echo -e "  ${BLD}tail -f $BASE/logs/firewall.log${RST}  — agent decisions"
echo -e "  ${BLD}sudo systemctl stop rl-firewall${RST}            — stop (restores forwarding)"
echo -e "  ${BLD}sudo systemctl restart rl-firewall${RST}         — restart"
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
