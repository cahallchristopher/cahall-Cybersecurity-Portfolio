# Operation Shadow Ledger - Attack Playbooks

This directory contains detailed adversary emulation scenarios for SOC analyst training and detection engineering.

---

## Overview

**Operation Shadow Ledger** is a comprehensive APT (Advanced Persistent Threat) simulation targeting a fictional financial institution. The playbook covers all 14 MITRE ATT&CK Enterprise tactics with realistic techniques, tools, and procedures used by modern threat actors.

---

## Purpose

### Training Objectives

1. **Understand the Full Attack Lifecycle**
   - From reconnaissance to ransomware deployment
   - See how attackers chain techniques together
   - Learn why each step is necessary

2. **Build Detection Engineering Skills**
   - Map attacks to MITRE ATT&CK framework
   - Create behavioral detection rules
   - Tune for false positives

3. **Practice Incident Response**
   - Identify indicators of compromise
   - Contain active threats
   - Perform root cause analysis

4. **Develop Threat Hunting Capabilities**
   - Hunt for persistent threats
   - Identify living-off-the-land techniques
   - Correlate events across systems

---

## Playbook Structure

### Operation Shadow Ledger

**File:** `operation-shadow-ledger.md`

**Target:** First National Digital Bank (Fictional)
- 500 employees
- Hybrid cloud infrastructure (AWS + on-prem)
- Windows Active Directory environment
- SQL Server databases (customer financial data)
- PCI-DSS compliance requirements

**Threat Actor:** APT-SimLab (Simulated)
- Motivation: Financial gain
- Sophistication: Advanced
- Tools: Custom malware, Sliver C2, Mimikatz, BloodHound
- TTPs: Similar to FIN7, Carbanak, Lazarus Group

**Timeline:** 72 hours (compressed for training)

**Scope:**
- 14 MITRE ATT&CK tactics
- 14 unique techniques (one per tactic)
- 30+ detection opportunities
- Multiple lateral movement paths
- Data exfiltration and ransomware

---

## Attack Phases

### Phase 1: Reconnaissance (Pre-Attack)
**Duration:** Day 0  
**Objective:** Gather intelligence on target organization  
**Techniques:**
- T1598.003: Spearphishing for Information
- LinkedIn OSINT
- DNS enumeration
- Technology stack identification

**Detection Difficulty:** None (external reconnaissance)

---

### Phase 2: Weaponization
**Duration:** Day 0-1  
**Objective:** Create custom malware  
**Techniques:**
- T1587.001: Develop Capabilities - Malware
- Sliver C2 implant generation
- Code signing with stolen certificate
- Evasion testing

**Detection Difficulty:** None (occurs on attacker infrastructure)

---

### Phase 3: Delivery & Initial Access
**Duration:** Day 1, 09:15 AM  
**Objective:** Compromise first victim  
**Techniques:**
- T1566.001: Spearphishing Attachment
- Macro-enabled Excel document
- Social engineering (bonus allocation theme)
- Targeting IT Manager (high privileges)

**Detection Opportunities:**
- Email gateway scanning
- Macro execution detection
- Behavioral analysis

---

### Phase 4: Execution & Persistence
**Duration:** Day 1, 09:18 AM - 09:30 AM  
**Objective:** Execute payload and maintain access  
**Techniques:**
- T1059.001: PowerShell
- T1547.001: Registry Run Keys
- T1053.005: Scheduled Tasks
- T1546.003: WMI Event Subscriptions

**Detection Opportunities:**
- Encoded PowerShell detection
- Registry monitoring
- WMI event subscription alerts

---

### Phase 5: Privilege Escalation
**Duration:** Day 1, 10:30 AM  
**Objective:** Gain SYSTEM privileges  
**Techniques:**
- T1134.001: Token Impersonation
- Stealing SYSTEM token from spoolsv.exe
- Creating new process with elevated privileges

**Detection Opportunities:**
- Suspicious process access
- Token theft indicators
- Unexpected privilege changes

---

### Phase 6: Defense Evasion
**Duration:** Day 1, 10:45 AM  
**Objective:** Remove forensic evidence  
**Techniques:**
- T1070.004: File Deletion
- T1070.001: Event Log Clearing
- Timestomping
- Disabling Windows Defender

**Detection Opportunities:**
- Event log cleared alerts
- Mass file deletion
- Security tool tampering

---

### Phase 7: Credential Access
**Duration:** Day 1, 11:00 AM  
**Objective:** Harvest credentials for lateral movement  
**Techniques:**
- T1003.001: LSASS Memory Dumping
- Mimikatz execution
- Password hash extraction
- Domain Admin credential theft

**Detection Opportunities:**
- LSASS process access
- Memory dump file creation
- Mimikatz-specific indicators

---

### Phase 8: Discovery
**Duration:** Day 1, 11:30 AM  
**Objective:** Map network and identify targets  
**Techniques:**
- T1087.002: Domain Account Discovery
- T1018: Remote System Discovery
- T1135: Network Share Discovery
- BloodHound enumeration

**Detection Opportunities:**
- Mass enumeration commands
- BloodHound data collection
- Unusual query patterns

---

### Phase 9: Lateral Movement
**Duration:** Day 1, 14:00 PM  
**Objective:** Access database server  
**Techniques:**
- T1021.001: RDP
- T1563.002: RDP Hijacking
- Pass-the-Hash authentication
- SQL Server compromise

**Detection Opportunities:**
- Unexpected RDP connections
- Session hijacking attempts
- Internal network scanning

---

### Phase 10: Collection
**Duration:** Day 1-2, 16:00 PM onwards  
**Objective:** Aggregate valuable data  
**Techniques:**
- T1005: Data from Local System
- SQL database backup
- File server document collection
- Email archive exfiltration

