# Lab Overview — Healthcare Vendor Risk SOC Lab

This lab models a common healthcare security problem:
third-party vendor access that exists, but is not sufficiently monitored.

The goal is not to simulate an attack.
The goal is to practice detection, logging, auditing, and explanation.

This is how many real-world healthcare incidents begin.

---

## Problem Statement

Healthcare organizations rely heavily on third-party vendors:
billing companies, support providers, analytics platforms, and service contractors.

These vendors often require:
- Network access
- DNS resolution
- Limited system connectivity

Over time, this access becomes “normal” and receives less scrutiny.

When logging and alerting are weak, abnormal behavior may go unnoticed
until sensitive data is exposed.

This lab focuses on identifying and closing that visibility gap.

---

## Lab Objectives

By completing this lab, the analyst should be able to:

- Describe how vendor access introduces risk
- Identify what activity should be logged
- Explain why DNS is a high-signal data source
- Map technical controls to HIPAA safeguards
- Describe how a SOC would detect and respond to issues
- Explain the lab clearly to a non-technical audience

---

## Environment Overview

The lab consists of three systems connected through a controlled gateway.

### 1. Ubuntu Server (Gateway)

Acts as the central control point.

Responsibilities:
- Routes all internal traffic
- Provides DNS via dnsmasq
- Logs DNS queries for audit purposes
- Enforces basic firewall rules

This system represents a hardened healthcare network boundary.

---

### 2. Windows System (Internal Asset)

Represents systems that handle or access sensitive data.

Characteristics:
- Normal business usage
- Trusted internal role
- No direct internet access outside the gateway

This mirrors real-world healthcare workstation behavior.

---

### 3. Vendor System (Third-Party Access)

Represents a billing or service vendor.

Characteristics:
- Limited access
- No direct trust relationship
- Activity must be monitored
- Behavior should be explainable

This system is not malicious.
It is simply external.

That distinction is important.

---

## Network Design Philosophy

All systems communicate through the gateway.

There are no shortcuts.
There is no direct outbound access.

This design ensures:
- Centralized logging
- Clear attribution
- Enforceable policy
- Auditable behavior

If the gateway cannot explain activity,
the environment is considered insecure.

---

## Detection Focus

This lab focuses on **behavioral signals**, not exploits.

Key questions:
- What domains is the vendor resolving?
- How often are requests occurring?
- Are destinations expected and documented?
- Would this behavior pass an audit?

DNS is used because:
- It is difficult to hide completely
- It reveals intent
- It is often under-monitored

---

## Logging and Audit Perspective

All vendor-related activity should be:

- Logged
- Timestamped
- Attributable to a system
- Retained for review

These logs support:
- Incident response
- Compliance audits
- Root cause analysis

Lack of logs is treated as a finding.

---

## HIPAA Alignment (High Level)

This lab aligns with HIPAA safeguards by:

- Limiting access to the minimum necessary
- Monitoring access to sensitive systems
- Maintaining audit controls
- Supporting investigation and accountability

Detailed mappings are covered in:
docs/03-hipaa-mapping.md

---

## How a SOC Would Use This Lab

In a SOC environment, this lab supports:

- Baseline creation
- Alert tuning
- Vendor risk discussions
- Tabletop incident response
- Compliance preparation

The lab is designed to be explainable,
not just executable.

---

## What This Lab Intentionally Avoids

This lab does not include:
- Exploits
- Payloads
- Privilege escalation
- “Red team” activity

This lab is about **defensive clarity


