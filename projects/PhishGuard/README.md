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

| Check | Description | Default Weight |
|---|---|---|
| **HTTPS** | Flags pages without SSL encryption | 2 |
| **URL Keywords** | Detects suspicious words like `login`, `verify`, `account`, `confirm` | 1 |
| **Blacklist** | Checks against 300+ live phishing URLs from OpenPhish | 3 |

**Scoring:**
- Score ≥ 3 → 🔴 DANGER — red warning shown in popup AND automatic red banner injected into the page
- Score 1–2 → 🟠 Warning — orange alert in popup
- Score 0 → ✅ Safe — green indicator

The weights are not fixed. A Q-learning feedback loop adjusts them based on user input — making PhishGuard more accurate the more you use it.

---

## ✨ Features

- **Real-time URL analysis** — checks every page you visit instantly
- **Live threat feed** — pulls from [OpenPhish](https://openphish.com) (300–500 confirmed phishing URLs, updated continuously)
- **Auto-updates** — threat list refreshes every 60 minutes via Chrome Alarms API
- **Automatic page warnings** — red banner injected directly into dangerous pages without any user action
- **Q-learning adaptation** — weights adjust when you click "Mark as safe" or "Confirm threat"
- **Weighted scoring** — catches novel phishing URLs not yet on any blacklist
- **Zero external dependencies** — pure JavaScript, no npm, no build step

---

## 📁 File Structure

```
phishguard/
├── manifest.json     # Extension blueprint — permissions, file registrations
├── popup.html        # UI panel — status display and buttons
├── popup.js          # Popup controller — scoring logic and Q-learning
├── background.js     # Service worker — fetches and stores OpenPhish feed
└── content.js        # Page injector — automatic red banner on threat pages
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
