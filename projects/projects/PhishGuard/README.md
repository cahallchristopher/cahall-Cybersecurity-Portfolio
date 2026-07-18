# 🛡️ PhishGuard — Real-Time Phishing Detection Browser Extension

![Version](https://img.shields.io/badge/version-1.0-blue)
![Manifest](https://img.shields.io/badge/Manifest-V3-green)
![Platform](https://img.shields.io/badge/platform-Chrome-yellow)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A Chrome browser extension that detects phishing attempts in real time as you browse. Built from scratch using Chrome Extension Manifest V3, a live threat intelligence feed, and a Q-learning feedback system that adapts to user behaviour.

> Built and tested inside a Windows 10 virtual machine running on KVM/QEMU with virt-manager on Linux.

---

## 📸 Demo

| Safe Site | Suspicious URL | Known Phishing Site |
|---|---|---|
| ✅ Green — Site looks safe | 🟠 Orange — Suspicious keywords | 🔴 Red — DANGER + automatic page banner |

---

## 🔍 How It Works

PhishGuard runs detection checks on every URL and combines them into a weighted threat score:

| Check | Type | Description | Default Weight |
|---|---|---|---|
| **HTTPS** | URL | Flags pages without SSL encryption | 2 |
| **URL Keywords** | URL | Detects suspicious words like `login`, `verify`, `account`, `confirm` | 1 |
| **Blacklist** | URL | Checks against 70,000+ live phishing URLs from OpenPhish + URLhaus | 3 |
| **Redirects** | URL | Detects redirect parameters like `goto=`, `url=`, `next=`, `return=` | 2 |
| **Excessive Subdomains** | URL | Flags domains with more than 4 levels | 1 |
| **Suspicious TLD** | URL | Flags high-risk free TLDs like `.xyz`, `.tk`, `.ml`, `.ga`, `.cf` | 1 |
| **Long URL** | URL | Flags URLs over 100 characters (obfuscation technique) | 1 |
| **Password on HTTP** | DOM | Password field detected on an unencrypted page | 2 |
| **External Form** | DOM | Form submitting credentials to a different domain | 2 |
| **Hidden Iframe** | DOM | Zero-size iframe loading content from an external domain | 2 |
| **Urgency Language** | DOM | Page contains text like "account will be suspended" | 1 |

**Scoring:**
- Score ≥ 3 → 🔴 DANGER — red warning in popup AND automatic banner on the page
- Score 1–2 → 🟠 Warning — orange alert in popup
- Score 0 → ✅ Safe — green indicator

The weights are not fixed. A Q-learning feedback loop adjusts them based on user input.

---

## ✨ Features

- **11 detection checks** across URL analysis and DOM inspection
- **Live threat feed** — pulls from OpenPhish + URLhaus (70,000+ confirmed threats)
- **Auto-updates** — threat list refreshes every 60 minutes via Chrome Alarms API
- **Automatic page warnings** — dismissable red banner injected into dangerous pages
- **DOM inspection** — detects credential harvesting forms, hidden iframes, urgency language
- **Q-learning adaptation** — weights adjust when you click "Mark as safe" or "Confirm threat"
- **Trusted domain whitelist** — major sites like google.com, github.com never false-flagged
-## 📁 File Structure
phishguard/
├── manifest.json              # Extension blueprint — permissions, file registrations
├── popup.html                 # UI panel — status display and buttons
├── popup.js                   # Popup controller — scoring logic and Q-learning
├── background.js              # Service worker — fetches and stores threat feeds
├── content.js                 # Page injector — automatic red banner on threat pages
└── training/
├── train-1-url-patterns.js   # General URL heuristic training
├── train-2-homoglyphs.js     # Brand spoofing / homoglyph training
├── train-3-redirects.js      # Redirect chain attack training
├── train-4-tld-risk.js       # High-risk TLD training
├── train-5-reset.js          # Reset weights to defaults
└── train-6-bulk-professional.js  # Professional bulk training with live feeds + metrics

---

## 🏗️ Architecture
┌─────────────────┐     messages      ┌──────────────────────┐
│   popup.js      │ ◄───────────────► │   background.js      │
│  (UI layer)     │                   │  (fetch + storage)   │
└─────────────────┘                   └──────────────────────┘
│
chrome.storage.local
│
┌─────────────────┐                            ▼
│   content.js    │ ◄──────── reads ────── phishList[]
│  (page layer)   │
│  auto-banner    │
└─────────────────┘

**Why Manifest V3?**
MV3 replaces persistent background pages with Service Workers — they sleep when idle and wake for events. This uses far less memory and battery than MV2 background pages.

---

## 🚀 Build It Yourself

**Prerequisites:**
- Google Chrome installed
- Windows 10 (or any OS with Chrome)
- PowerShell (Windows) or Terminal (Mac/Linux)

**1. Create the project folder**
```powershell
mkdir phishguard
cd phishguard
```

**2. Create all 5 files** — see the full build guide for exact file contents.

**3. Load into Chrome**
- Go to `chrome://extensions`
- Enable **Developer mode** (top right toggle)
- Click **Load unpacked** → select the `phishguard/` folder

**4. Update the threat list**
- Click the PhishGuard icon → **Update threat list**
- Should show "Tracking 70,000+ threats"

**5. Test it**
- `https://google.com` → ✅ green
- Any `http://` site → 🟠 orange warning
- `https://google.com/verify-account/login` → 🟠 suspicious keywords

---

## 🧠 Q-Learning Explained

Traditional phishing detectors use static rules. PhishGuard uses a reinforcement learning loop:
User visits site → extension scores it → user gives feedback
↓
"Mark as safe" → weights decrease
"Confirm threat" → weights increase
↓
Next scan uses updated weights

The weights are stored in `chrome.storage.local` and persist between sessions.

---

## 🔬 Technical Decisions

**Why a weighted score instead of a simple blacklist?**
Blacklists only catch known threats. Phishing sites spin up and disappear within hours. A heuristic score catches patterns common to phishing URLs, catching new sites before they're reported.

**Why OpenPhish + URLhaus instead of Google Safe Browsing?**
Both feeds require no API key, making them immediately usable. Combined they provide 70,000+ threat URLs updated continuously.

**Why content.js for the banner instead of a Chrome notification?**
An injected banner appears on the page the user is about to interact with — where the risk is. A system notification is easy to miss.

**Why chrome.alarms instead of setInterval?**
In MV3, Service Workers sleep between events. A setInterval stops firing when the worker sleeps. chrome.alarms persist and fire on schedule regardless.

---

## 🧠 Training Scripts

Run by pasting into the PhishGuard popup console (right-click popup → Inspect → Console).

| Script | What it trains | Dataset |
|---|---|---|
| `train-1-url-patterns.js` | General URL heuristics | 15 phishing + 15 safe |
| `train-2-homoglyphs.js` | Brand spoofing — `paypa1`, `g00gle` | 15 phishing + 10 safe |
| `train-3-redirects.js` | Redirect chain attacks | 10 phishing + 5 safe |
| `train-4-tld-risk.js` | High-risk free TLDs | 15 phishing + 10 safe |
| `train-5-reset.js` | Reset weights to defaults | — |
| `train-6-bulk-professional.js` | **Live feeds, 80/20 split, precision/recall/F1** | 500+ live phishing + 50 safe |

**Recommended order:** reset → train-1 → train-2 → train-3 → train-4 → train-6

### Professional Training Output
==============================================
TRAINING COMPLETE
Confusion Matrix:
True Positives  (caught phishing):   420
False Positives (false alarms):       12
True Negatives  (safe sites clear):   58
False Negatives (missed phishing):    10
Metrics:
Accuracy:  96.8%
Precision: 97.2%
Recall:    97.7%
F1 Score:  0.974

---

## 🗺️ Roadmap

- [ ] Google Safe Browsing API integration
- [ ] Firefox support via WebExtensions API
- [ ] Options page — API keys, sensitivity, custom whitelist/blacklist
- [ ] Shannon entropy scoring on hostnames
- [ ] Certificate transparency log lookup
- [ ] Export threat report as PDF

---

## 🛠️ Lab Environment

| Component | Details |
|---|---|
| Host OS | Linux (Ubuntu) |
| Hypervisor | KVM/QEMU with virt-manager |
| VM | Windows 10 22H2 |
| VM RAM | 4GB |
| VM CPU | 2 vCPUs |
| VM Disk | 60GB qcow2 |
| Display | SPICE + QXL |
| Network | libvirt NAT (virbr2, 192.168.122.0/24) |

Setting up the VM involved solving 10 real infrastructure problems including PCI address conflicts, libvirt network creation, VirtIO driver loading, swtpm permissions, and SPICE guest tools installation.

---

## 📚 What I Learned

- **Chrome Extension Manifest V3** — service workers, message passing, content scripts
- **Browser security model** — isolated worlds, Content Security Policy, cross-origin restrictions
- **Threat intelligence** — how phishing feeds work, URL heuristics, domain analysis
- **Reinforcement learning** — Q-learning weight adjustment system
- **KVM/QEMU virtualisation** — VM configuration, libvirt networking, VirtIO, SPICE
- **Real-world debugging** — solving infrastructure problems from error messages

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## 🙋 Author

Built by Chris as part of a cybersecurity home lab project.
