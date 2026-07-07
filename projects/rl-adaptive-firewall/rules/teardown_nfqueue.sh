#!/bin/bash
# ============================================================
# rules/teardown_nfqueue.sh
# Removes nfqueue iptables rules and restores normal forwarding.
# Run this if the RL agent crashes to restore connectivity.
# ============================================================

set -euo pipefail

echo "[nfqueue] Removing nfqueue rules and restoring normal forwarding..."
iptables -F FORWARD
iptables -P FORWARD ACCEPT
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -i enp2s0 -o enp1s0 -j ACCEPT
iptables -A FORWARD -i enp1s0 -o enp2s0 -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "[nfqueue] Normal forwarding restored."
iptables -L FORWARD -n -v
