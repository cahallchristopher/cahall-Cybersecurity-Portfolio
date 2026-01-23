# 🔧 Environment Setup

This document describes how the SOAR lab environment is built.

The focus is on clarity and repeatability.

---

## Phase 1: Gateway Configuration

The Ubuntu Server VM acts as the gateway for the SOAR lab.
It handles routing, DNS, DHCP, and firewall rules.

### Ubuntu Server Network Layout

- `enp0s3` – External interface (NAT / Internet)
- `enp0s8` – Internal SOAR lab network

### Netplan Configuration

Edit the Netplan file:

```bash
sudo nano /etc/netplan/01-netcfg.yaml
