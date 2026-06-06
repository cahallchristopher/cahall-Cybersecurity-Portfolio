# Xubuntu VM + PrivateGPT Malware Traffic Analysis Lab

## Overview

This guide documents the complete build process for a malware traffic analysis lab using an Xubuntu VirtualBox VM connected to a host-based PrivateGPT instance. The lab is designed to download, extract, and analyze PCAP files from [malware-traffic-analysis.net](https://www.malware-traffic-analysis.net/), extract Indicators of Compromise (IOCs) using `tshark` and `suricata`, and feed findings into a local AI (PrivateGPT) for threat analysis and report generation.

---

## Environment

| Component | Details |
|---|---|
| **Host OS** | Ubuntu (chris-US-Desktop-Codex-R) |
| **Guest OS** | Ubuntu 26.04 LTS (Xubuntu VM) |
| **Hypervisor** | VirtualBox 7.0 |
| **Host CPU** | 12th Gen Intel Core i7-12700F |
| **VM RAM** | 3910 MB |
| **VM Kernel** | Linux 7.0.0-22-generic |
| **PrivateGPT** | Running on host, port 8001 (Gradio UI) |
| **Analysis Tools** | tshark, Wireshark, Suricata |

---

## Network Architecture

```
┌─────────────────────────────────────────────┐
│              HOST MACHINE                   │
│         chris-US-Desktop-Codex-R            │
│                                             │
│  PrivateGPT → localhost:8001                │
│  vboxnet1   → 192.168.57.1/24              │
└──────────────────┬──────────────────────────┘
                   │ Host-Only Network
                   │ 192.168.57.0/24
┌──────────────────┴──────────────────────────┐
│              XUBUNTU VM                     │
│                                             │
│  enp0s3 → 10.10.10.24/24  (network)        │
│  enp0s8 → 192.168.57.10/24 (host-only)     │
│                                             │
│  tshark / Wireshark / Suricata              │
└─────────────────────────────────────────────┘
         ↓
malware-traffic-analysis.net (PCAPs)
```

---

## Directory Structure

```
~/
├── pcaps/
│   ├── 2025-01-22-traffic-analysis-exercise.pcap.zip
│   ├── 2025-01-22-traffic-analysis-exercise.pcap
│   └── iocs.txt
/etc/
├── netplan/
│   └── 01-network-manager-all.yaml
└── resolv.conf
/mnt/
└── shared/          ← VirtualBox shared folder (optional)
```

---

## Step 1: VirtualBox Network Setup

### 1.1 Configure Host-Only Network

In VirtualBox on the host machine, configure a host-only network adapter:

1. Go to **File → Host Network Manager** (`Ctrl+H`)
2. Ensure `vboxnet1` exists with:
   - IPv4 Address: `192.168.57.1`
   - Subnet Mask: `255.255.255.0`
   - DHCP: **Disabled**
3. In VM Settings → **Network**:
   - Adapter 1: Your primary network (NAT or Bridged)
   - Adapter 2: **Host-only Adapter** → `vboxnet1`

---

## Step 2: Static IP Configuration (Netplan)

### 2.1 Install net-tools (optional)

```bash
sudo apt update && sudo apt install net-tools -y
```

### 2.2 Find Interface Names

```bash
ip a
```

In VirtualBox, typical interface names are:
- `enp0s3` — Adapter 1 (primary network)
- `enp0s8` — Adapter 2 (host-only)

### 2.3 Configure Netplan

Edit the Netplan configuration file:

```bash
sudo nano /etc/netplan/01-network-manager-all.yaml
```

Add the following configuration:

```yaml
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: no
      addresses: [10.10.10.24/24]
      routes:
        - to: default
          via: 10.10.10.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
    enp0s8:
      dhcp4: no
      addresses: [192.168.57.10/24]
```

> **Note:** `gateway4` is deprecated in Ubuntu 20.04+. Always use `routes: - to: default via:` instead.

### 2.4 Fix File Permissions

Netplan requires strict file permissions or it will warn and may refuse to apply:

```bash
sudo chmod 600 /etc/netplan/01-network-manager-all.yaml
```

### 2.5 Apply Configuration

```bash
sudo netplan apply
```

### 2.6 Verify Interfaces

```bash
ip a show enp0s3
ip a show enp0s8
```

**Expected output:**

```
2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    inet 10.10.10.24/24 brd 10.10.10.255 scope global enp0s3
       valid_lft forever preferred_lft forever

3: enp0s8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    inet 192.168.57.10/24 brd 192.168.57.255 scope global enp0s8
       valid_lft forever preferred_lft forever
```

`valid_lft forever` confirms permanent static IPs (not DHCP leases).

---

## Step 3: Enable systemd-networkd

If `netplan apply` reports `systemd-networkd is not running`, enable it:

```bash
sudo systemctl enable systemd-networkd
sudo systemctl start systemd-networkd
sudo netplan apply
```

---

## Step 4: Fix DNS Resolution

### Troubleshooting: "Temporary failure in name resolution"

If DNS fails after setting a static IP with no gateway, the VM has no route to the internet. Verify with:

```bash
ping 8.8.8.8   # Tests internet connectivity (no DNS needed)
ping google.com # Tests DNS resolution
ip route show   # Check for a default route
```

**No default route** means the gateway is missing from Netplan. Ensure the `routes` block is present in `enp0s3` (see Step 2.3).

After adding the gateway and applying Netplan:

```bash
sudo netplan apply
ping 8.8.8.8
ping google.com
```

---

## Step 5: SSH Server Setup

### 5.1 Install OpenSSH Server

```bash
sudo apt update
sudo apt install openssh-server -y
```

### 5.2 Enable and Start SSH

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

### 5.3 Connect from Host

```bash
ssh lab@192.168.57.10
```

---

## Step 6: Install Analysis Tools

### 6.1 Install tshark, Wireshark, and Suricata

```bash
sudo apt install tshark wireshark suricata -y
```

When prompted: **"Should non-superusers be able to capture packets?"** → Select **Yes**

### 6.2 Add User to Wireshark Group

```bash
sudo usermod -aG wireshark lab
```

Log out and back in for the group change to take effect:

```bash
exit
ssh lab@192.168.57.10
```

### 6.3 Update Suricata Rules

```bash
sudo suricata-update
```

### 6.4 Verify Installations

```bash
tshark --version
suricata --version
wireshark --version
```

---

## Step 7: Troubleshooting — AppArmor Blocking tshark

### Symptom

```
tshark: You don't have permission to read the file "file.pcap".
```

Even as root, even with correct file permissions (`-rw-r--r-- 1 lab lab`).

### Diagnosis

```bash
sudo dmesg | grep tshark | tail -10
```

**Output confirming AppArmor block:**

```
apparmor="DENIED" operation="open" class="file" profile="tshark"
name="/home/lab/pcaps/file.pcap" requested_mask="r" denied_mask="r"
```

### Fix

```bash
sudo apt install apparmor-utils -y
sudo aa-disable /etc/apparmor.d/tshark
```

---

## Step 8: Connect VM to PrivateGPT

### 8.1 Verify PrivateGPT is Listening on All Interfaces (Host)

```bash
ss -tlnp | grep 8001
```

**Expected output:**

```
LISTEN 0  2048  0.0.0.0:8001  0.0.0.0:*  users:(("python",pid=5212,fd=22))
```

`0.0.0.0` means it's listening on all interfaces including `192.168.57.1`.

### 8.2 Allow Port 8001 Through Host Firewall

```bash
sudo ufw allow from 192.168.57.0/24 to any port 8001
sudo ufw status
```

### 8.3 Test from VM

```bash
curl http://192.168.57.1:8001/
```

A Gradio HTML response confirms connectivity.

---

## Step 9: Download and Analyze PCAPs

### 9.1 Zip Password Scheme

PCAPs on malware-traffic-analysis.net are password-protected. The password format is:

```
infected_YYYYMMDD
```

For example, a PCAP posted on January 22, 2025:

```
infected_20250122
```

### 9.2 Download a PCAP

```bash
mkdir ~/pcaps && cd ~/pcaps
wget https://www.malware-traffic-analysis.net/2025/01/22/2025-01-22-traffic-analysis-exercise.pcap.zip
```

### 9.3 Extract the PCAP

```bash
unzip -P 'infected_20250122' 2025-01-22-traffic-analysis-exercise.pcap.zip
chmod 644 2025-01-22-traffic-analysis-exercise.pcap
```

### 9.4 Extract IOCs with tshark

**DNS queries:**

```bash
tshark -r ~/pcaps/2025-01-22-traffic-analysis-exercise.pcap \
  -Y dns.flags.response==0 \
  -T fields -e dns.qry.name 2>/dev/null | sort -u
```

**External IPs (excluding RFC1918):**

```bash
tshark -r ~/pcaps/2025-01-22-traffic-analysis-exercise.pcap \
  -T fields -e ip.dst 2>/dev/null \
  | grep -v '^10\.' | grep -v '^192\.168\.' | grep -v '^172\.' \
  | sort -u
```

**HTTP requests:**

```bash
tshark -r ~/pcaps/2025-01-22-traffic-analysis-exercise.pcap \
  -Y http.request \
  -T fields -e ip.dst -e http.host -e http.request.uri 2>/dev/null | sort -u
```

**Save all IOCs to file:**

```bash
tshark -r ~/pcaps/2025-01-22-traffic-analysis-exercise.pcap \
  -Y http.request \
  -T fields -e ip.dst -e http.host -e http.request.uri 2>/dev/null \
  | sort -u > ~/pcaps/iocs.txt

tshark -r ~/pcaps/2025-01-22-traffic-analysis-exercise.pcap \
  -Y dns.flags.response==0 \
  -T fields -e dns.qry.name 2>/dev/null \
  | sort -u >> ~/pcaps/iocs.txt
```

### 9.5 Send IOCs to PrivateGPT

```bash
curl -X POST http://192.168.57.1:8001/run/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": ["Analyze these network IOCs from a malware PCAP and identify the threat, malware family, and TTPs:\n\nC2 Server: 5.252.153.241\nConnections to: /1517096937, /api/file/get-file/29842.ps1, /api/file/get-file/pas.ps1, /api/file/get-file/TeamViewer\nStatus callbacks: startup shortcut created, PS process started\nInfected host: DESKTOP-L8C5GSJ (10.1.17.215)\nDomain: bluemoontuesday.com"]
  }'
```

---

## Step 10: VirtualBox Shared Folder (Optional)

For sharing analysis results between VM and host without network:

### 10.1 Configure in VirtualBox

1. VM Settings → **Shared Folders** → click **+**
2. Set Folder Path to a host directory (e.g. `~/shared_analysis`)
3. Set Folder Name to `shared`
4. Check **Auto-mount**

### 10.2 Install Guest Utilities on VM

```bash
sudo apt install virtualbox-guest-utils -y
sudo reboot
```

### 10.3 Mount the Shared Folder

```bash
sudo mkdir -p /mnt/shared
sudo mount -t vboxsf shared /mnt/shared
```

**Persistent mount via fstab:**

```bash
echo "shared  /mnt/shared  vboxsf  defaults,uid=1000,gid=1000  0  0" | sudo tee -a /etc/fstab
sudo mount -a
```

### 10.4 Cleanup

```bash
# VM
sudo umount /mnt/shared

# Host
sudo ufw delete allow from 192.168.57.0/24 to any port 8001
rm -rf ~/shared_analysis
```

---

## IOC Analysis — Example Findings

From the 2025-01-22 exercise PCAP:

| IOC | Type | Notes |
|---|---|---|
| `5.252.153.241` | C2 Server | PowerShell downloads, status callbacks |
| `/api/file/get-file/29842.ps1` | Malicious PS1 | Downloaded from C2 |
| `/api/file/get-file/pas.ps1` | Malicious PS1 | Downloaded from C2 |
| `/api/file/get-file/TeamViewer` | RAT component | Likely for remote access |
| `startup shortcut created` | Persistence | Registry/startup persistence |
| `DESKTOP-L8C5GSJ` | Infected Host | IP: 10.1.17.215 |
| `bluemoontuesday.com` | AD Domain | Internal domain |
| `win-gsh54qlw48d` | Domain Controller | IP: 10.1.17.2 |

**Malware behavior:** C2 beaconing → PowerShell execution → TeamViewer deployment → persistence via startup shortcut. Consistent with a RAT/stealer infection pattern.

---

## Security Considerations

- **Isolated network:** The host-only adapter (`vboxnet1`) keeps VM traffic off the main LAN.
- **No internet on host-only:** `enp0s8` has no gateway — it cannot route to the internet.
- **PCAP handling:** Never open PCAPs or extracted malware samples on a Windows host — risk of infection.
- **AppArmor:** Keep AppArmor enabled system-wide. Only disable the `tshark` profile, not globally.
- **UFW rules:** Scope firewall rules to `192.168.57.0/24` only — never open port 8001 to `Anywhere`.
- **PrivateGPT:** Runs locally — no data leaves the host machine.
- **Zip passwords:** PCAPs are password-protected to prevent accidental execution by antivirus.

---

## Verification Checklist

- [ ] `enp0s3` shows `inet 10.10.10.24/24 ... valid_lft forever`
- [ ] `enp0s8` shows `inet 192.168.57.10/24 ... valid_lft forever`
- [ ] `ping 8.8.8.8` succeeds from VM
- [ ] `ping google.com` succeeds from VM (DNS working)
- [ ] `ping 192.168.57.10` succeeds from host
- [ ] `ssh lab@192.168.57.10` connects successfully
- [ ] `tshark --version` returns without errors
- [ ] `suricata --version` returns without errors
- [ ] `curl http://192.168.57.1:8001/` returns Gradio HTML from VM
- [ ] PCAP downloads and extracts successfully with `infected_YYYYMMDD` password
- [ ] `tshark -r file.pcap` reads packets without permission errors
- [ ] IOC extraction commands return results
- [ ] PrivateGPT responds to curl POST from VM
