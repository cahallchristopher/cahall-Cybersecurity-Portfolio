#!/bin/bash

# SOAR Gateway Setup Script for Ubuntu 22.04 LTS
# Purpose: Configure DNS/DHCP gateway for LimaCharlie SOAR lab
# Usage: ./setup-soar-gateway.sh

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[+]${NC} $1"
}

error() {
    echo -e "${RED}[!]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[*]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Use sudo when needed."
   exit 1
fi

# Verify Ubuntu version
log "Verifying Ubuntu version..."
if ! grep -q "22.04" /etc/os-release; then
    warn "This script is designed for Ubuntu 22.04 LTS. Proceeding anyway..."
fi

# Configuration variables
INTERNAL_INTERFACE="${INTERNAL_INTERFACE:-enp0s8}"
EXTERNAL_INTERFACE="${EXTERNAL_INTERFACE:-enp0s3}"
DHCP_RANGE_START="${DHCP_RANGE_START:-10.50.50.50}"
DHCP_RANGE_END="${DHCP_RANGE_END:-10.50.50.200}"
GATEWAY_IP="${GATEWAY_IP:-10.50.50.1}"
SUBNET="${SUBNET:-10.50.50.0/24}"

log "Configuration:"
echo "  Internal Interface: $INTERNAL_INTERFACE"
echo "  External Interface: $EXTERNAL_INTERFACE"
echo "  DHCP Range: $DHCP_RANGE_START - $DHCP_RANGE_END"
echo "  Gateway IP: $GATEWAY_IP"
echo "  Subnet: $SUBNET"
echo ""
read -p "Continue with this configuration? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    error "Setup cancelled by user"
    exit 1
fi

# Temporary DNS fix for apt
log "Configuring temporary DNS for package installation..."
sudo rm -f /etc/resolv.conf
echo -e "nameserver 1.1.1.1\nnameserver 8.8.8.8" | sudo tee /etc/resolv.conf > /dev/null

# Enable IPv4 forwarding
log "Enabling IPv4 forwarding..."
cat <<EOF | sudo tee /etc/sysctl.d/99-soar-forwarding.conf > /dev/null
# SOAR Lab IPv4 forwarding configuration
net.ipv4.ip_forward=1
net.ipv4.conf.all.accept_redirects=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.all.accept_source_route=0
net.ipv4.conf.default.accept_redirects=0
net.ipv4.conf.default.send_redirects=0
EOF

sudo sysctl --system > /dev/null 2>&1
log "IPv4 forwarding enabled"

# Update package lists and install dnsmasq
log "Updating package lists..."
sudo apt update -qq

log "Installing dnsmasq and dependencies..."
sudo DEBIAN_FRONTEND=noninteractive apt install -y dnsmasq iptables-persistent > /dev/null 2>&1

# Stop dnsmasq before configuration
log "Stopping dnsmasq for configuration..."
sudo systemctl stop dnsmasq

# Configure dnsmasq
log "Configuring dnsmasq for SOAR lab..."
cat <<EOF | sudo tee /etc/dnsmasq.d/soar.conf > /dev/null
# SOAR Lab dnsmasq configuration
# Internal network interface
interface=$INTERNAL_INTERFACE

# Don't bind to localhost
except-interface=lo

# DNS port
port=53

# DHCP configuration
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,12h
dhcp-option=option:router,$GATEWAY_IP
dhcp-option=option:dns-server,$GATEWAY_IP

# Upstream DNS servers
server=1.1.1.1
server=8.8.8.8

# Logging
log-queries
log-dhcp
log-facility=/var/log/dnsmasq.log

# Bind to interfaces dynamically
bind-dynamic

# Don't read /etc/resolv.conf for upstream servers
no-resolv

# Don't read /etc/hosts
no-hosts

# Cache size
cache-size=1000
EOF

# Create log file
sudo touch /var/log/dnsmasq.log
sudo chown dnsmasq:nogroup /var/log/dnsmasq.log

# Configure systemd to wait for internal interface
log "Configuring dnsmasq systemd dependencies..."
sudo mkdir -p /etc/systemd/system/dnsmasq.service.d

cat <<EOFSYSTEMD | sudo tee /etc/systemd/system/dnsmasq.service.d/wait-for-interface.conf > /dev/null
[Unit]
Requires=sys-subsystem-net-devices-$INTERNAL_INTERFACE.device
After=sys-subsystem-net-devices-$INTERNAL_INTERFACE.device
EOFSYSTEMD

# Reload systemd daemon
sudo systemctl daemon-reload

# Restart dnsmasq
log "Starting dnsmasq service..."
sudo systemctl restart dnsmasq
sudo systemctl enable dnsmasq

if ! sudo systemctl is-active --quiet dnsmasq; then
    error "dnsmasq failed to start. Check logs with: sudo journalctl -u dnsmasq"
    exit 1
fi

log "dnsmasq configured to wait for $INTERNAL_INTERFACE on boot"

# Configure system DNS to use dnsmasq
log "Configuring system DNS to use local dnsmasq..."
sudo rm -f /etc/resolv.conf
echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf > /dev/null
sudo chattr +i /etc/resolv.conf
log "System DNS locked to localhost"

# Flush existing firewall rules
log "Flushing existing firewall rules..."
sudo iptables -F
sudo iptables -t nat -F
sudo iptables -X

# Configure firewall rules
log "Applying NAT and forwarding rules..."

# Set default policies
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow established connections
sudo iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow forwarding from internal to external interface
sudo iptables -A FORWARD -i $INTERNAL_INTERFACE -o $EXTERNAL_INTERFACE -j ACCEPT

# NAT configuration for internal network
sudo iptables -t nat -A POSTROUTING -s $SUBNET -o $EXTERNAL_INTERFACE -j MASQUERADE

# Allow DNS and DHCP on internal interface
sudo iptables -A INPUT -i $INTERNAL_INTERFACE -p udp --dport 53 -j ACCEPT
sudo iptables -A INPUT -i $INTERNAL_INTERFACE -p tcp --dport 53 -j ACCEPT
sudo iptables -A INPUT -i $INTERNAL_INTERFACE -p udp --dport 67 -j ACCEPT

# Save firewall rules
log "Saving iptables rules..."
sudo mkdir -p /etc/iptables
sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null

# Verification
log "Verifying configuration..."
echo ""

if sudo systemctl is-active --quiet dnsmasq; then
    echo -e "${GREEN}✓${NC} dnsmasq is running"
else
    echo -e "${RED}✗${NC} dnsmasq is NOT running"
fi

if sysctl net.ipv4.ip_forward | grep -q "= 1"; then
    echo -e "${GREEN}✓${NC} IPv4 forwarding is enabled"
else
    echo -e "${RED}✗${NC} IPv4 forwarding is NOT enabled"
fi

if sudo iptables -t nat -L POSTROUTING -n | grep -q "MASQUERADE"; then
    echo -e "${GREEN}✓${NC} NAT masquerading is configured"
else
    echo -e "${RED}✗${NC} NAT masquerading is NOT configured"
fi

echo ""
log "SOAR Gateway setup complete!"
echo ""
echo "Next steps:"
echo "  1. Configure Kali and Windows VMs on Internal Network 'SOARLab'"
echo "  2. Verify VMs receive IP in range $DHCP_RANGE_START - $DHCP_RANGE_END"
echo "  3. Test internet connectivity from VMs"
echo "  4. Install LimaCharlie sensor on Windows VM"
echo ""
echo "Useful commands:"
echo "  - View DHCP leases: cat /var/lib/misc/dnsmasq.leases"
echo "  - View dnsmasq logs: sudo tail -f /var/log/dnsmasq.log"
echo "  - View firewall rules: sudo iptables -L -n -v"
echo "  - View NAT rules: sudo iptables -t nat -L -n -v"
echo ""
