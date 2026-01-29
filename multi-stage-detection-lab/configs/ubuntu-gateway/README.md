# Ubuntu Gateway Configuration Files

This directory contains configuration files and scripts for the Ubuntu Server gateway.

---

## Files

### setup-soar-gateway.sh
Automated setup script that configures the entire gateway.

**Usage:**
```bash
chmod +x setup-soar-gateway.sh
./setup-soar-gateway.sh
```

**What it does:**
- Enables IP forwarding
- Installs dnsmasq
- Configures DHCP (10.50.50.50-200)
- Sets up DNS forwarding
- Configures NAT (iptables)
- Verifies all services

**Environment Variables:**
```bash
# Override defaults
INTERNAL_INTERFACE=enp0s8 \
EXTERNAL_INTERFACE=enp0s3 \
DHCP_RANGE_START=10.50.50.100 \
DHCP_RANGE_END=10.50.50.150 \
GATEWAY_IP=10.50.50.1 \
./setup-soar-gateway.sh
```

---

## Manual Installation

See: [Ubuntu Gateway Setup Guide](../../docs/01-ubuntu-gateway-setup.md)

---

## Troubleshooting

### Script fails with "dnsmasq failed to start"
```bash
# Check logs
sudo journalctl -u dnsmasq -n 50

# Common fix: systemd-resolved conflict
sudo systemctl disable systemd-resolved
sudo systemctl stop systemd-resolved
./setup-soar-gateway.sh
```

### No internet after setup
```bash
# Check NAT
sudo iptables -t nat -L POSTROUTING -n

# Should see MASQUERADE rule
# If missing, re-run script
```

---

## Verification Commands
```bash
# All services
sudo systemctl status dnsmasq
sysctl net.ipv4.ip_forward
sudo iptables -t nat -L -n

# Test from client VM
ping 10.50.50.1      # Gateway
ping 8.8.8.8         # Internet
nslookup google.com  # DNS
```
