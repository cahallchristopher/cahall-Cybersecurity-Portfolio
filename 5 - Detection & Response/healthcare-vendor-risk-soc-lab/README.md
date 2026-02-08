Healthcare Vendor Risk SOC Lab

HIPAA Safeguards • Logging • Audit Trails • SOC Alerts

What this lab is

This lab models a common healthcare security failure: vendor access that exists, but isn’t properly monitored.

There is no hacking in this lab.
There is no malware.

The risk comes from quiet misconfiguration and lack of visibility.

This mirrors how many real HIPAA violations occur.

Why this matters

Recent healthcare enforcement actions show that:

Sensitive data is often exposed by vendors

Third-party access is frequently over-trusted

Failures are discovered after data is already exposed

This lab focuses on visibility, accountability, and detection, not exploitation.

Lab design (high level)

Ubuntu Server acts as a secure gateway

Windows system represents patient data access

Vendor system represents a third-party billing or service provider

All traffic passes through the gateway.
All activity is logged.
Vendor behavior is monitored.

This reflects real healthcare network design.

Network & gateway setup (evidence)

The gateway enforces segmentation and visibility between internal systems and vendors.

Host-only networking without external DHCP

Ubuntu gateway installation summary

Internal interface configured and up

DNS visibility and audit logging

DNS is a critical signal for vendor behavior and intent.

The gateway runs dnsmasq with logging enabled and bound only to the internal interface.

dnsmasq bound to internal interfaces

dnsmasq service running

This supports:

Audit trails

Behavioral analysis

HIPAA accountability requirements

Detection tooling: Zeek (network telemetry)

Zeek is deployed on the gateway to provide deep network visibility.

Installation (documented, reproducible)

The following screenshot shows the exact commands used to install Zeek from the official repository:

Active monitoring and logs

Zeek runs on the internal interface and generates structured logs for analysis.

Zeek running

Zeek log files present

These logs support:

DNS analysis

Connection tracking

Audit evidence

Incident reconstruction

What this lab demonstrates

How vendor access can introduce risk

How DNS reveals intent and behavior

How logging supports HIPAA audit requirements

How SOC-style alerts surface quiet failures

How technical controls map to compliance safeguards

Skills demonstrated

Detection and response fundamentals

DNS logging and analysis

Network segmentation

Vendor risk modeling

HIPAA safeguard implementation

Clear technical documentation

How this fits into the portfolio

This lab lives in Detection & Response because it focuses on:

Visibility

Logging

Alerting

Incident awareness

It connects earlier topics (assets, threats, networking) to later topics (SIEM, SOAR, automation).

How I explain this lab in interviews

“I built a lab that models healthcare vendor risk.
A third-party system has limited access through a gateway.
DNS and traffic are logged, and alerts trigger on suspicious behavior.
Each control maps back to HIPAA safeguards.”

What this lab is not

It is not a penetration test

It is not exploit-focused

It is not about flashy tooling

It is about making quiet risk visible.
