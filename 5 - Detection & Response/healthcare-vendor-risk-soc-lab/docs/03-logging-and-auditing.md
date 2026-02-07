# Logging and Audit Strategy — Healthcare Vendor Risk SOC Lab

This document defines what activity is logged in the lab,
why those logs matter, and how they support security operations
and healthcare compliance.

In this lab, logging is treated as a primary security control.

---

## Logging Philosophy

In healthcare environments, the absence of logs is itself a finding.

This lab prioritizes:
- Centralized logging
- Clear attribution
- Sufficient retention
- Explainable evidence

If activity cannot be explained using logs,
the environment is considered insecure.

---

## Primary Log Source: DNS

DNS logging is the primary signal used in this lab.

DNS activity is logged at the Ubuntu gateway using dnsmasq.

Captured information includes:
- Timestamp
- Source system
- Queried domain
- Frequency of requests

DNS is valuable because it:
- Reveals intent
- Is difficult to fully hide
- Often exposes misconfigurations
- Is commonly under-monitored

Vendor DNS activity is reviewed with higher scrutiny.

---

## Supporting Context (Network Awareness)

While this lab does not rely on full packet capture,
basic network context is assumed:

- Source system identity
- Destination domain or IP
- Direction of traffic
- Approximate timing

This context supports correlation during investigations
and improves confidence during audits.

---

## SOC Investigation Use Cases

From a SOC perspective, these logs support:

- Establishing normal behavior baselines
- Identifying anomalous vendor activity
- Triage during potential incidents
- Root cause analysis after findings
- Evidence preservation

DNS anomalies are often the first indicator
that vendor activity warrants review.

---

## Audit Use Cases

From an audit and compliance perspective, logs support:

- Demonstrating vendor access oversight
- Reconstructing activity during specific time windows
- Validating access aligns with documented purpose
- Supporting HIPAA safeguard requirements

If logs cannot answer these questions,
controls are considered insufficient.

---

## Retention Considerations

Log retention is treated as a risk decision.

Retention must be long enough to support:
- Incident response timelines
- Regulatory inquiries
- Internal investigations

Short retention periods create visibility gaps
that cannot be corrected retroactively.

---

## Logging Gaps as Findings

This lab treats the following as reportable findings:

- Missing DNS logs
- Incomplete timestamps
- Lack of source attribution
- Logs that cannot be correlated

A system that cannot explain its behavior
cannot defend its behavior.

---

## Summary

Logging enables:
- Detection
- Accountability
- Compliance
- Trust

In healthcare environments,
logs are not optional artifacts.
They are operational evidence.
