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
-
