# Lab Infrastructure

**Purpose:** Automated setup and configuration of the complete detection lab environment.

---

## Overview

This section contains all scripts and configurations needed to deploy the 3-VM detection lab:
```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Ubuntu Gateway  │      │   Kali Linux     │      │   Windows 10     │
│  (10.50.50.1)    │◄────►│  (10.50.50.100)  │◄────►│  (10.50.50.15X)  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
         │                        │                          │
    dnsmasq, NAT          Sliver C2, Tools      LimaCharlie, Sysmon
```

---

## Quick Start
```bash
# 1. Create Ubuntu Gateway
cd automation
./create-ubuntu-gateway-vm.sh

# 2. Install Ubuntu Server
# Follow: docs/01-ubuntu-gateway-setup.md

# 3. Configure Gateway
wget https://raw.githubusercontent.com/cahallchristopher/cahall-Cybersecurity-Portfolio/main/multi-stage-detection-lab/01-infrastructure/configs/ubuntu-gateway/setup-soar-gateway.sh
chmod +x setup-soar-gateway.sh
./setup-soar-gateway.sh

# 4. Deploy Kali VM
./create-kali-vm.sh

# 5. Deploy Windows VM
./create-windows-vm.sh
```

---

## Contents

### automation/
VM creation scripts using VBoxManage
- `create-ubuntu-gateway-vm.sh` - Ubuntu Server VM
- `create-kali-vm.sh` - Kali Linux VM (red team)
- `create-windows-vm.sh` - Windows 10 VM (blue team)

### configs/
Configuration files for each VM
- `ubuntu-gateway/` - dnsmasq, iptables, network
- `kali-attacker/` - Tools, scripts, post-install
- `windows-victim/` - Sysmon, LimaCharlie, EDR

### docs/
Installation and setup guides
- `01-ubuntu-gateway-setup.md` - Complete gateway guide
- `02-kali-setup.md` - Kali configuration
- `03-windows-setup.md` - Windows + EDR setup
- `gateway-quick-reference.md` - Quick commands

---

## Network Configuration

**Internal Network:** SOARLab (10.50.50.0/24)

| Host | IP | Role | Services |
|------|-----|------|----------|
| Ubuntu Gateway | 10.50.50.1 | Router/DNS/DHCP | dnsmasq, iptables NAT |
| Kali Linux | 10.50.50.100 | Red Team | Sliver C2, attack tools |
| Windows 10 | 10.50.50.150+ | Blue Team | LimaCharlie, Sysmon |

---

## Documentation

- [Ubuntu Gateway Setup](docs/01-ubuntu-gateway-setup.md)
- [Kali Linux Setup](docs/02-kali-setup.md)
- [Windows 10 Setup](docs/03-windows-setup.md)
- [Quick Reference](docs/gateway-quick-reference.md)

