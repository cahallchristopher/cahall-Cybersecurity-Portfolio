# 🛡️ KVM Cyber Range

A fully segmented cybersecurity home lab built with KVM/libvirt,
OpenWrt firewall, Windows Active Directory, and AI-powered traffic
analysis using local LLMs.

## 🏗️ Architecture

```
[Internet]
     │
  nat-wan (NAT)
     │
[OpenWrt Router] ← firewall/router
  ├── br-lan   192.168.1.0/24  ← Kali attacker
  ├── br-dmz   10.10.10.0/24   ← Metasploitable2
  ├── br-ad    10.20.20.0/24   ← Windows AD (DC01)
  └── br-mgmt  10.99.99.0/24   ← Capture VM
```

## 🖥️ VMs

| VM | Role | IP | Network |
|----|------|----|---------|
| OpenWrt | Firewall/Router | gateway | All |
| Kali Linux | Attacker | 192.168.1.x | br-lan |
| Metasploitable2 | Vulnerable target | 10.10.10.100 | br-dmz |
| Windows Server 2022 | Domain Controller | 10.20.20.10 | br-ad |
| Xubuntu | Capture + Analysis | 10.99.99.50 | br-mgmt |

## ⚔️ Attack Scenarios

| Attack | Tool | MITRE ID |
|--------|------|----------|
| Kerberoasting | impacket-GetUserSPNs | T1558.003 |
| SMB Enumeration | crackmapexec | T1021.002 |
| Password Spray | crackmapexec | T1110.003 |
| Pass-the-Hash | mimikatz | T1550.002 |
| AD Enumeration | bloodhound-python | T1069.002 |

## 🤖 AI Analysis

Local LLM analysis with Q-learning feedback loop:
```bash
python3 scripts/analyze_rl.py capture.pcap
```

## 📁 Project Structure

```
cyber-range/
├── README.md              ← This file
├── cyber-range-setup.md   ← Full setup guide
├── networks/              ← libvirt network XMLs
├── hooks/                 ← libvirt hook scripts
├── scripts/               ← Analysis tools
├── docs/                  ← Additional documentation
└── videos/                ← Walkthrough videos
```

## ⚠️ Disclaimer

For **educational purposes only**.
All attacks performed in isolated virtual environment.
