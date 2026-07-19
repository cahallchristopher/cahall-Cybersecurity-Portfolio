# Exegol + TryHackMe Setup on Lubuntu VM

![Exegol](https://img.shields.io/badge/Exegol-v5.1.8-blue)
![Platform](https://img.shields.io/badge/Platform-Lubuntu%2024.04-orange)
![Docker](https://img.shields.io/badge/Docker-Required-blue)
![License](https://img.shields.io/badge/License-Personal%20Use-green)

## 📋 Overview

This repository documents the complete setup of **Exegol** (a powerful pentesting framework) on a **Lubuntu VirtualBox VM** with optimized performance settings for penetration testing and cybersecurity labs, specifically configured for **TryHackMe**.

## 🎯 Project Goals

- Install Exegol using best practices (pipx installation)
- Configure persistent workspace for tools and loot
- Set up OpenVPN integration for TryHackMe
- Optimize VirtualBox VM for maximum performance
- Create convenient aliases for common workflows

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│ VirtualBox Host (Windows/Mac/Linux)                 │
│  ├── Optimized VM Settings                          │
│  └── Hardware Virtualization Enabled                │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ Lubuntu 24.04 VM                                    │
│  ├── Docker Engine                                  │
│  ├── Exegol (via pipx)                             │
│  └── ~/exegol-workspace/                           │
│      ├── vpn/      (TryHackMe .ovpn files)         │
│      ├── tools/    (Custom scripts)                │
│      └── loot/     (Captured data)                 │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ Exegol Docker Container "thm"                       │
│  ├── Full pentesting suite                         │
│  ├── Mounted workspace (/workspace)                │
│  └── OpenVPN client                                │
└─────────────────────────────────────────────────────┘
```

## ⚡ Features

- ✅ **Optimized Installation**: Uses pipx for clean Python package management
- ✅ **Persistent Storage**: Workspace mounted for data persistence
- ✅ **TryHackMe Ready**: Pre-configured OpenVPN integration
- ✅ **Performance Tuned**: VirtualBox optimizations for smooth operation
- ✅ **Convenient Aliases**: Quick commands for common tasks
- ✅ **Best Practices**: Follows Linux FHS with proper directory structure

## 📦 Prerequisites

### Host Machine Requirements
- VirtualBox 6.1+ or 7.0+
- CPU with VT-x/AMD-V support (enabled in BIOS)
- Minimum 16GB RAM (8GB for VM)
- 50GB+ free disk space
- SSD recommended for best performance

### VM Specifications (Recommended)
- **OS**: Lubuntu 24.04 LTS
- **RAM**: 8GB (minimum 4GB)
- **CPU**: 4 cores
- **Disk**: 40GB dynamic VDI
- **Network**: NAT or Bridged

## 🚀 Quick Start

### 1. Install Exegol
```bash
# One-liner installation
sudo apt update && sudo apt install -y docker.io docker-compose git pipx && \
sudo systemctl enable docker --now && \
sudo usermod -aG docker $USER && \
pipx install exegol && \
pipx ensurepath && \
mkdir -p ~/exegol-workspace/{vpn,tools,loot}
```

### 2. Configure Aliases
```bash
cat >> ~/.bashrc << 'EOF'

# ─── Exegol Aliases ───────────────────────────────────────────
alias exegol-install='exegol install'
alias exegol-start='exegol start thm -w ~/exegol-workspace'
alias exegol-stop='exegol stop'
alias exegol-shell='exegol exec thm'
alias thm-vpn='sudo openvpn ~/workspace/vpn/*.ovpn &'
alias thm-check='ip addr show tun0'
alias exegol-thm='exegol start thm -w ~/exegol-workspace && exegol exec thm sudo openvpn ~/workspace/vpn/*.ovpn'
# ──────────────────────────────────────────────────────────────
EOF

source ~/.bashrc
```

### 3. Logout and Login
```bash
logout
# Required for Docker group permissions
```

### 4. Install Exegol Image
```bash
exegol install
# Choose "full" when prompted (recommended for pentesting)
```

### 5. Download TryHackMe VPN
1. Go to https://tryhackme.com/access
2. Download your `.ovpn` file
3. Copy to workspace:
```bash
cp ~/Downloads/*.ovpn ~/exegol-workspace/vpn/
```

### 6. Start Hacking!
```bash
# Start container with workspace
exegol-start

# Enter the container
exegol-shell

# Connect to TryHackMe (inside container)
sudo openvpn /workspace/vpn/*.ovpn &

# Verify VPN connection
ip addr show tun0
```

## 📚 Documentation

- [Complete Setup Commands](setup-commands.md) - Step-by-step installation guide
- [VirtualBox Optimization](virtualbox-optimization.md) - Performance tuning guide
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `exegol-install` | Install Exegol Docker image |
| `exegol-start` | Start THM container with workspace |
| `exegol-stop` | Stop the container |
| `exegol-shell` | Enter the container shell |
| `exegol-thm` | All-in-one: Start + Connect VPN |
| `thm-vpn` | Connect to TryHackMe VPN (inside container) |
| `thm-check` | Verify VPN connection |

## 🔧 Workspace Structure

```
~/exegol-workspace/
├── vpn/               # TryHackMe .ovpn files
│   └── yourname.ovpn
├── tools/             # Custom tools and scripts
│   └── custom-script.sh
└── loot/              # Captured flags, hashes, data
    └── machine-name/
        ├── flags.txt
        └── credentials.txt
```

## 📊 Performance Metrics

After optimization:
- **Boot Time**: ~15 seconds
- **Docker Start**: ~3 seconds
- **Container Launch**: ~2 seconds
- **VPN Connection**: ~5 seconds

## 🎓 Learning Outcomes

Through this project, I learned:
- Docker containerization for cybersecurity tools
- Python package management with pipx
- VirtualBox VM optimization techniques
- OpenVPN configuration and networking
- Linux system administration best practices
- Efficient pentesting workflow automation

## 🔐 Security Considerations

- ✅ Exegol containers are isolated from host system
- ✅ TryHackMe VPN credentials stored securely in workspace
- ✅ Docker daemon runs with proper user permissions
- ✅ All tools confined to container environment
- ⚠️ Remember: Only use on authorized systems and CTF platforms

## 📝 License

This documentation is for **personal educational use only**. Exegol is subject to its own [EULA](https://docs.exegol.com/legal/eula) and is strictly limited to personal, non-commercial, educational, or research purposes.

## 🙏 Acknowledgments

- [Exegol Project](https://github.com/ThePorgs/Exegol) by ThePorgs
- [TryHackMe](https://tryhackme.com) for providing awesome learning platform
- Lubuntu team for the lightweight distro

## 📧 Contact

**Christopher Cahall**
- GitHub: [@cahallchristopher](https://github.com/cahallchristopher)
- Portfolio: [Cybersecurity Portfolio](https://github.com/cahallchristopher/cahall-Cybersecurity-Portfolio)

---

**Last Updated**: February 2026
**Exegol Version**: v5.1.8
**Lubuntu Version**: 24.04 LTS
