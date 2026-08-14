# Networks

libvirt XML network definitions for the cyber range.

## Files

| File | Bridge | Subnet | Purpose |
|------|--------|--------|---------|
| `br-lan.xml` | br-lan | 192.168.1.0/24 | Attacker LAN |
| `br-dmz.xml` | br-dmz | 10.10.10.0/24 | DMZ targets |
| `br-mgmt.xml` | br-mgmt | 10.99.99.0/24 | Management |
| `br-ad.xml` | br-ad | 10.20.20.0/24 | Active Directory |
| `nat-wan.xml` | virbr1 | 192.168.122.0/24 | WAN/NAT |

## Usage

```bash
# Define and start a network
virsh net-define networks/br-lan.xml
virsh net-start br-lan
virsh net-autostart br-lan
```

> 🚧 XML files coming soon
