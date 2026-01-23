# Quick Start Guide

## Prerequisites
- VirtualBox installed
- 3 VMs: Ubuntu Server, Windows 10, Kali Linux
- LimaCharlie account

## Setup Steps

1. **Gateway VM**: Run `scripts/setup-soar-gateway.sh`
2. **Windows VM**: Install LimaCharlie sensor
3. **Kali VM**: Install Sliver C2
4. **LimaCharlie**: Add the 3 detection rules from `configs/`
5. **Execute**: Run the attack scenario

## Network Layout
- Gateway: 10.50.50.1
- Windows: 10.50.50.117 (DHCP)
- Kali: 10.50.50.155 (DHCP)

See main README.md for full documentation.
