#!/bin/bash
# ============================================================
# rules/setup_nfqueue.sh
# Sets up iptables to mirror forwarded traffic into NFQUEUE 0
# so the RL agent can inspect and act on every packet.
#
# Run as root: sudo bash rules/setup_nfqueue.sh
#
# To remove rules: sudo bash rules/teardown_nfqueue.sh
# ============================================================

set -euo pipefail

LAN_IFACE="enp2s0"   # packets coming FROM client-lan
WAN_IFACE="enp1s0"   # packets going TO internet via DMZ

echo "[nfqueue] Flushing existing FORWARD rules..."
iptables -F FORWARD

echo "[nfqueue] Setting default FORWARD policy to DROP..."
iptables -P FORWARD DROP

echo "[nfqueue] Allow established/related connections through without queuing..."
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

echo "[nfqueue] Queue new outbound packets from LAN for RL agent inspection..."
iptables -A FORWARD -i "$LAN_IFACE" -o "$WAN_IFACE" -m state --state NEW -j NFQUEUE --queue-num 0

echo "[nfqueue] Queue new inbound packets to LAN for RL agent inspection..."
iptables -A FORWARD -i "$WAN_IFACE" -o "$LAN_IFACE" -m state --state NEW -j NFQUEUE --queue-num 0

echo "[nfqueue] Allow loopback..."
iptables -A FORWARD -i lo -j ACCEPT

echo ""
echo "iptables FORWARD chain:"
iptables -L FORWARD -n -v
echo ""
echo "[nfqueue] Done. Start the RL agent to process queued packets."
echo "          Packets will BLOCK until the agent accepts/drops them."
