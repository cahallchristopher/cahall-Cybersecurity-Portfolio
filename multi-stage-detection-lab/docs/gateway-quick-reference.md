# Gateway Quick Reference

## Configuration Summary

| Component | Value |
|-----------|-------|
| **Gateway IP** | 10.50.50.1/24 |
| **DHCP Range** | 10.50.50.50 - 10.50.50.200 |
| **DNS Servers** | 1.1.1.1, 8.8.8.8 |
| **Lease Time** | 12 hours |
| **Internal Interface** | enp0s8 |
| **External Interface** | enp0s3 |

---

## One-Liner Checks
```bash
# Everything in one command
echo "=== Gateway Status ===" && \
sudo systemctl is-active dnsmasq && echo "✓ dnsmasq running" || echo "✗ dnsmasq NOT running" && \
sysctl net.ipv4.ip_forward | grep -q "= 1" && echo "✓ IP forwarding enabled" || echo "✗ IP forwarding disabled" && \
sudo iptables -t nat -L POSTROUTING -n | grep -q MASQUERADE && echo "✓ NAT configured" || echo "✗ NAT NOT configured" && \
cat /var/lib/misc/dnsmasq.leases | wc -l && echo "DHCP leases"
```

---

## Emergency Reset
```bash
# Reset dnsmasq
sudo systemctl stop dnsmasq
sudo rm -f /var/lib/misc/dnsmasq.leases
sudo systemctl start dnsmasq

# Reset firewall
sudo iptables -F
sudo iptables -t nat -F
# Re-run setup script
```

---

## Port Reference

| Port | Protocol | Service | Purpose |
|------|----------|---------|---------|
| 53 | UDP/TCP | DNS | Name resolution |
| 67 | UDP | DHCP | IP assignment |
| 68 | UDP | DHCP | Client responses |

---

## Log Locations
```bash
# dnsmasq logs
/var/log/dnsmasq.log

# System logs
sudo journalctl -u dnsmasq

# DHCP leases
/var/lib/misc/dnsmasq.leases
```
