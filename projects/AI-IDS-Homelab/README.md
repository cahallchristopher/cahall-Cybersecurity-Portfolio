# AI-Powered IDS Homelab

A complete cybersecurity homelab built on Linux Mint using 
KVM/virt-manager with 4 virtual machines.

## Lab Components
- **OpenWRT** — Virtual router with mwan3 failover and iptables firewall
- **sentinel** — AI-IDS using Python, Flask, and Streamlit
- **gateway** — dnsmasq DNS sinkhole and NAT router
- **client** — Test client VM

## Full Build Documentation
See [BUILD_NOTES.md](BUILD_NOTES.md) for complete step-by-step guide.
