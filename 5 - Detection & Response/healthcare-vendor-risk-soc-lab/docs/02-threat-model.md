# Threat Model — Healthcare Vendor Risk SOC Lab

This document outlines the threat model for the Healthcare Vendor Risk SOC Lab.
It focuses on realistic risks introduced by third-party vendors in healthcare
environments, not attacker exploitation techniques.

The intent is to identify where visibility is lost and how detection can fail.

---

## Assets in Scope

The following assets are considered sensitive or high value:

- Patient data accessed by internal systems
- Network infrastructure supporting healthcare operations
- DNS and network logs used for auditing and investigations
- Trust relationships between the organization and vendors

Loss of visibility into these assets is treated as a security failure.

---

## Trust Boundaries

This lab defines clear trust boundaries.

### Trusted
- Internal Windows systems
- Internal users performing normal business functions
- The Ubuntu gateway enforcing policy and logging

### Semi-Trusted
- Third-party vendor systems
- Vendor network traffic
- Vendor DNS activity

Vendor systems are not assumed to be malicious,
but they are not implicitly trusted.

---

## Threat Actors (Non-Exhaustive)

This lab considers the following realistic threat actors:

- Misconfigured vendor systems
- Compromised vendor endpoints
- Over-privileged vendor access
- Automated vendor software behaving unexpectedly
- Insider misuse at a vendor organization

No advanced attacker capabilities are required for impact.

---

## Threat Scenarios

### Scenario 1 — Excessive Vendor DNS Activity

A vendor system generates DNS requests far outside its expected scope.

Risks:
- Data exfiltration channels
- Unauthorized external communications
- Undocumented dependencies

Detection depends entirely on DNS visibility.

---

### Scenario 2 — Vendor Access Outside Business Context

Vendor activity occurs:
- Outside normal business hours
- From unexpected domains
- At unusual frequency

Without logging, this behavior blends into background noise.

---

### Scenario 3 — Logging Gaps

DNS or network logs are:
- Disabled
- Incomplete
- Not retained long enough

This prevents:
- Incident investigation
- Compliance validation
- Root cause analysis

Lack of logs is treated as a critical risk.

---

## Abuse vs. Failure

This lab distinguishes between:
- Malicious abuse
- Operational failure

Most healthcare incidents originate from failure:
misconfiguration, poor monitoring, or incorrect assumptions.

Detection strategies must account for both.

---

## Detection Opportunities

High-signal detection points include:

- DNS query patterns
- Domain reputation anomalies
- Frequency and timing analysis
- Deviations from documented vendor behavior

These signals are available without deep packet inspection.

---

## Impact Analysis

Potential impacts include:

- Exposure of protected health information (PHI)
- Regulatory penalties
- Loss of trust
- Inability to demonstrate compliance
- Delayed incident response

The technical failure becomes an organizational failure.

---

## Risk Treatment Strategy

This lab emphasizes:

- Visibility before prevention
- Logging before blocking
- Explainability over complexity
- Evidence over assumptions

Controls that cannot be explained are considered weak.

---

## Summary

Vendor risk is not hypothetical.
It is operational.

This threat model supports detection, audit readiness,
and clear communication between security, IT, and compliance teams


