# Vendor Risk Assessment — Healthcare Vendor Risk SOC Lab

This document demonstrates how SOC observations and logging
feed into a structured vendor risk assessment.

The focus is on evidence-based evaluation rather than assumptions.

---

## Purpose of Vendor Risk Assessment

Healthcare organizations rely on third-party vendors to
support billing, operations, and patient services.

Vendor risk assessments exist to answer a simple question:

Can this vendor be trusted with access to sensitive systems?

Trust is evaluated using evidence.

---

## Vendor Profile (Lab Context)

**Vendor Role:**  
Billing / operational service provider

**Access Characteristics:**  
- Limited network access
- No direct access to internal assets
- All activity routed through a gateway
- DNS and network activity logged

**Trust Level:**  
Semi-trusted

---

## Evidence Sources Used

This lab uses the following evidence sources for vendor evaluation:

- DNS query logs
- Timing and frequency of activity
- Domain reputation context
- Alignment with documented business purpose
- Presence or absence of logging gaps

All conclusions are based on observable behavior.

---

## Risk Indicators

### Indicator 1 — Undocumented Behavior

Risk increases when:
- Vendor accesses undocumented domains
- Activity does not align with stated purpose
- Changes occur without notice

Undocumented behavior is treated as a risk signal.

---

### Indicator 2 — Abnormal Activity Patterns

Risk increases when:
- DNS activity spikes unexpectedly
- Requests occur at fixed intervals
- Activity appears automated without explanation

Patterns matter more than single events.

---

### Indicator 3 — Off-Hours Activity

Risk increases when:
- Vendor activity occurs outside approved hours
- No maintenance window is documented
- Oversight is reduced

Off-hours access requires justification.

---

### Indicator 4 — Visibility Gaps

Risk increases significantly when:
- Logs are missing
- Activity cannot be attributed
- Evidence cannot be retained

Lack of visibility is treated as high risk.

---

## Risk Scoring Approach (Conceptual)

This lab uses a simple qualitative approach:

- **Low Risk:** Documented, explainable, logged behavior
- **Medium Risk:** Minor anomalies with justification
- **High Risk:** Repeated unexplained activity or logging gaps

Complex scoring models are not required to identify concern.

---

## SOC and Governance Interaction

SOC findings inform:
- Vendor reviews
- Contract discussions
- Access restrictions
- Remediation requirements

Detection feeds governance.
Governance feeds control improvements.

---

## Remediation Examples

Potential remediation actions include:
- Clarifying vendor scope
- Updating documentation
- Restricting access
- Increasing monitoring
- Escalating to compliance or legal teams

Remediation is proportional to risk.

---

## Summary

Vendor risk is not static.

This lab demonstrates how:
- Detection produces evidence
- Evidence informs risk decisions
- Risk decisions drive control changes

Vendor trust must be continuously validated.
