# Attack Playbooks

**Purpose:** Red team scenarios for testing detection capabilities.

---

## Operation Shadow Ledger

**File:** `operation-shadow-ledger.md`

Complete APT simulation covering all 14 MITRE ATT&CK tactics:

### Attack Timeline

**Day 0:** Reconnaissance  
**Day 1:** Initial Access → Execution → Persistence → Privilege Escalation  
**Day 2:** Credential Access → Discovery → Lateral Movement → Collection  
**Day 3:** Exfiltration → Impact (Ransomware)

### Target

First National Digital Bank (Fictional)
- 500 employees
- Hybrid infrastructure (AWS + on-prem)
- SQL databases with customer financial data
- Active Directory domain

### Attack Chain

1. **T1598.003** - Spearphishing for Information
2. **T1587.001** - Develop Malware (Sliver C2)
3. **T1566.001** - Spearphishing Attachment
4. **T1059.001** - PowerShell Execution
5. **T1547.001** - Registry Run Keys
6. **T1134.001** - Token Impersonation
7. **T1070.004** - File Deletion
8. **T1003.001** - LSASS Dumping
9. **T1087.002** - Domain Account Discovery
10. **T1021.001** - Remote Desktop Protocol
11. **T1005** - Data from Local System
12. **T1071.001** - Web Protocols (HTTPS C2)
13. **T1041** - Exfiltration Over C2
14. **T1486** - Data Encrypted for Impact

---

## Additional Scenarios

**Location:** `scenarios/`

Individual attack scenarios for focused testing:
- Macro-based phishing
- Credential harvesting
- CEO fraud (BEC)
- Ransomware deployment

---

## Usage

Each playbook includes:
- Attack narrative
- Technical commands
- Detection opportunities
- Response recommendations
- MITRE ATT&CK mapping

