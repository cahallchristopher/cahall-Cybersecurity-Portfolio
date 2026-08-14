# Documentation

Additional documentation for the cyber range.

## Contents

| File | Description |
|------|-------------|
| `firewall-rules.md` | OpenWrt nftables firewall zone policy |
| `attack-playbooks.md` | Step-by-step attack scenario guides |
| `troubleshooting.md` | Common issues and fixes |
| `credentials.md` | ⚠️ VM credentials (keep private) |

## Firewall Zone Policy

| Source | Destination | Policy |
|--------|-------------|--------|
| LAN | WAN | ACCEPT |
| LAN | DMZ | ACCEPT |
| DMZ | WAN | ACCEPT |
| DMZ | LAN | DROP |
| MGMT | ALL | ACCEPT |
| LAN | MGMT | DROP |
| WAN | ALL | DROP |

> 🚧 Documentation coming soon
