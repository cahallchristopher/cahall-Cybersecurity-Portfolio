# Interview Talking Points — Healthcare Vendor Risk SOC Lab

This document translates the lab into clear, interview-ready
talking points suitable for SOC, security analyst, or
entry-level detection roles.

The focus is on explaining *why* decisions were made,
not just *what* was built.

---

## High-Level Project Summary

“I built a SOC-focused lab to model healthcare vendor risk,
with an emphasis on logging, detection, and audit readiness
rather than exploitation.”

The lab simulates how third-party vendors can introduce risk
when activity is trusted but not sufficiently monitored.

---

## Why I Built This Lab

Healthcare breaches often involve vendors rather than attackers
directly compromising hospital systems.

I wanted to practice:
- Detecting vendor risk
- Designing audit-ready controls
- Explaining findings clearly
- Mapping technical behavior to compliance requirements

---

## Key Skills Demonstrated

This lab demonstrates experience with:

- Threat modeling
- Network segmentation
- DNS-based detection
- Logging and audit strategy
- SOC alert design
- Vendor risk assessment
- Compliance-aligned thinking

---

## Example Interview Questions and Answers

### “Tell me about a security project you worked on.”

“I designed a healthcare-focused SOC lab that models vendor risk.
Instead of simulating malware, I focused on visibility gaps,
logging, and alerting—because that’s where many real incidents start.”

---

### “How do you approach detection?”

“I start with high-signal data sources like DNS.
I define what normal looks like, then alert on deviations that
are explainable and actionable rather than noisy.”

---

### “How do you think about third-party risk?”

“I treat vendors as semi-trusted.
Access is limited, behavior is logged, and unexplained activity
feeds directly into risk assessments rather than being ignored.”

---

### “How does compliance influence your security work?”

“Compliance requirements like HIPAA shape what must be logged
and retained. Detection without evidence doesn’t support audits
or investigations, so logging strategy is foundational.”

---

## What I Would Improve Next

Given more time, I would:
- Integrate alert output into a SIEM
- Automate vendor behavior baselining
- Expand retention and correlation logic
- Add tabletop incident response scenarios

---

## How This Lab Applies to a SOC Role

This lab mirrors real SOC responsibilities:
- Monitoring third-party activity
- Investigating anomalies
- Supporting audits
- Communicating risk clearly
- Making evidence-based decisions

---

## Summary

This project reflects how I think about security:
- Visibility before prevention
- Evidence over assumptions
- Detection that supports governance
- Security that can be explained
