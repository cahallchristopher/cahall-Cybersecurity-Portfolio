# Automated Phishing Email Analysis Lab

**Author:** Christopher Cahall  
**Project:** Advanced SOC Analyst Training - Email Threat Detection  
**Status:** 🟢 Active Development  
**Difficulty:** ⭐⭐⭐ Intermediate  

---

## 🎯 Project Overview

A complete email security analysis pipeline that automatically detects, analyzes, and catalogs phishing threats. Built for hands-on SOC analyst training with production-ready tools and techniques.

### What This Lab Does
```
┌─────────────────────────────────────────────────────┐
│         Automated Phishing Analysis Pipeline         │
└─────────────────────────────────────────────────────┘

[Incoming Email] 
      │
      ├──> Email Parser (Headers, Body, Attachments)
      │
      ├──> Threat Intelligence Lookup (VirusTotal, PhishTank)
      │
      ├──> Attachment Analysis
      │    ├─> Hash Analysis (MD5, SHA256)
      │    ├─> Static Analysis (strings, metadata)
      │    ├─> YARA Scanning (30+ custom rules)
      │    ├─> Macro Detection (oletools)
      │    └─> Sandbox Detonation (behavior analysis)
      │
      ├──> URL Analysis
      │    ├─> Domain Reputation
      │    ├─> Typosquatting Detection
      │    └─> Malicious Link Database
      │
      └──> Automated Report Generation
           ├─> Threat Score (0-100)
           ├─> IOC Extraction
           ├─> MITRE ATT&CK Mapping
           └─> Incident Response Recommendations
```

---

## 🏗️ Architecture

### Infrastructure
```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Kali Linux     │      │  Ubuntu Gateway  │      │   Windows 10     │
│   (Attacker)     │─────>│  (Email Server)  │─────>│   (Victim)       │
│                  │      │                  │      │                  │
│ • Phishing Kit   │      │ • Postfix SMTP   │      │ • Outlook        │
│ • Payload Gen    │      │ • Analysis Tools │      │ • LimaCharlie    │
│ • Campaign Mgmt  │      │ • YARA Scanner   │      │ • Sysmon         │
└──────────────────┘      │ • ML Detector    │      └──────────────────┘
                          └──────────────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  Analysis DB     │
                          │  & Reporting     │
                          └──────────────────┘
```

### Network

- **Internal Network:** 10.50.50.0/24 (SOARLab)
- **Kali (Attacker):** 10.50.50.100
- **Ubuntu (Email Server):** 10.50.50.1
- **Windows (Victim):** 10.50.50.15X

---

## 🎓 Skills You'll Learn

### Email Forensics
- ✅ SMTP header analysis
- ✅ SPF/DKIM/DMARC validation
- ✅ Email routing trace
- ✅ Sender authentication

### Malware Analysis
- ✅ Static analysis (strings, metadata)
- ✅ Dynamic analysis (sandbox execution)
- ✅ Macro extraction and deobfuscation
- ✅ IOC extraction

### Detection Engineering
- ✅ YARA rule development (30+ rules)
- ✅ Behavioral detection logic
- ✅ False positive tuning
- ✅ Signature creation

### Threat Intelligence
- ✅ VirusTotal API integration
- ✅ PhishTank database queries
- ✅ URLhaus reputation checking
- ✅ MITRE ATT&CK mapping

---

## 📋 Lab Exercises

### Exercise 1: Macro-Based Phishing Detection
**Scenario:** Invoice phishing with malicious Excel macro  
**Objective:** Detect and analyze VBA macro payload  
**Skills:** Oletools, YARA rules, macro deobfuscation  
**MITRE:** T1566.001 (Spearphishing Attachment)

### Exercise 2: Credential Harvesting Detection
**Scenario:** Fake Microsoft login page  
**Objective:** Identify phishing URL and extract IOCs  
**Skills:** URL analysis, domain reputation, typosquatting  
**MITRE:** T1566.002 (Spearphishing Link)

### Exercise 3: PDF Exploit Analysis
**Scenario:** Malicious PDF with embedded JavaScript  
**Objective:** Extract and analyze exploit code  
**Skills:** PDF parsing, JavaScript deobfuscation  
**MITRE:** T1203 (Exploitation for Client Execution)

### Exercise 4: HTML Smuggling Detection
**Scenario:** Email with embedded Base64 executable  
**Objective:** Decode and analyze hidden payload  
**Skills:** Base64 decoding, HTML parsing, steganography  
**MITRE:** T1027 (Obfuscated Files or Information)

### Exercise 5: Business Email Compromise (BEC)
**Scenario:** CEO impersonation (no malware)  
**Objective:** Detect social engineering without technical indicators  
**Skills:** Content analysis, sender verification, behavioral detection  
**MITRE:** T1598.003 (Spearphishing for Information)

---

## 🚀 Quick Start

### Prerequisites

- Ubuntu Server 22.04 LTS (running)
- Kali Linux 2024.1
- Windows 10 with LimaCharlie EDR
- 8GB RAM minimum
- 50GB disk space
