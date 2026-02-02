# Phishing Analysis Lab

**Purpose:** Automated email threat detection and analysis pipeline.

---

## Quick Start
```bash
# Install
./setup.sh

# Analyze email
python3 tools/analyzers/phish-analyzer.py test-samples/malicious/invoice_phishing.eml
```

---

## Features

- Email metadata extraction
- SPF/DKIM/DMARC validation
- Attachment analysis (hash, type, macros)
- URL extraction and reputation checking
- YARA scanning
- Automated threat scoring
- IOC extraction
- Report generation (HTML, JSON, PDF)

---

## Components

### Tools
- `phish-analyzer.py` - Main analysis engine
- `attachment-analyzer.py` - Deep file analysis
- `url-analyzer.py` - URL reputation checker
- `header-analyzer.py` - Email header parser

### YARA Rules
30+ custom rules for:
- Malicious macros
- Encoded PowerShell
- PDF exploits
- Suspicious keywords

### Test Samples
- Macro-based phishing
- Credential harvesting
- PDF exploits
- HTML smuggling
- CEO fraud (BEC)

---

## Documentation

See: `docs/` for complete guides

