# Lab Setup — Healthcare Vendor Risk SOC Lab

This document explains how the lab environment is built and why each component exists.

The focus is on visibility, logging, and detection rather than exploitation.

---

## Systems Overview

### Ubuntu Server (Gateway / Sensor Hub)
- Central network choke point
- Runs dnsmasq for DNS + DHCP + query logging
- Runs Zeek for network security monitoring
- Runs Snort for IDS alerting

### Windows 10 (Healthcare Asset)
- Represents internal systems accessing sensitive data
- Generates normal user traffic
- No direct internet access

### Kali Linux (Vendor / Attacker Simulation)
- Represents third-party vendor access
- Generates both normal and abnormal behavior

---

## Network Design

- Ubuntu has two network interfaces:
  - NAT (internet access)
  - Host-only (internal lab network)
- Windows and Kali use host-only networking only
- All outbound traffic passes through Ubuntu

This ensures centralized logging and attribution.

---

## Success Criteria

The lab is considered functional when:

- Windows and Kali receive internal IPs
- DNS queries appear in dnsmasq logs
- Zeek logs DNS activity and raises notices
- Snort generates alerts for suspicious patterns
