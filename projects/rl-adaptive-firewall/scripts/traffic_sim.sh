#!/bin/bash
# ============================================================
# traffic_sim.sh
# Run on CLIENT-LAN as: sudo bash traffic_sim.sh
#
# Alternates between normal and attack traffic in labelled
# bursts so the RL agent on gw-dmz can learn the difference.
#
# Normal traffic:
#   - DNS lookups
#   - HTTP/HTTPS requests (wget)
#   - ICMP ping (low rate)
#
# Attack traffic (simulated, contained to your lab):
#   - SYN flood (hping3)
#   - ICMP flood
#   - Port scan (nmap)
#   - UDP flood
#
# All attack traffic targets 10.0.96.1 (OpenWrt DMZ gateway)
# Nothing harmful leaves your lab.
# ============================================================

set -uo pipefail

RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
BLD='\033[1m'
RST='\033[0m'

GW="10.0.96.1"
EXTERNAL="8.8.8.8"
ROUNDS=${1:-5}

log_normal() { echo -e "${GRN}[NORMAL]${RST}  $*"; }
log_attack() { echo -e "${RED}[ATTACK]${RST}  $*"; }
log_info()   { echo -e "${YLW}[info]${RST}    $*"; }

check_tools() {
    local missing=()
    for tool in hping3 nmap wget curl; do
        command -v "$tool" &>/dev/null || missing+=("$tool")
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Missing tools: ${missing[*]}"
        echo "Install with: sudo apt install -y hping3 nmap wget curl"
        exit 1
    fi
}

normal_dns() {
    log_normal "DNS lookups..."
    for domain in google.com cloudflare.com github.com ubuntu.com debian.org; do
        nslookup "$domain" 8.8.8.8 &>/dev/null && echo "  resolved: $domain"
        sleep 0.5
    done
}

normal_http() {
    log_normal "HTTP/HTTPS requests..."
    for url in "http://example.com" "https://www.google.com" "https://cloudflare.com"; do
        wget -q --timeout=5 -O /dev/null "$url" 2>/dev/null \
            && echo "  fetched: $url" \
            || echo "  timeout: $url"
        sleep 1
    done
}

normal_ping() {
    log_normal "Low-rate ICMP ping..."
    ping -c 5 -i 0.5 "$EXTERNAL" | grep -E "bytes|statistics" || true
}

normal_mixed() {
    log_normal "Mixed normal traffic burst..."
    normal_dns &
    normal_ping &
    normal_http &
    wait
}

attack_syn_flood() {
    log_attack "SYN flood → ${GW}:80 (10 seconds)"
    sudo timeout 10 hping3 --syn --flood --rand-source -p 80 "$GW" 2>/dev/null || true
    log_attack "SYN flood done"
}

attack_icmp_flood() {
    log_attack "ICMP flood → ${GW} (8 seconds)"
    sudo timeout 8 hping3 --icmp --flood "$GW" 2>/dev/null || true
    log_attack "ICMP flood done"
}

attack_port_scan() {
    log_attack "Port scan → ${GW} (top 1000 ports)"
    sudo nmap -sS -T4 --top-ports 1000 -n "$GW" 2>/dev/null | tail -5 || true
    log_attack "Port scan done"
}

attack_udp_flood() {
    log_attack "UDP flood → ${GW}:53 (6 seconds)"
    sudo timeout 6 hping3 --udp --flood -p 53 "$GW" 2>/dev/null || true
    log_attack "UDP flood done"
}

attack_slow_scan() {
    log_attack "Slow stealth scan → ${GW}"
    sudo nmap -sS -T2 -p 22,80,443,8080,8443,3306,5432 "$GW" 2>/dev/null | tail -5 || true
    log_attack "Slow scan done"
}

main() {
    check_tools

    echo ""
    echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
    echo -e "${BLD}  RL Firewall Traffic Simulator${RST}"
    echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
    echo -e "  Rounds:        ${ROUNDS}"
    echo -e "  Attack target: ${GW} (inside lab only)"
    echo -e "  Normal target: ${EXTERNAL}"
    echo -e ""
    echo -e "  Watch gw-dmz logs:"
    echo -e "  tail -f ~/rl-firewall/logs/firewall.log"
    echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
    echo ""

    for round in $(seq 1 "$ROUNDS"); do
        echo ""
        echo -e "${BLD}── Round ${round}/${ROUNDS} ──────────────────────────────────────${RST}"

        log_info "NORMAL traffic phase (60s)..."
        normal_mixed
        sleep 5
        normal_dns
        sleep 5
        normal_ping
        sleep 5

        log_info "ATTACK traffic phase..."
        case $((round % 4)) in
            0) attack_syn_flood  ;;
            1) attack_port_scan  ;;
            2) attack_icmp_flood ;;
            3) attack_udp_flood  ;;
        esac
        sleep 3
        attack_slow_scan
        sleep 5

        log_info "Round ${round} complete. Pausing 10s..."
        sleep 10
    done

    echo ""
    echo -e "${GRN}Simulation complete.${RST}"
}

main
