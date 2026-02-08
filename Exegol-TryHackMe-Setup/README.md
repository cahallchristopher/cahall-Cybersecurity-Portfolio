# Exegol + TryHackMe Lab Setup

## 📋 Overview

This repository documents a complete **Exegol** penetration testing environment running inside a **Lubuntu 24.04 VirtualBox VM**, configured specifically for **TryHackMe** labs.

The focus is clarity, correctness, and real-world workflows — not shortcuts.

---

## 🎯 Project Goals

- Install Exegol using best practices (`pipx`)
- Maintain a persistent workspace for tools and loot
- Connect securely to TryHackMe via OpenVPN
- Handle container networking correctly (TUN + NET_ADMIN)
- Document the setup so it can be rebuilt and explained

---

## 🏗️ Architecture

┌─────────────────────────────────────────────────────┐
│ VirtualBox Host (Windows / macOS / Linux) │
│ └── Hardware Virtualization Enabled │
└──────────────────┬──────────────────────────────────┘
│
┌──────────────────▼──────────────────────────────────┐
│ Lubuntu 24.04 VM │
│ ├── Docker Engine │
│ ├── Exegol (installed via pipx) │
│ └── ~/exegol-workspace/ │
│ ├── vpn/ (TryHackMe .ovpn files) │
│ ├── tools/ (Scripts & helpers) │
│ └── loot/ (Notes & captures) │
└──────────────────┬──────────────────────────────────┘
│
┌──────────────────▼──────────────────────────────────┐
│ Exegol Docker Container (thm) │
│ ├── Community image │
│ ├── Mounted workspace (/workspace) │
│ └── OpenVPN client (manual) │
└─────────────────────────────────────────────────────┘


---

## ⚡ Features

- ✅ Clean Exegol install via `pipx`
- ✅ Persistent workspace mounted into container
- ✅ Correct OpenVPN + TUN handling
- ✅ No VPN leakage onto host
- ✅ Simple, readable documentation

---

## 📦 Prerequisites

### Host Machine

- VirtualBox 6.1+ / 7.x
- VT-x / AMD-V enabled
- 16 GB RAM recommended
- 50 GB free disk space

### VM

- Lubuntu 24.04 LTS
- 8 GB RAM (4 GB minimum)
- 4 CPU cores
- NAT or Bridged networking

---

## 🚀 Quick Start

### 1️⃣ Install Dependencies (Host VM)

```bash
sudo apt update && sudo apt install -y docker.io docker-compose git pipx
sudo systemctl enable docker --now
sudo usermod -aG docker $USER
pipx install exegol
pipx ensurepath
mkdir -p ~/exegol-workspace/{vpn,tools,loot}


Log out and log back in after this step so Docker group permissions apply.

2️⃣ Create the Exegol Container
exegol start thm -w ~/exegol-workspace --cap NET_ADMIN -d /dev/net/tun

3️⃣ Enter the Container
exegol exec thm


You should see a prompt similar to:

exegol-thm /workspace #

4️⃣ Connect to TryHackMe (Inside Container)
sudo openvpn /workspace/vpn/thm.ovpn &


Verify the VPN connection:

ip addr show tun0


A tun0 interface confirms successful connectivity.

