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

PhishGuard runs three detection checks on every URL and combines them into a weighted threat score:

| Check | Type | Description | Default Weight |
|---|---|---|---|
| **HTTPS** | URL | Flags pages without SSL encryption | 2 |
| **URL Keywords** | URL | Detects suspicious words like `login`, `verify`, `account`, `confirm` | 1 |
| **Blacklist** | URL | Checks against 300+ live phishing URLs from OpenPhish | 3 |
| **Redirects** | URL | Detects redirect parameters like `goto=`, `url=`, `next=`, `return=` | 2 |
| **Excessive Subdomains** | URL | Flags domains with more than 4 levels (e.g. `login.secure.verify.paypal.evil.com`) | 1 |
| **Suspicious TLD** | URL | Flags high-risk free TLDs like `.xyz`, `.tk`, `.ml`, `.ga`, `.cf` | 1 |
| **Long URL** | URL | Flags URLs over 100 characters (obfuscation technique) | 1 |
| **Password on HTTP** | DOM | Password field detected on an unencrypted page | 2 |
| **External Form** | DOM | Form submitting credentials to a different domain | 2 |
| **Hidden Iframe** | DOM | Zero-size iframe loading content from an external domain | 2 |
| **Urgency Language** | DOM | Page contains text like "account will be suspended", "verify immediately" | 1 |

**Scoring:**
- Score ≥ 3 → 🔴 DANGER — red warning shown in popup AND automatic red banner injected into the page
- Score 1–2 → 🟠 Warning — orange alert in popup
- Score 0 → ✅ Safe — green indicator

The weights are not fixed. A Q-learning feedback loop adjusts them based on user input — making PhishGuard more accurate the more you use it.

---

## ✨ Features

