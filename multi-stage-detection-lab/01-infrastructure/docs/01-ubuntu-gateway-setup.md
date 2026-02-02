# Ubuntu Gateway Setup Guide

## Overview

This guide documents the complete setup of the Ubuntu Server gateway for the Multi-Stage Attack Detection Lab. The gateway provides DHCP, DNS, and NAT routing for the internal lab network.

---

## Prerequisites

- Ubuntu Server 22.04 LTS installed
- 2GB RAM, 20GB disk
- Two network interfaces:
  - `enp0s3` - NAT (Internet access)
  - `enp0s8` - Internal Network "SOARLab"

---

## Architecture
```
                    Internet
                        │
                        │ (NAT)
                        ▼
            ┌─────────────────────────┐
            │   Ubuntu Gateway        │
            │                         │
            │   enp0s3: 10.0.2.15/24 │ (WAN - DHCP from VirtualBox)
            │   enp0s8: 10.50.50.1/24│ (LAN - Static)
            │                         │
            │   Services:             │
            │   • dnsmasq (DHCP/DNS)  │
            │   • iptables (NAT)      │
            │   • IP forwarding       │
            └────────────┬────────────┘
                         │
                10.50.50.0/24
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼───┐        ┌───▼───┐      ┌───▼───┐
    │ Kali  │        │Win10  │      │ Other │
    │.50.10X│        │.50.10Y│      │  VMs  │
    └───────┘        └───────┘      └───────┘
```

---

## Installation Methods

### Method 1: Automated Script (Recommended)

The automated setup script handles all configuration automatically.

**Download and run:**
```bash
# Download the script
wget https://raw.githubusercontent.com/cahallchristopher/cahall-Cybersecurity-Portfolio/main/multi-stage-detection-lab/configs/ubuntu-gateway/setup-soar-gateway.sh

# Make executable
chmod +x setup-soar-gateway.sh

# Run the script
./setup-soar-gateway.sh
```

**The script will:**
1. ✅ Verify Ubuntu version
2. ✅ Configure temporary DNS for package installation
3. ✅ Enable IPv4 forwarding
4. ✅ Install dnsmasq and iptables-persistent
5. ✅ Configure dnsmasq for DHCP/DNS
6. ✅ Set up systemd dependencies
7. ✅ Configure NAT and firewall rules
8. ✅ Verify all services

---

### Method 2: Manual Installation

If you prefer to understand each step, follow the manual process below.

#### Step 1: Enable IP Forwarding
```bash
# Create sysctl configuration
sudo tee /etc/sysctl.d/99-soar-forwarding.conf > /dev/null << EOF
# SOAR Lab IPv4 forwarding configuration
net.ipv4.ip_forward=1
net.ipv4.conf.all.accept_redirects=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.all.accept_source_route=0
net.ipv4.conf.default.accept_redirects=0
net.ipv4.conf.default.send_redirects=0
