# Detection Walkthrough — Healthcare Vendor Risk SOC Lab

This walkthrough demonstrates how vendor activity is detected and investigated.

---

## Step 1 — Baseline Activity

Windows generates normal browsing and DNS traffic.
This establishes expected behavior.

---

## Step 2 — Vendor Activity

Kali generates DNS queries consistent with vendor access.
Activity is logged but not immediately suspicious.

---

## Step 3 — Abnormal Behavior

Kali simulates:
- High-frequency DNS queries
- Requests to unusual or placeholder domains
- Probing behavior

---

## Step 4 — Detection Signals

Evidence sources include:
- dnsmasq DNS logs
- Zeek DNS logs and notices
- Snort alert output

---

## Step 5 — SOC Triage

Analyst actions:
- Confirm source system
- Correlate across logs
- Assess business justification
- Document findings
- Feed results into vendor risk assessment