**Detection Opportunities:**
- Mass file access
- Unusual backup operations
- Large data aggregation

---

### Phase 11: Command and Control
**Duration:** Continuous  
**Objective:** Maintain covert communication  
**Techniques:**
- T1071.001: HTTPS C2
- Encrypted beaconing (60s intervals)
- Domain fronting
- DNS tunneling (backup)

**Detection Opportunities:**
- Beaconing pattern detection
- Unusual HTTPS connections
- DNS anomalies

---

### Phase 12: Exfiltration
**Duration:** Day 2, 02:00 AM  
**Objective:** Steal 1.2 GB of data  
**Techniques:**
- T1041: Exfiltration Over C2
- Chunked transfer (5 MB pieces)
- Bandwidth throttling
- Off-hours exfiltration

**Detection Opportunities:**
- Large outbound transfers
- Off-hours network activity
- Data volume anomalies

---

### Phase 13: Impact
**Duration:** Day 3, 03:30 AM  
**Objective:** Deploy ransomware  
**Techniques:**
- T1486: Data Encrypted for Impact
- T1490: Inhibit System Recovery
- Shadow copy deletion
- Mass file encryption

**Detection Opportunities:**
- Shadow copy deletion
- Mass file modifications
- Ransom note creation
- Wallpaper changes

---

## Technical Details

### Tools Used

**Attacker Tools:**
- Kali Linux 2024.1
- Sliver C2 Framework 1.5.42
- Mimikatz 2.2.0
- BloodHound 4.3.1
- Atomic Red Team
- Custom PowerShell scripts

**Defender Tools:**
- Windows 10 Pro (Build 19045)
- Sysmon 15.0
- LimaCharlie EDR
- Custom YAML detection rules
- Event log monitoring

**Network:**
- Ubuntu Server 22.04 LTS (Gateway)
- dnsmasq (DHCP/DNS)
- iptables (NAT/Firewall)
- Internal network: 10.50.50.0/24

---

## Detection Rules

### Coverage Matrix

| Phase | Techniques | Detection Rules | Coverage |
|-------|-----------|-----------------|----------|
| Initial Access | 1 | 2 | 100% |
| Execution | 1 | 3 | 100% |
| Persistence | 3 | 4 | 100% |
| Privilege Escalation | 1 | 2 | 100% |
| Defense Evasion | 2 | 3 | 100% |
| Credential Access | 1 | 4 | 100% |
| Discovery | 3 | 3 | 100% |
| Lateral Movement | 2 | 2 | 100% |
| Collection | 1 | 3 | 100% |
| C2 | 1 | 2 | 100% |
| Exfiltration | 1 | 1 | 100% |
| Impact | 2 | 4 | 100% |

**Total:** 30 detection rules covering all attack phases

---

## Using This Playbook

### For SOC Analysts

**Learning Path:**

1. **Read the full attack narrative**
   - Understand attacker motivations
   - See how techniques chain together
   - Note detection opportunities

2. **Study each phase in detail**
   - What tools were used?
   - Why did this technique succeed?
   - How could it be detected?

3. **Map to your environment**
   - Do you have similar systems?
   - Are these techniques relevant?
   - What are your detection gaps?

4. **Create detection rules**
   - Use the examples as templates
   - Tune for your environment
   - Test and validate

5. **Practice incident response**
   - How would you investigate?
   - What evidence would you collect?
   - How would you contain the threat?

### For Detection Engineers

**Workflow:**

1. **Deploy the lab environment**
   - Use provided automation scripts
   - Set up VirtualBox VMs
   - Configure network

2. **Install detection tools**
   - Sysmon on Windows
   - LimaCharlie EDR
   - SIEM integration (optional)

3. **Deploy detection rules**
   - Start with high-fidelity rules
   - Gradually add more coverage
   - Tune for false positives

4. **Execute attack scenarios**
   - Follow playbook step-by-step
   - Verify detections trigger
   - Measure response times

5. **Iterate and improve**
   - Analyze what worked
   - Fix detection gaps
   - Document lessons learned

### For Hiring Managers

**What This Demonstrates:**

✅ **Technical Depth**
- Understands full attack lifecycle
- Can map to MITRE ATT&CK
- Knows how attackers think

✅ **Practical Skills**
- Can write detection rules
- Understands EDR platforms
- Experience with SIEM correlation

✅ **Real-World Readiness**
- Not just theoretical knowledge
- Hands-on lab experience
- Can respond to actual incidents

✅ **Self-Directed Learning**
- Built this independently
- Researched techniques
- Created comprehensive documentation

✅ **Communication**
- Clear technical writing
- Can explain complex attacks
- Professional documentation

---

## Related Resources

### Documentation
- [Complete Attack Narrative](operation-shadow-ledger.md)
- [Detection Rules](../detection-rules/limacharlie/advanced/)
- [Lab Setup Guide](../docs/quick-setup.md)
- [Testing Results](../results/detection-testing-results.md)

### Code & Automation
- [VM Creation Scripts](../automation/)
- [Configuration Files](../configs/)
- [Helper Scripts](../configs/*/scripts/)

### Training Materials
- [MITRE ATT&CK Enterprise](https://attack.mitre.org/)
- [LimaCharlie Documentation](https://doc.limacharlie.io/)
- [Sliver C2 Wiki](https://github.com/BishopFox/sliver/wiki)

---

## Contributing

This playbook is designed for educational purposes. If you have suggestions for:

- Additional attack scenarios
- Improved detection rules
- Better documentation
- Realistic variations