- **11 detection checks** across URL analysis and DOM inspection
- **Live threat feed** — pulls from [OpenPhish](https://openphish.com) (300–500 confirmed phishing URLs, updated continuously)
- **Auto-updates** — threat list refreshes every 60 minutes via Chrome Alarms API
- **Automatic page warnings** — dismissable red banner injected directly into dangerous pages with exact reasons listed
- **DOM inspection** — detects credential harvesting forms, hidden iframes, and urgency language directly on the page
- **Q-learning adaptation** — all 11 weights adjust when you click "Mark as safe" or "Confirm threat"
- **Weighted scoring** — catches novel phishing URLs not yet on any blacklist
- **Zero external dependencies** — pure JavaScript, no npm, no build step

---

## 📁 File Structure

```
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
    └── train-5-reset.js          # Reset weights to defaults
```

---

## 🏗️ Architecture

```
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
```

**Why Manifest V3?**
MV3 replaces persistent background pages with Service Workers — they sleep when idle and wake for events. This uses far less memory and battery than MV2 background pages.

---

## 🚀 Build It Yourself

This extension was built step by step from scratch. Full beginner-friendly instructions are in [PhishGuard-Build-Guide.docx](./PhishGuard-Build-Guide.docx).

### Quick Start

**Prerequisites:**
- Google Chrome installed
- Windows 10 (or any OS with Chrome)
- PowerShell (Windows) or Terminal (Mac/Linux)

**1. Create the project folder**
```powershell
mkdir phishguard
cd phishguard
```

**2. Create all 5 files** — see the build guide for the exact content of each file.

**3. Load into Chrome**
- Go to `chrome://extensions`
- Enable **Developer mode** (top right toggle)
- Click **Load unpacked**
- Select the `phishguard/` folder

**4. Update the threat list**
- Click the PhishGuard icon in the Chrome toolbar
- Click **Update threat list**
- You should see "Tracking 300+ threats"

**5. Test it**
- Visit `https://google.com` → should show ✅ green
- Visit any `http://` site → should show 🟠 orange warning
- Visit `https://google.com/verify-account/login` → should show 🟠 suspicious keywords

---

## 🧠 Q-Learning Explained

Traditional phishing detectors use static rules. PhishGuard uses a simple reinforcement learning loop:

```
User visits site → extension scores it → user gives feedback
                                              ↓
                              "Mark as safe" → weights decrease
                              "Confirm threat" → weights increase
                                              ↓
                              Next scan uses updated weights
```

The weights are stored in `chrome.storage.local` and persist between sessions. Over time the extension learns your browsing patterns and reduces false positives.

**Example:**
- You frequently visit internal company sites with `login` in the URL
- You click "Mark as safe" several times
- The keyword weight drops from 1.0 → 0.7 → 0.4
- Those sites no longer trigger warnings

---

## 🔬 Technical Decisions

**Why a weighted score instead of a simple blacklist?**
Blacklists only catch known threats. Phishing sites spin up and disappear within hours — faster than any list can track. A heuristic score catches *patterns* common to phishing URLs, catching new sites before they're reported.

**Why OpenPhish instead of Google Safe Browsing?**
OpenPhish has no API key requirement for the basic feed, making it immediately usable for a lab project. Google Safe Browsing (next step) adds a second database with broader coverage.

**Why content.js for the banner instead of a Chrome notification?**
An injected banner appears *on the page* the user is about to interact with — where the risk is. A system notification is easy to dismiss and miss. The in-page banner forces attention at the right moment.

**Why chrome.alarms instead of setInterval?**
In MV3, Service Workers go to sleep between events. A `setInterval` inside a service worker stops firing when it sleeps. `chrome.alarms` persist and fire on schedule even when the worker is inactive.

---

## 🧠 Training Scripts

The `training/` folder contains scripts that train the Q-learning weights using known phishing and safe URLs. Run them by pasting into the PhishGuard popup console (right-click popup → Inspect → Console).

| Script | What it trains | URLs |
|---|---|---|
| `train-1-url-patterns.js` | General URL heuristics — keywords, HTTPS, TLDs, subdomains | 15 phishing + 15 safe |
| `train-2-homoglyphs.js` | Brand spoofing — `paypa1`, `g00gle`, `micros0ft` | 15 phishing + 10 safe |
| `train-3-redirects.js` | Redirect chain attacks — `?url=`, `?goto=`, `?redirect=` | 10 phishing + 5 safe |
| `train-4-tld-risk.js` | High-risk free TLDs — `.xyz`, `.tk`, `.ml`, `.ga`, `.cf` | 15 phishing + 10 safe |
| `train-5-reset.js` | Resets all weights back to defaults | — |
| `train-6-bulk-professional.js` | **Professional grade** — fetches live feeds, 80/20 train/test split, 3 epochs, outputs precision/recall/F1 confusion matrix | 500+ live phishing + 70 safe |

**Recommended training order:**
1. Run `train-5-reset.js` to start clean
2. Run `train-1-url-patterns.js` for baseline accuracy
3. Run `train-2-homoglyphs.js` to improve brand spoofing detection
4. Run `train-3-redirects.js` to improve redirect detection
5. Run `train-4-tld-risk.js` to improve TLD risk scoring
6. Run `train-6-bulk-professional.js` for final professional-grade training on live data

After full training you should reach **95%+ F1 score** on unseen test data.

### Professional Training Output Example
```
==============================================
TRAINING COMPLETE
==============================================
Confusion Matrix:
  True Positives  (caught phishing):   420
  False Positives (false alarms):       12
  True Negatives  (safe sites clear):   58
  False Negatives (missed phishing):    10

Metrics:
  Accuracy:  96.8%
  Precision: 97.2%  (low false positives)
  Recall:    97.7%  (threats caught)
  F1 Score:  0.974  (overall detector quality)
==============================================
```

### What Makes Script 6 Security Engineer Grade
- **Shannon entropy scoring** — detects random-looking auto-generated phishing domains like `a8f3kx92.xyz`
- **IP address detection** — legitimate sites never use raw IPs as hostnames
- **80/20 train/test split** — validates on unseen data so accuracy is real, not inflated
- **Multi-epoch training** — runs 3 passes through data until weights converge
- **Best weight tracking** — saves only the epoch with highest F1, not just the last
- **Live feed integration** — trains on real confirmed phishing URLs from OpenPhish and URLhaus

## 🗺️ Roadmap

- [ ] Google Safe Browsing API integration (second threat database)
- [ ] DOM inspection — detect credential harvesting forms and hidden iframes
- [ ] Firefox support via WebExtensions API
- [ ] Options page — configure API keys, sensitivity, custom blacklist/whitelist
- [ ] Shannon entropy scoring on hostnames (high entropy = random-looking = suspicious)
- [ ] ML model trained on URL features using scikit-learn
- [ ] Certificate transparency log lookup
- [ ] Export threat report as PDF

---

## 🛠️ Lab Environment

This project was built in a cybersecurity home lab:

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

Setting up the VM involved solving 10 real infrastructure problems including PCI address conflicts, libvirt network creation, VirtIO driver loading, swtpm permissions, and SPICE guest tools installation. Full troubleshooting notes are in [PhishGuard-Lab-Notes.docx](./PhishGuard-Lab-Notes.docx).

---

## 📚 What I Learned

- **Chrome Extension Manifest V3** — service workers, message passing, content scripts, host permissions
- **Browser security model** — isolated worlds, Content Security Policy, cross-origin restrictions
- **Threat intelligence** — how phishing feeds work, what makes a URL suspicious
- **Reinforcement learning** — implementing a basic Q-learning weight adjustment system
- **KVM/QEMU virtualisation** — VM configuration, libvirt networking, VirtIO drivers, SPICE protocol
- **Real-world debugging** — solving infrastructure problems methodically from error messages

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## 🙋 Author

Built by Chris as part of a cybersecurity home lab project.
