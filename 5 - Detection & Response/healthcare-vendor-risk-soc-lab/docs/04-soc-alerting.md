# SOC Alerting Strategy — Healthcare Vendor Risk SOC Lab

This document defines the alerting logic used in the lab.
Alerts are designed to surface meaningful vendor risk,
not generate noise.

The focus is on explainable, reviewable signals that
support SOC decision-making.

---

## Alerting Philosophy

Not all suspicious activity is malicious.
Not all malicious activity is loud.

This lab prioritizes alerts that are:
- Explainable
- Actionable
- Tied to documented risk
- Reviewable by analysts

An alert that cannot be explained
is treated as low value.

---

## Alert Category 1: Unexpected Vendor Domains

### Trigger Condition
A vendor system resolves domains that are:
- Not documented
- Outside expected business purpose
- Previously unseen

### Why This Matters
Unexpected domains may indicate:
- Misconfiguration
- Shadow dependencies
- Data exfiltration paths
- Compromised vendor systems

### SOC Action
- Review domain context
- Validate against vendor documentation
- Escalate if unexplained

---

## Alert Category 2: Excessive DNS Frequency

### Trigger Condition
Vendor DNS queries occur:
- At unusually high frequency
- At consistent intervals
- Outside normal usage patterns

### Why This Matters
High-frequency DNS patterns can indicate:
- Automated processes
- Beaconing behavior
- Unapproved integrations

### SOC Action
- Compare against baseline behavior
- Check timing consistency
- Correlate with business hours

---

## Alert Category 3: Off-Hours Vendor Activity

### Trigger Condition
Vendor activity occurs:
- Outside documented business hours
- During weekends or holidays
- Without change approval

### Why This Matters
Off-hours access increases risk and reduces oversight.

### SOC Action
- Validate approved maintenance windows
- Confirm vendor justification
- Document findings

---

## Alert Category 4: Logging Gaps

### Trigger Condition
Expected logs are:
- Missing
- Incomplete
- Delayed
- Unattributable

### Why This Matters
A lack of logs prevents detection, investigation,
and compliance validation.

This is treated as a security finding.

### SOC Action
- Escalate as visibility failure
- Notify engineering or IT
- Document impact

---

## Alert Severity Considerations

Alert severity is influenced by:
- Sensitivity of affected systems
- Repetition of behavior
- Duration of anomaly
- Availability of corroborating evidence

Single events may warrant review.
Repeated unexplained events warrant escalation.

---

## False Positive Management

This lab assumes:
- Initial alerts may be noisy
- Baselines improve over time
- Documentation reduces false positives

Alert tuning is treated as a continuous process.

---

## Vendor Risk Tie-In

SOC alerts inform vendor risk assessments by:
- Identifying undocumented behavior
- Highlighting control gaps
- Providing evidence for risk scoring
- Supporting remediation discussions

Detection feeds governance.

---

## Summary

Effective SOC alerting is not about volume.
It is about clarity.

This lab demonstrates alerting
