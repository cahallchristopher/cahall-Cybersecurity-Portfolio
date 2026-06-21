## Home Cyber Range: Virtualized Network with Red/Blue Segmentation, IDS, and SIEM

Built a home cyber range that simulates a small enterprise network on a single Linux Mint workstation.

Designed separate red team and blue team network segments using KVM, GNS3, and pfSense to create realistic attack and defense scenarios. Configured routing, firewall rules, and network isolation to control traffic between environments.

Deployed a security monitoring stack with Wazuh and Suricata to collect logs, detect threats, and generate alerts. Integrated endpoints, network sensors, and centralized logging to improve visibility across the environment.

Created attacker and target systems to test common attack techniques and validate detection rules. Used the lab to analyze network traffic, investigate alerts, and practice incident response workflows.

Deployed Wazuh and Suricata to collect logs, monitor network traffic, and generate security alerts. Created attacker and target systems to test detections and practice incident response workflows.

Installed, configured, and maintained every component by hand. Troubleshot issues involving virtual networking, DNS, routing, firewall policies, and service connectivity.

Documented the full build process, including terminal commands, configuration changes, problems encountered, and the steps used to resolve them.

**Technologies:** Linux Mint, KVM, GNS3, pfSense, Wazuh, Suricata, Virtual Networking, SIEM, IDS/IPS, Network Segmentation

Architecture
Internet
   │
Linux Mint host (wlo1 — real uplink, never modified)
   │
OpenWrt VM (virtualized router/firewall)
   ├── WAN   — internet uplink
   ├── MGMT  — administrative access (SSH)
   ├── LAN   — general segment, bridges into GNS3
   └── IOT   — isolated segment
        │
   GNS3 (network simulation platform)
        │
   pfSense (4-interface firewall, the core of the range)
   ├── WAN   — uplink through OpenWrt
   ├── LAN   — Blue Team / Wazuh SIEM (192.168.1.0/24)
   ├── DMZ   — Metasploitable2 target (192.168.20.0/24)
   └── RED   — Kali Linux attacker (192.168.30.0/24)

   Firewall rules enforce real segmentation: RED can attack DMZ, DMZ can never reach LAN, and a single narrow exception (UDP/514 syslog) lets DMZ ship logs to the SIEM without opening anything else.

   What's in this repo

Project Documentation Structure
	File	What It Covers
1	PROJECT_JOURNAL.md	Chronological build log covering every phase of the project from start to finish.
2	ARCHITECTURE.md	Network diagrams, IP address plan, firewall rules, and trust zones.
3	COMMAND_REFERENCE.md	Every command used during the build, grouped by tool and technology.
4	TROUBLESHOOTING_GUIDE.md	Issues encountered, root causes, troubleshooting steps, and fixes, organized by category.
5	LESSONS_LEARNED.md	What worked well, what could be improved, and what would be done differently in future builds.
