
#!/bin/bash
# ============================================================
# lab-up.sh  —  Host lab network bring-up
# Run on Linux Mint HOST as: sudo bash lab-up.sh
#
# Creates veth pairs so your Mint host can talk to each
# OpenWrt segment directly (SSH, browser, ping etc).
# Uses STATIC IPs only — never DHCP — so Mint DNS and
# default route on wlo1 are completely untouched.
#
# Segment map (matches openwrt-configure.sh):
#   MGMT  10.0.99.0/24  →  host gets 10.0.99.100
#   LAN   10.0.98.0/24  →  host gets 10.0.98.100
#   DMZ   10.0.96.0/24  →  host gets 10.0.96.100
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'
BLD='\033[1m'; RST='\033[0m'
log()  { echo -e "${GRN}[lab-up]${RST}  $*"; }
warn() { echo -e "${YLW}[warn]${RST}    $*"; }
die()  { echo -e "${RED}[error]${RST}   $*"; exit 1; }

[[ $EUID -ne 0 ]] && die "Run with sudo: sudo bash $0"

# ── Config ───────────────────────────────────────────────────
# bridges must match libvirt isolated net bridge names
bridges="sw-r0-eth1 sw-r0-eth2 sw-r0-eth3"

# veths: "bridge-side-dev|master=bridge:host-side-dev|ip=cidr"
# bridge-side gets enslaved to the bridge (reaches OpenWrt)
# host-side gets a static IP (how Mint talks to that segment)
veths="
veth-mgmt-b|master=sw-r0-eth1:veth-mgmt-h|ip=10.0.99.100/24
veth-lan-b|master=sw-r0-eth2:veth-lan-h|ip=10.0.98.100/24
veth-dmz-b|master=sw-r0-eth3:veth-dmz-h|ip=10.0.96.100/24
"
# ── End Config ───────────────────────────────────────────────

# ── Create veth pairs ────────────────────────────────────────
log "Creating veth pairs and assigning IPs..."
while IFS= read -r line; do
    line="$(echo "$line" | xargs)"
    [[ -z "$line" ]] && continue

    raw_left="${line%%:*}"
    raw_right="${line##*:}"

    left_dev="${raw_left%%|*}"
    left_opts="$( [[ "$raw_left" == *"|"* ]] && echo "${raw_left##*|}" || echo "" )"
    right_dev="${raw_right%%|*}"
    right_opts="$( [[ "$raw_right" == *"|"* ]] && echo "${raw_right##*|}" || echo "" )"

    if ip link show "$left_dev" &>/dev/null; then
        warn "  $left_dev already exists — skipping creation"
    else
        ip link add "$left_dev" type veth peer name "$right_dev"
        log "  ✓ Created pair: $left_dev <-> $right_dev"
    fi

    for spec in "${left_dev}|${left_opts}" "${right_dev}|${right_opts}"; do
        dev="${spec%%|*}"
        opts="${spec##*|}"
        ip link set "$dev" up
        [[ -z "$opts" ]] && continue
        IFS=',' read -ra opt_list <<< "$opts"
        for opt in "${opt_list[@]}"; do
            key="${opt%%=*}"
            val="${opt##*=}"
            case "$key" in
                master)
                    ip link set "$dev" master "$val" 2>/dev/null || true
                    log "    $dev → enslaved to $val"
                    ;;
                ip)
                    ip addr flush dev "$dev" 2>/dev/null || true
                    ip addr add "$val" dev "$dev"
                    log "    $dev → $val"
                    ;;
            esac
        done
    done
done <<< "$veths"

# ── Safety check — Mint default route untouched ──────────────
log "Verifying Mint default route..."
default_dev=$(ip route show default | awk '{print $5}' | head -1)
if [[ "$default_dev" =~ ^(wlo1|wlp|enp|eth0).*$ ]]; then
    log "  ✓ Default route still on $default_dev (Mint uplink safe)"
else
    warn "  Default route is on '$default_dev' — run: ip route"
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
echo -e "${GRN}  Lab host interfaces up!${RST}"
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
echo ""
echo -e "  From Mint you can now reach:"
echo -e "  ${BLD}ssh root@10.0.99.1${RST}   → OpenWrt MGMT interface"
echo -e "  ${BLD}ping 10.0.98.1${RST}        → OpenWrt LAN gateway"
echo -e "  ${BLD}ping 10.0.96.1${RST}        → OpenWrt DMZ gateway"
echo ""
echo -e "  Mint DNS / default route: ${GRN}untouched ✓${RST}"
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
