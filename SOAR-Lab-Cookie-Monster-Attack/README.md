🍪 SOAR Lab: Cookie Monster Attack – Detection & Response

## Project Overview

This lab demonstrates a Security Orchestration, Automation, and Response (SOAR) workflow using LimaCharlie EDR to detect, investigate, and respond to a simulated cyberattack.  
The focus of this lab is understanding **detection coverage, telemetry gaps, and investigative workflows**, rather than assuming perfect prevention.

**Duration:** 3 days  
**Difficulty:** Intermediate  
**Tools Used:** VirtualBox, Ubuntu Server, Windows 10, Kali Linux, LimaCharlie, Sliver C2

---

## Lab Architecture

### Infrastructure Components

| Component | Role | OS | IP Address |
|-----------|------|----|-----------|
| Gateway VM | DNS / DHCP / Router | Ubuntu Server 22.04 LTS | 10.50.50.1 |
| Windows Sensor | Target / Victim | Windows 10 Pro | 10.50.50.117 (DHCP) |
| Kali Attacker | Red Team | Kali Linux 2024.4 | 10.50.50.155 (DHCP) |
| LimaCharlie | EDR / SOAR Platform | Cloud-based | N/A |

---

### Network Topology

```text
Internet
   ↕
[NAT Adapter]
   ↕
Gateway VM (10.50.50.1)
├─ dnsmasq (DHCP / DNS)
├─ iptables (NAT / Firewall)
└─ IPv4 forwarding
   ↕
[Internal Network: soarlab]
   ↕
   ├─ Windows Sensor (10.50.50.117)
   │   └─ LimaCharlie Agent
   │
   └─ Kali Attacker (10.50.50.155)
       └─ Sliver C2 Server
