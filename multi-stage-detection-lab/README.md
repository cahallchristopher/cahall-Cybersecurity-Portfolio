
---

## 📋 Detailed Setup Documentation

### Ubuntu Gateway Setup
Complete guide: [Ubuntu Gateway Setup](docs/01-ubuntu-gateway-setup.md)

**Quick setup:**
```bash
wget https://raw.githubusercontent.com/cahallchristopher/cahall-Cybersecurity-Portfolio/main/multi-stage-detection-lab/configs/ubuntu-gateway/setup-soar-gateway.sh
chmod +x setup-soar-gateway.sh
./setup-soar-gateway.sh
```

**Verification:**
```bash
sudo systemctl status dnsmasq
sysctl net.ipv4.ip_forward
sudo iptables -t nat -L
```

### Quick Reference
See: [Gateway Quick Reference](docs/gateway-quick-reference.md)

---

## 🔧 Configuration Files

All configuration files are in `configs/`:
- [ubuntu-gateway/](configs/ubuntu-gateway/) - Gateway setup script and configs
- [kali-attacker/](configs/kali-attacker/) - Kali configuration (coming soon)
- [windows-victim/](configs/windows-victim/) - Windows configs (coming soon)

---

