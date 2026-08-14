# libvirt Hook Scripts

Automatically attach vnet interfaces to correct bridges on VM start.

## Files

| File | Purpose |
|------|---------|
| `qemu` | Fires on VM start - attaches vnets to bridges |
| `network` | Fires on network start - configures STP and rp_filter |

## Installation

```bash
sudo mkdir -p /etc/libvirt/hooks
sudo cp hooks/qemu /etc/libvirt/hooks/qemu
sudo cp hooks/network /etc/libvirt/hooks/network
sudo chmod +x /etc/libvirt/hooks/qemu
sudo chmod +x /etc/libvirt/hooks/network
sudo systemctl restart libvirtd
```

## How it works

Uses MAC address lookup instead of virsh to avoid deadlock:
```bash
# Find vnet by MAC (host-side MAC = fe: + VM NIC MAC last 5 octets)
VNET=$(ip link | grep -B1 "fe:54:00:xx:xx:xx" | grep -o "vnet[0-9]*")
ip link set "$VNET" master br-lan
```

> 🚧 Hook scripts coming soon
