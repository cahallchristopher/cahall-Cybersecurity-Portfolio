# Home Cyber Range (SOC Analyst Lab)

## overview

i built a small cyber range to practice soc work in a realistic setup. it’s a virtual network with segmentation, logging, and detection tools.

it’s meant to simulate what you’d see in a basic enterprise environment. multiple zones, controlled traffic, and security monitoring in place.

---

## what this lab is

this is a segmented virtual network with attack and defense components.

it includes:
- network segmentation
- intrusion detection
- centralized logging
- siem-style analysis
- controlled attack simulation

---

## network layout

- **WAN** – simulated internet
- **LAN** – internal systems
- **DMZ** – exposed services
- **RED** – attacker network

traffic is restricted by default. only specific flows are allowed between zones.

---

## tools used

### network and virtualization
- OpenWrt (routing)
- pfSense (firewall)
- libvirt / KVM (virtual machines)

### attack simulation
- Kali Linux (attacker system)
- Metasploitable2 (vulnerable target)

### detection and logging
- Suricata (intrusion detection)
- Wazuh (log analysis / siem)
- syslog (log forwarding)

---

## what i practiced here

### network segmentation
i built a multi-zone network and enforced separation between systems.

everything is blocked by default. only required traffic is allowed through firewall rules.

---

### detection pipeline
i set up a basic detection flow:

suricata detects traffic  
logs get forwarded  
wazuh processes and shows alerts  

i tested this with custom rules to make sure alerts actually show up end to end.

---

### troubleshooting real issues

#### bridge interface issue
a virtual bridge kept coming back after i deleted it.

it wasn’t obvious at first. i checked running services, but that didn’t explain it.

eventually i traced it to a conflict between NetworkManager and libvirt.

i confirmed it by checking MAC addresses before and after reboot.

---

### legacy system support
i also worked with older systems that don’t behave well with modern tools.

- ubuntu 8.04
- fips-restricted amazon linux 2

i had to deal with broken repositories and missing packages. some things needed manual fixes instead of normal installs.

---

### siem and logging issues
at one point, logs were not showing in wazuh.

suricata was running, but alerts were not being ingested.

the issue ended up being a small xml config error. there was no obvious error message, so i had to check each step in the pipeline.

---

## current status

the lab is working.

- OpenWrt handles routing
- pfSense handles firewall rules
- Kali runs attack simulations
- Wazuh collects logs and shows alerts
- Suricata monitors LAN traffic

---

## known limitation

suricata only sees LAN traffic right now.

it does not inspect traffic between RED and DMZ yet. i plan to fix that later.

---

## files in this project

- `PROJECT_JOURNAL.md` – full build notes
- `TROUBLESHOOTING_GUIDE.md` – fixes and errors i ran into
- `LESSONS_LEARNED.md` – what i would improve next time

---

## why this matters

this setup helps me practice real soc tasks like:

- alert triage
- log analysis
- intrusion detection
- incident investigation
- network troubleshooting
