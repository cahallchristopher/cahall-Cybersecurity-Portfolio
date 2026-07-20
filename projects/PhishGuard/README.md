# 🛡️ PhishGuard — Real-Time Phishing Detection Browser Extension

![Version](https://img.shields.io/badge/version-1.0-blue)
![Manifest](https://img.shields.io/badge/Manifest-V3-green)
![Platform](https://img.shields.io/badge/platform-Chrome-yellow)
![Threats](https://img.shields.io/badge/threats-70%2C000%2B-red)
![F1 Score](https://img.shields.io/badge/F1%20Score-97%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> **A working Chrome extension that detects phishing sites in real time — built from scratch, no frameworks, no shortcuts.**

| What it does | How good is it | How it learns |
|---|---|---|
| Scans every URL you visit | 70,000+ live threat database | Q-learning adapts weights from your feedback |
| Injects red warning banner automatically | 97% F1 score after training | Retrains on live phishing feeds |
| Inspects page DOM for credential harvesting | 11 independent detection checks | Precision/recall metrics tracked per epoch |

---

## ⚡ See It In Action

**Visiting a known phishing site:**
```
🔴 PhishGuard Warning: Known phishing site, No HTTPS — Click to dismiss
```

**Visiting Google:**
```
✅ Site looks safe — Tracking 70,965 threats
```

**After professional bulk training:**
```
Epoch 3/3 — Train: 96% | F1: 0.974 | Precision: 0.972 | Recall: 0.977
True Positives: 420 | False Positives: 12 | F1 Score: 0.974
```

---

## 🔍 11 Detection Checks — Two Layers

### URL Layer (runs before the page loads)
| Check | What it catches |
|---|---|
| **No HTTPS** | Unencrypted pages — credentials sent in plaintext |
| **Suspicious keywords** | `login`, `verify`, `account`, `confirm` in the URL path |
| **Live blacklist** | 70,000+ confirmed phishing URLs from OpenPhish + URLhaus |
| **Redirect parameters** | `?goto=`, `?url=`, `?redirect=` — destination hiding |
| **Excessive subdomains** | `login.secure.verify.paypal.evil.com` — depth > 4 |
| **High-risk TLDs** | `.xyz`, `.tk`, `.ml`, `.ga`, `.cf` — free domains abused by phishers |
| **Long URLs** | > 100 characters — obfuscation technique |

### DOM Layer (runs after the page loads)
| Check | What it catches |
|---|---|
| **External form action** | Form submits credentials to a different domain |
| **Password field on HTTP** | Credentials sent unencrypted |
| **Hidden iframes** | Zero-size cross-origin iframes — clickjacking signature |
| **Urgency language** | "Your account will be suspended", "verify immediately" |

---

## 🧠 Q-Learning Adaptive Scoring

Each check has a weight. Weights adjust based on your feedback:

```
"Mark as safe"    → weights decrease → fewer false positives
"Confirm threat"  → weights increase → more aggressive detection
```

Weights persist across sessions in `chrome.storage.local`. The more you use it, the more accurate it gets for your browsing patterns.

---

## 🔬 Professional Training Pipeline

The `training/` folder contains 6 scripts that train the model using security engineer practices:

```
train-5-reset.js              → reset weights to defaults
train-1-url-patterns.js       → general URL heuristics (15 phishing + 15 safe)
train-2-homoglyphs.js         → brand spoofing: paypa1, g00gle, micros0ft
train-3-redirects.js          → redirect chain attacks
train-4-tld-risk.js           → high-risk TLD scoring
train-6-bulk-professional.js  → live feeds + 80/20 split + precision/recall/F1
```

`train-6-bulk-professional.js` fetches 500+ live phishing URLs, splits 80/20 train/test, runs 3 epochs, and outputs a full confusion matrix — the same evaluation approach used in production security tools.

---

## 🏗️ Architecture

```
┌─────────────────┐     messages      ┌──────────────────────┐
│   popup.js      │ ◄───────────────► │   background.js      │
│  (UI + scoring) │                   │  (fetch + storage)   │
└─────────────────┘                   └──────────────────────┘
                                               │
                                    chrome.storage.local
                                    (70,000+ URL blacklist)
                                               │
┌─────────────────┐                            ▼
│   content.js    │ ◄──────── reads ────── phishList[]
│  (DOM inspector)│
│  auto-banner    │
└─────────────────┘
```

**Why Manifest V3?** Service Workers sleep between events — far less memory than MV2 persistent background pages.

**Why weighted scoring over a blacklist?** Blacklists only catch known threats. Phishing sites spin up and disappear within hours. Heuristic scoring catches novel sites by pattern before they're reported.

**Why chrome.alarms over setInterval?** Service Workers sleep. `setInterval` stops firing. `chrome.alarms` persist and fire on schedule regardless of worker state.

---

## 🚀 Install & Run in 60 Seconds

```bash
# 1. Clone or download the phishguard/ folder
# 2. Open Chrome → chrome://extensions
# 3. Enable Developer mode (top right)
# 4. Click Load unpacked → select phishguard/
# 5. Click the shield icon → Update threat list
```

Test it:
- `https://google.com` → ✅ green
- `http://anything` → 🟠 No HTTPS warning  
- `https://example.com/verify-account/login` → 🟠 Suspicious keywords
- Any URL from the OpenPhish feed → 🔴 DANGER + automatic page banner

---

## 🛠️ Lab Environment

Built and tested in a cybersecurity home lab — not just on a local machine:

| Component | Details |
|---|---|
| Host OS | Linux (Ubuntu) |
| Hypervisor | KVM/QEMU with virt-manager |
| Guest OS | Windows 10 22H2 |
| VM RAM | 4GB / 16GB host |
| VM Storage | 60GB qcow2 |
| Display | SPICE + QXL paravirtualised |
| Network | libvirt NAT — virbr2, 192.168.122.0/24 |
| Drivers | VirtIO storage + network, SPICE guest tools |

Setting up the VM involved solving 10 real infrastructure problems: PCI address conflicts, libvirt network creation from scratch, VirtIO driver loading during Windows install, swtpm TPM permissions, and SPICE clipboard integration. Full troubleshooting notes in the repo.

---

## 📚 Skills Demonstrated

`Chrome Extension Manifest V3` `Service Workers` `Content Scripts` `Message Passing` `chrome.storage` `chrome.alarms` `Threat Intelligence APIs` `URL Heuristics` `DOM Inspection` `Q-Learning` `Precision/Recall/F1` `Shannon Entropy` `KVM/QEMU` `libvirt` `VirtIO` `SPICE Protocol` `Bash Scripting` `GitHub API`

---

## 📄 License

MIT — free to use, modify, and distribute.

---

*Built by Chris Cahall as part of a cybersecurity home lab project.*  
*Questions or feedback: [github.com/cahallchristopher](https://github.com/cahallchristopher)*
