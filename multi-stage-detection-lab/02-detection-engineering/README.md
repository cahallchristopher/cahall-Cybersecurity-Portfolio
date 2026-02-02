# Detection Engineering

**Purpose:** Detection rules, Sysmon configurations, and EDR policies for identifying attacks.

---

## Overview

Production-ready detection rules covering all 14 MITRE ATT&CK tactics.

---

## Detection Rules

### LimaCharlie D&R Rules

**Location:** `detection-rules/limacharlie/`

30+ YAML detection rules including:
- PowerShell encoded command execution
- LSASS memory access (credential dumping)
- Registry persistence
- Shadow copy deletion (ransomware precursor)
- C2 beaconing patterns
- Lateral movement (RDP)

**Deployment:**
```bash
# Via LimaCharlie Web UI
1. Login to https://app.limacharlie.io
2. Automation → D&R Rules
3. Import rules from detection-rules/limacharlie/
```

### Sysmon Configuration

**Location:** `detection-rules/sysmon/`

Enhanced Windows event logging:
- Event ID 1: Process creation
- Event ID 10: LSASS access monitoring
- Event ID 13: Registry modifications
- Event ID 3: Network connections

---

## MITRE ATT&CK Coverage

| Tactic | Techniques Covered | Rules |
|--------|-------------------|-------|
| Initial Access | T1566.001 | 2 |
| Execution | T1059.001 | 3 |
| Persistence | T1547.001, T1053.005 | 4 |
| Privilege Escalation | T1134.001 | 2 |
| Defense Evasion | T1070.001, T1070.004 | 3 |
| Credential Access | T1003.001 | 4 |
| Discovery | T1087.002 | 3 |
| Lateral Movement | T1021.001 | 2 |
| Collection | T1005 | 3 |
| C&C | T1071.001 | 2 |
| Exfiltration | T1041 | 1 |
| Impact | T1486, T1490 | 4 |

**Total:** 30+ rules across 12 tactics

---

## Testing

See: [Detection Testing Results](../results/detection-testing-results.md)

- Detection Rate: 100% (4/4 tested)
- False Positive Rate: 0%
- Average Response Time: <1 second

