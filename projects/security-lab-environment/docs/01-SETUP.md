# Security Lab Environment - Complete Setup Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Part 1: DNSmasq Server Setup](#part-1-dnsmasq-server-setup)
- [Part 2: LimaCharlie Sensor VM Setup](#part-2-limacharlie-sensor-vm-setup)
- [Part 3: Kali Linux Attacker VM](#part-3-kali-linux-attacker-vm)
- [Part 4: Network Configuration](#part-4-network-configuration)
- [Part 5: Create Snapshots](#part-5-create-snapshots)
- [Part 6: Verification and Testing](#part-6-verification-and-testing)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

- **Host Machine RAM**: 16GB minimum (32GB recommended)
- **Available Disk Space**: 100GB minimum
- **CPU**: Multi-core processor with virtualization support (VT-x/AMD-V enabled in BIOS)

### Software Requirements

- **VirtualBox**: Version 7.0 or later
  - Download: https://www.virtualbox.org/wiki/Downloads
  - Install VirtualBox Extension Pack for enhanced features

- **Operating System ISOs**:
  - Ubuntu Server 22.04.5 LTS: https://ubuntu.com/download/server
  - Debian 12 (Bookworm): https://www.debian.org/download
  - Kali Linux VirtualBox OVA: https://www.kali.org/get-kali/#kali-virtual-machines

### Accounts Needed

- **LimaCharlie Account**: Free tier available
  - Sign up: https://app.limacharlie.io
  - Create organization before sensor installation

### Knowledge Prerequisites

- Basic Linux command line navigation
- Understanding of networking concepts (IP, DHCP, DNS, NAT)
- Familiarity with VirtualBox interface

---

## Architecture Overview

### Network Design
```
Internet
   |
   └── VirtualBox NAT Gateway
        |
        ├── soarlab (Ubuntu Server 22.04)
        │    ├── enp0s3: NAT (WAN - Internet access)
        │    └── enp0s8: 10.50.50.1 (LAN - Internal gateway)
        │
        └── Internal Network "SecurityLab" (10.50.50.0/24)
             |
             ├── lima_sensor (Debian 12 + XFCE)
             │    ├── enp0s3: 10.50.50.x (DHCP from soarlab)
             │    └── enp0s8: NAT (LimaCharlie cloud connectivity)
             │
             └── kali_attacker (Kali Linux 2024.4)
                  ├── eth0: 10.50.50.x (DHCP from soarlab)
                  └── eth1: NAT (Updates and tool downloads)
```

### IP Addressing Scheme

- **Network**: 10.50.50.0/24
- **Gateway**: 10.50.50.1 (soarlab)
- **DHCP Range**: 10.50.50.50 - 10.50.50.200
- **DNS Servers**: 1.1.1.1 (Cloudflare), 8.8.8.8 (Google)

---

## Part 1: DNSmasq Server Setup

### 1.1 Create Ubuntu Server VM

1. **Open VirtualBox** and click "New"

2. **VM Configuration**:
```
   Name: soarlab
   Type: Linux
   Version: Ubuntu (64-bit)
```

3. **Memory Settings**:
   - RAM: 2048 MB (2GB)

4. **Hard Disk**:
   - Create a virtual hard disk now
   - VDI (VirtualBox Disk Image)
   - Dynamically allocated
   - Size: 20 GB

5. **Click "Create"**

### 1.2 Configure Network Adapters

1. **Select soarlab VM** → Click "Settings" → "Network"

2. **Adapter 1 (NAT - WAN)**:
```
   Enable Network Adapter: ✓
   Attached to: NAT
```

3. **Adapter 2 (Internal Network - LAN)**:
```
   Enable Network Adapter: ✓
   Attached to: Internal Network
   Name: SecurityLab
```

4. **Click "OK"**

### 1.3 Install Ubuntu Server

1. **Start soarlab VM**

2. **Mount Ubuntu Server ISO**:
   - Click "Devices" → "Optical Drives" → "Choose disk image"
   - Select `ubuntu-22.04.5-live-server-amd64.iso`

3. **Installation Steps**:
   - Language: English
   - Keyboard: Your layout
   - Installation type: Ubuntu Server (default)
   - Network: Accept DHCP for enp0s3
   - Storage: Use entire disk (default)
   - Profile setup:
```
     Your name: sensor
     Server name: soarlab
     Username: sensor
     Password: [your secure password]
```
   - SSH: Install OpenSSH server (optional but recommended)
   - Featured Server Snaps: None needed
   - Wait for installation to complete
   - Reboot

4. **Login** with your credentials

### 1.4 Run DNSmasq Setup Script

1. **Update system**:
```bash
   sudo apt update && sudo apt upgrade -y
```

2. **Create setup script**:
```bash
   nano setup-dnsmasq.sh
```

3. **Paste the following script**:
```bash
   #!/bin/bash
   set -e
   
   echo "[+] Temporary DNS fix for apt"
   sudo rm -f /etc/resolv.conf
   echo -e "nameserver 1.1.1.1\nnameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   
   echo "[+] Enabling IPv4 forwarding"
   cat <<EOF | sudo tee /etc/sysctl.d/99-soar-forwarding.conf
   net.ipv4.ip_forward=1
   net.ipv4.conf.all.accept_redirects=0
   net.ipv4.conf.all.send_redirects=0
   net.ipv4.conf.all.accept_source_route=0
   EOF
   sudo sysctl --system
   
   echo "[+] Installing dnsmasq"
   sudo apt update
   sudo apt install -y dnsmasq
   
   echo "[+] Configuring dnsmasq"
   cat <<EOF | sudo tee /etc/dnsmasq.d/soar.conf
   interface=enp0s8
   except-interface=lo
   port=53
   dhcp-range=10.50.50.50,10.50.50.200,12h
   dhcp-option=3,10.50.50.1
   dhcp-option=6,10.50.50.1
   server=1.1.1.1
   server=8.8.8.8
   log-queries
   log-dhcp
   log-facility=/var/log/dnsmasq.log
   bind-dynamic
   EOF
   
   echo "[+] Restarting dnsmasq"
   sudo systemctl restart dnsmasq
   
   echo "[+] Forcing system DNS to dnsmasq"
   sudo rm -f /etc/resolv.conf
   echo "nameserver 127.0.0.1" | sudo tee /etc/resolv.conf
   sudo chattr +i /etc/resolv.conf
   
   echo "[+] Flushing firewall"
   sudo iptables -F
   sudo iptables -t nat -F
   sudo iptables -X
   
   echo "[+] Applying firewall rules"
   sudo iptables -P INPUT ACCEPT
   sudo iptables -P FORWARD DROP
   sudo iptables -P OUTPUT ACCEPT
   sudo iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
   sudo iptables -A FORWARD -i enp0s8 -o enp0s3 -j ACCEPT
   sudo iptables -t nat -A POSTROUTING -s 10.50.50.0/24 -o enp0s3 -j MASQUERADE
   
   echo "[+] Saving firewall state"
   sudo iptables-save | sudo tee /root/iptables.backup
   
   echo "[+] Gateway setup complete"
```

4. **Make executable and run**:
```bash
   chmod +x setup-dnsmasq.sh
   ./setup-dnsmasq.sh
```

5. **Verify DNSmasq is running**:
```bash
   sudo systemctl status dnsmasq
```
   Should show: `active (running)`

### 1.5 Configure Static IP for Internal Interface

1. **Edit netplan configuration**:
```bash
   sudo nano /etc/netplan/00-installer-config.yaml
```

2. **Add configuration**:
```yaml
   network:
     version: 2
     ethernets:
       enp0s3:
         dhcp4: true
       enp0s8:
         addresses:
           - 10.50.50.1/24
```

3. **Apply configuration**:
```bash
   sudo netplan apply
```

4. **Verify**:
```bash
   ip a show enp0s8
```
   Should show: `inet 10.50.50.1/24`

---

## Part 2: LimaCharlie Sensor VM Setup

### 2.1 Create Debian VM

1. **VirtualBox** → Click "New"

2. **VM Configuration**:
```
   Name: lima_sensor
   Type: Linux
   Version: Debian (64-bit)
```

3. **Memory and CPU**:
   - RAM: 4096 MB (4GB)
   - CPUs: 2

4. **Hard Disk**:
   - Create virtual hard disk
   - VDI format
   - Dynamically allocated
   - Size: 40 GB

### 2.2 Configure Network Adapters

1. **Settings** → "Network"

2. **Adapter 1 (Internal Network)**:
```
   Enable Network Adapter: ✓
   Attached to: Internal Network
   Name: SecurityLab
```

3. **Adapter 2 (NAT for LimaCharlie)**:
```
   Enable Network Adapter: ✓
   Attached to: NAT
```

### 2.3 Install Debian with XFCE Desktop

1. **Start VM** and mount Debian ISO

2. **Installation Process**:
   - Language: English
   - Location: Your location
   - Keyboard: Your layout
   - Hostname: `limasensor`
   - Domain: Leave blank
   - Root password: [set password]
   - User account:
```
     Full name: sensor
     Username: sensor
     Password: [set password]
```
   - Partitioning: Guided - use entire disk
   - Software Selection:
```
     [✓] Debian desktop environment
     [✓] ... XFCE
     [ ] ... GNOME (uncheck)
     [✓] SSH server
     [✓] standard system utilities
```
   - Install GRUB: Yes, to /dev/sda
   - Complete installation and reboot

### 2.4 Install XFCE Desktop (Alternative Method)

If you need to install XFCE after the fact:
```bash
#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

sudo apt update && sudo apt upgrade -y

# Install XFCE components
sudo apt install -y \
  xfce4 \
  xfce4-goodies \
  xfce4-session \
  xfce4-terminal \
  xfwm4 \
  xfdesktop4 \
  xfce4-panel \
  xfce4-settings \
  xfce4-power-manager \
  xfce4-screensaver \
  dbus-x11

# Install GDM3 display manager
sudo apt install -y gdm3
sudo systemctl enable gdm3
sudo systemctl set-default graphical.target

# Install basic tools
sudo apt install -y \
  firefox-esr \
  wget \
  curl \
  net-tools \
  fonts-noto \
  thunar \
  thunar-archive-plugin \
  thunar-volman

# Fix permissions
sudo chown -R "$USER:$USER" "$HOME"
chmod 755 "$HOME"
rm -f ~/.Xauthority ~/.ICEauthority

sudo reboot
```

### 2.5 Install VirtualBox Guest Additions

1. **Login to XFCE desktop**

2. **Open terminal**

3. **Install prerequisites**:
```bash
   sudo apt update
   sudo apt install -y build-essential dkms linux-headers-$(uname -r) wget
```

4. **Download Guest Additions**:
```bash
   cd /tmp
   wget https://download.virtualbox.org/virtualbox/7.0.20/VBoxGuestAdditions_7.0.20.iso
```

5. **Mount and install**:
```bash
   sudo mkdir -p /mnt/cdrom
   sudo mount -o loop VBoxGuestAdditions_7.0.20.iso /mnt/cdrom
   cd /mnt/cdrom
   sudo ./VBoxLinuxAdditions.run
```

6. **Cleanup**:
```bash
   cd ~
   sudo umount /mnt/cdrom
   rm /tmp/VBoxGuestAdditions_7.0.20.iso
```

7. **Add user to vboxsf group**:
```bash
   sudo usermod -aG vboxsf $USER
```

8. **Reboot**:
```bash
   sudo reboot
```

### 2.6 Disable Screen Blanking

**IMPORTANT for VMs** - Prevents display from going black:
```bash
#!/bin/bash
# Disable screen blanking

xset s off
xset s noblank
xset -dpms

xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/blank-on-ac -n -t int -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/blank-on-battery -n -t int -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-enabled -n -t bool -s false
xfconf-query -c xfce4-screensaver -p /saver/enabled -n -t bool -s false

mkdir -p ~/.config/autostart
cat > ~/.config/autostart/disable-screensaver.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Disable Screen Blanking
Exec=sh -c "xset s off; xset s noblank; xset -dpms"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo "✅ Screen blanking disabled!"
```

### 2.7 Install LimaCharlie Sensor

#### Step 1: Create LimaCharlie Account

1. Go to: https://app.limacharlie.io
2. Sign up for free account
3. Verify email

#### Step 2: Create Organization

1. Click profile → "Organizations" → "+ Create Organization"
2. Name: `SecurityLab`
3. Region: Choose closest to you
4. Plan: Free tier
5. Click "Create"

#### Step 3: Create Installation Key

1. Click "Installation Keys" in left menu
2. Click "+ Create Installation Key"
3. Description: `Debian Lab Sensor`
4. Tags (optional):
```
   environment:lab
   os:debian
   virtualization:virtualbox
   purpose:training
```
5. Click "Create"
6. **COPY THE INSTALLATION KEY** (looks like: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)

#### Step 4: Download Sensor

1. In LimaCharlie console: "Sensors" → "+ Add Sensor"
2. Platform: Linux
3. Distribution: Debian/Ubuntu
4. Architecture: x86_64 (64-bit)
5. Click download link
6. File downloads to: `~/Downloads/hcp_linux_x64_release_4.33.24`

#### Step 5: Install Sensor
```bash
cd ~/Downloads
chmod +x hcp_linux_x64_release_4.33.24

# Install with your key
sudo ./hcp_linux_x64_release_4.33.24 -i <YOUR-INSTALLATION-KEY>

# You should see: *** Agent installed successfully!
```

#### Step 6: Create Systemd Service

The sensor may auto-create this, but verify:
```bash
# Check if service exists
sudo systemctl status limacharlie

# If not, create it:
sudo nano /etc/systemd/system/limacharlie.service
```

Paste:
```ini
[Unit]
Description=LimaCharlie Agent

[Service]
Type=simple
Restart=always
ExecStart=/usr/local/bin/limacharlie_sensor
StandardError=null
WorkingDirectory=/etc
StandardOutput=null
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable limacharlie
sudo systemctl start limacharlie
sudo systemctl status limacharlie
```

#### Step 7: Verify Sensor

1. Go to LimaCharlie web console
2. Click "Sensors"
3. Wait 30-60 seconds
4. Your sensor should appear: **Online** (green)
5. Hostname: `limasensor`

#### Step 8: Test Sensor

1. Click on sensor
2. Go to "Console" tab
3. Run: `os_processes`
4. Should see JSON output of all processes

---

## Part 3: Kali Linux Attacker VM

### 3.1 Download Kali Linux

1. Go to: https://www.kali.org/get-kali/#kali-virtual-machines
2. Download: **VirtualBox** (64-bit)
3. File: `kali-linux-2024.4-virtualbox-amd64.7z`
4. Size: ~3-4GB

### 3.2 Extract Archive
```bash
# Install 7zip
sudo apt install p7zip-full

# Extract
7z x kali-linux-2024.4-virtualbox-amd64.7z
```

### 3.3 Import Kali VM

**Option A: Command Line**:
```bash
VBoxManage import kali-linux-2024.4-virtualbox-amd64.ova \
  --vsys 0 --vmname "kali_attacker" \
  --vsys 0 --cpus 2 \
  --vsys 0 --memory 4096
```

**Option B: GUI**:
1. VirtualBox → File → Import Appliance
2. Select `.ova` file
3. Name: `kali_attacker`
4. CPUs: 2
5. RAM: 4096 MB
6. Import

### 3.4 Configure Network

1. Settings → Network

2. **Adapter 1 (Internal)**:
```
   Enable: ✓
   Attached to: Internal Network
   Name: SecurityLab
```

3. **Adapter 2 (NAT)**:
```
   Enable: ✓
   Attached to: NAT
```

### 3.5 Start and Configure

1. **Start kali_attacker**

2. **Login**:
```
   Username: kali
   Password: kali
```

3. **Change password** (recommended):
```bash
   passwd
```

4. **Configure network**:
```bash
   # Check interfaces
   ip a
   
   # Request DHCP on eth0
   sudo dhclient eth0
   
   # Verify IP
   ip a show eth0  # Should be 10.50.50.x
```

5. **Test connectivity**:
```bash
   # Ping gateway
   ping -c 4 10.50.50.1
   
   # Test DNS
   nslookup google.com
   
   # Test internet
   ping -c 4 8.8.8.8
```

6. **Update Kali** (optional):
```bash
   sudo apt update
   sudo apt upgrade -y
```

---

## Part 4: Network Configuration

### 4.1 Verify DHCP and Connectivity

**On soarlab**:
```bash
# Check DNSmasq status
sudo systemctl status dnsmasq

# View DHCP leases
cat /var/lib/misc/dnsmasq.leases

# Monitor logs
sudo tail -f /var/log/dnsmasq.log
```

**On lima_sensor**:
```bash
# Check IP
ip a show enp0s3

# Should show: 10.50.50.x

# Test gateway
ping -c 4 10.50.50.1

# Test DNS
nslookup google.com

# Test internet
ping -c 4 google.com
```

**On kali_attacker**:
```bash
# Same tests
ip a show eth0
ping -c 4 10.50.50.1
nslookup google.com
ping -c 4 google.com
```

### 4.2 Test Inter-VM Communication

**From kali_attacker**:
```bash
# Scan internal network
nmap -sn 10.50.50.0/24

# Should discover:
# - 10.50.50.1 (soarlab)
# - 10.50.50.x (lima_sensor)
# - 10.50.50.x (kali_attacker)
```

---

## Part 5: Create Snapshots

### 5.1 Shutdown All VMs
```bash
# From each VM:
sudo shutdown -h now

# Or from VirtualBox: Machine → ACPI Shutdown
```

**Wait for all VMs to fully power off.**

### 5.2 Create Baseline Snapshots
```bash
# Snapshot soarlab
VBoxManage snapshot "soarlab" take "Working-DNSmasq-Server" \
  --description "Functional DNSmasq DHCP/DNS server configured and tested. Date: $(date '+%Y-%m-%d')"

# Snapshot lima_sensor
VBoxManage snapshot "lima_sensor" take "Clean-LC-Sensor-Install" \
  --description "Debian 12 with XFCE, VBox Guest Additions, LimaCharlie sensor installed and online. Date: $(date '+%Y-%m-%d')"

# Snapshot kali_attacker
VBoxManage snapshot "kali_attacker" take "Clean-Kali-Base" \
  --description "Fresh Kali Linux configured for internal network. Date: $(date '+%Y-%m-%d')"
```

### 5.3 Verify Snapshots
```bash
# List snapshots
VBoxManage snapshot "soarlab" list
VBoxManage snapshot "lima_sensor" list
VBoxManage snapshot "kali_attacker" list
```

### 5.4 Start VMs
```bash
# Start in order
VBoxManage startvm "soarlab" --type headless
VBoxManage startvm "lima_sensor" --type gui
VBoxManage startvm "kali_attacker" --type gui
```

---

## Part 6: Verification and Testing

### 6.1 Network Verification Checklist

- [ ] All VMs receive DHCP addresses from soarlab
- [ ] All VMs can ping each other
- [ ] DNS resolution works on all VMs
- [ ] Internet access works on all VMs
- [ ] NAT forwarding works from internal network

### 6.2 LimaCharlie Verification

1. **Check sensor status**:
```bash
   sudo systemctl status limacharlie
```

2. **Verify in console**:
   - Go to https://app.limacharlie.io
   - Sensors → `limasensor` should be **Online** (green)
   - Click sensor → Timeline → See events
   - Console tab → Run `os_processes` → See output

### 6.3 Attack Simulation Test

**From kali_attacker**:
```bash
# Network scan
nmap -sV 10.50.50.0/24

# Port scan target (replace with lima_sensor IP)
nmap -p- 10.50.50.x
```

**In LimaCharlie Console**:
- Go to lima_sensor → Timeline
- You should see nmap scans logged
- Network connections from Kali IP address

### 6.4 Generate Test Activity

**On lima_sensor**:
```bash
# File activity
echo "test" > /tmp/limacharlie_test.txt

# Process activity
ps aux | head -20

# Network activity
curl https://www.google.com
```

**Check LimaCharlie Timeline** - all events should appear!

---

## Troubleshooting

### DNSmasq Not Working

**Check service**:
```bash
sudo systemctl status dnsmasq
sudo journalctl -u dnsmasq -f
```

**Restart**:
```bash
sudo systemctl restart dnsmasq
```

**Verify config**:
```bash
sudo cat /etc/dnsmasq.d/soar.conf
```

### No DHCP Address

**On client VM**:
```bash
# Request DHCP manually
sudo dhclient <interface>

# Check interface is up
ip link show <interface>

# Bring up if down
sudo ip link set <interface> up
```

**On soarlab**:
```bash
# Check leases
cat /var/lib/misc/dnsmasq.leases

# Monitor logs
sudo tail -f /var/log/dnsmasq.log
```

### LimaCharlie Sensor Offline
```bash
# Check service
sudo systemctl status limacharlie

# View logs
sudo journalctl -u limacharlie -f

# Test internet
ping app.limacharlie.io

# Restart sensor
sudo systemctl restart limacharlie
```

### VMs Can't Ping Each Other
```bash
# Verify internal network name matches
# VirtualBox Settings → Network → "SecurityLab"

# Check firewall
sudo iptables -L -v -n

# Check IP addresses
ip a
```

### Screen Goes Blank
```bash
# Re-run screen blanking disable script
xset s off
xset s noblank
xset -dpms
```

### Snapshot Restore
```bash
# Power off VM
VBoxManage controlvm "<VM-Name>" poweroff

# Restore snapshot
VBoxManage snapshot "<VM-Name>" restore "<Snapshot-Name>"

# Start VM
VBoxManage startvm "<VM-Name>"
```

---

## Resources

- **LimaCharlie Documentation**: https://doc.limacharlie.io
- **VirtualBox Manual**: https://www.virtualbox.org/manual/
- **DNSmasq Documentation**: https://thekelleys.org.uk/dnsmasq/doc.html
- **Kali Linux Documentation**: https://www.kali.org/docs/
- **Debian Documentation**: https://www.debian.org/doc/

---

## Conclusion

Congratulations! You now have a fully functional security lab environment with:

- ✅ Isolated network (10.50.50.0/24)
- ✅ DHCP/DNS server (soarlab)
- ✅ EDR-monitored target (lima_sensor)
- ✅ Penetration testing platform (kali_attacker)
- ✅ Baseline snapshots for easy reset

### What You Can Do Next:

1. **Practice Attack Scenarios**:
   - Nmap scanning
   - Metasploit exploitation
   - Brute force attempts
   - Web application attacks

2. **Create Detection Rules**:
   - Build D&R rules in LimaCharlie
   - Test and tune detections
   - Practice incident response

3. **Expand the Lab**:
   - Add vulnerable web applications
   - Deploy additional sensors
   - Create multi-stage attack scenarios

4. **Document Your Work**:
   - Take screenshots of attacks
   - Document detection rules
   - Write up findings

**Happy hunting! 🎯**
