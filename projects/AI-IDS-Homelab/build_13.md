# AI-Powered Intrusion Detection System (AI-IDS) Homelab

## Overview

This document is a complete step-by-step build guide for deploying an AI-powered Intrusion Detection System (AI-IDS) inside a KVM/virt-manager virtual lab on a Linux Mint host. The lab consists of two virtual machines:

- **sentinel** — Xubuntu 24.04 VM running a Python-based IDS with a Flask API and Streamlit dashboard
- **openwrt** — OpenWRT 25.12.4 VM acting as a virtual router with Multi-WAN failover via mwan3

Traffic from sentinel is routed through OpenWRT, allowing the AI-IDS to monitor real network traffic in a controlled lab environment.

---

## Environment

| Component | Details |
|-----------|---------|
| Host OS | Linux Mint (Ubuntu 24.04 base) |
| CPU | 12th Gen Intel Core i7-12700F (40 logical cores) |
| RAM | 32GB |
| Hypervisor | KVM/QEMU via virt-manager |
| sentinel OS | Xubuntu 24.04.4 LTS |
| OpenWRT Version | 25.12.4 |
| Python Version | 3.12 |
| Flask | 3.1.3 |
| Streamlit | 1.58.0 |
| scikit-learn | 1.9.0 |

### Network Configuration

```
Internet
    ↕
Linux Mint Host (10.99.99.1)
    ↕ nat-lab (10.99.99.0/24) — NAT network with DHCP
OpenWRT WAN (10.99.99.146)
    ↕
OpenWRT LAN (192.168.1.1)
    ↕ isolated-lab (192.168.1.0/24) — isolated internal network
sentinel (192.168.1.192)
    ├── Flask API      → port 5000
    └── Streamlit Dashboard → port 8501
```

---

## Directory Structure

```
ai-ids/
├── models/              # Saved trained models
├── data/                # Datasets and synthetic data
├── logs/                # Retraining logs
├── scripts/
│   ├── train_model.py   # Initial model training
│   ├── retrain_model.py # Scheduled retraining
│   ├── app.py           # Flask prediction API
│   ├── dashboard.py     # Streamlit dashboard
│   └── generate_data.py # Synthetic dataset generator
└── venv/                # Python virtual environment
```

---

## Step 1: Remove VirtualBox and Prepare the Host

### Why
VirtualBox kernel modules conflict with KVM. They must be unloaded before installing virt-manager.

### Check for running VirtualBox modules

```bash
lsmod | grep vbox
```

**Expected output if VirtualBox is running:**
```
vboxnetadp   28672  0
vboxnetflt   40960  1
vboxdrv     712704  6 vboxnetadp,vboxnetflt
```

### Kill any running VirtualBox processes

```bash
sudo pkill -f virtualbox
```

```bash
sudo pkill -f VBoxSVC
```

```bash
sudo pkill -f VBoxXPCOMIPCD
```

### Unload VirtualBox kernel modules

```bash
sudo modprobe -r vboxnetadp vboxnetflt vboxdrv
```

### Verify modules are unloaded

```bash
lsmod | grep vbox
```

**Expected output:** nothing (empty)

### Remove VirtualBox completely

```bash
sudo apt remove --purge virtualbox* -y
```

```bash
sudo apt autoremove -y
```

---

## Step 2: Verify KVM Support

### Why
KVM (Kernel-based Virtual Machine) provides near-native virtualization performance. Must be supported by the CPU and enabled in the kernel.

### Check CPU virtualization support

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo
```

**Expected output:** any number greater than 0 (e.g. `40`)

### Install cpu-checker and verify KVM

```bash
sudo apt install cpu-checker -y
```

```bash
kvm-ok
```

**Expected output:**
```
INFO: /dev/kvm exists
KVM acceleration can be used
```

### Check available RAM

```bash
free -h
```

---

## Step 3: Install virt-manager and KVM

### Why
virt-manager provides a GUI for managing KVM virtual machines. It uses the same KVM technology as Proxmox but runs alongside your existing desktop OS.

### Install all required packages

```bash
sudo apt update
```

```bash
sudo apt install -y virt-manager qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst
```

### Add your user to required groups

```bash
sudo usermod -aG libvirt $USER
```

```bash
sudo usermod -aG kvm $USER
```

### Reboot to apply group changes

```bash
sudo reboot
```

### Verify libvirt is running after reboot

```bash
virsh list --all
```

**Expected output:** empty list with no errors

---

## Step 4: Enable KVM Kernel Module

### Why
The KVM Intel module must be loaded for hardware-accelerated virtualization. Without it, VMs run much slower using software emulation.

### Check CPU model

```bash
cat /proc/cpuinfo | grep "model name" | head -1
```

### Load KVM module (Intel CPU)

```bash
sudo modprobe kvm_intel
```

### Verify KVM device exists

```bash
ls -la /dev/kvm
```

**Expected output:**
```
crw-rw----+ 1 root kvm 10, 232 Jun 12 03:35 /dev/kvm
```

### Make KVM module load permanently on every boot

```bash
echo 'kvm_intel' | sudo tee /etc/modules-load.d/kvm.conf
```

---

## Step 5: Configure Virtual Networks

### Why
Two virtual networks are needed — one for NAT internet access (nat-lab) and one for isolated VM-to-VM communication (isolated-lab).

### Check existing networks

```bash
sudo virsh net-list --all
```

**Expected output showing existing networks:**
```
 Name           State    Autostart   Persistent
-------------------------------------------------
 isolated-lab   active   yes         yes
 nat-lab        active   yes         yes
```

### Start networks if inactive

```bash
sudo virsh net-start nat-lab
```

```bash
sudo virsh net-start isolated-lab
```

### Verify nat-lab DHCP configuration

```bash
sudo virsh net-dumpxml nat-lab
```

**Expected DHCP range:** `10.99.99.100` to `10.99.99.200`

---

## Step 6: Create the sentinel VM (Xubuntu AI-IDS)

### Why
sentinel is the VM that runs the AI-IDS project — Flask API, Streamlit dashboard, and the trained machine learning model.

### Download Xubuntu 24.04.4 LTS ISO

```bash
wget -P ~/Downloads https://cdimage.ubuntu.com/xubuntu/releases/24.04/release/xubuntu-24.04.4-desktop-amd64.iso
```

### Verify ISO is present

```bash
ls ~/Downloads/*.iso
```

### Create the VM using virt-install

```bash
virt-install \
  --name sentinel \
  --ram 8192 \
  --vcpus 4 \
  --disk path=/var/lib/libvirt/images/sentinel.qcow2,size=40 \
  --cdrom /home/chris/Downloads/xubuntu-24.04.4-desktop-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=nat-lab \
  --graphics spice \
  --video qxl \
  --boot cdrom,hd
```

**Note:** The VM name in virsh shows as `xubuntu-ai-ids` due to OS detection.

### Install Xubuntu inside the VM

Follow the graphical installer:
1. Select **Install Xubuntu**
2. Choose **Erase disk and install**
3. Set username and password
4. Wait for installation to complete
5. Reboot when prompted

### Install SPICE guest tools for copy/paste support

Run inside the Xubuntu VM:

```bash
sudo apt install spice-vdagent -y
```

### Verify network connectivity inside sentinel

```bash
ping -c 3 google.com
```

---

## Step 7: Set Up AI-IDS Project Inside sentinel

### Why
The AI-IDS project uses Python, scikit-learn, Flask, and Streamlit to detect network intrusions using a trained Random Forest classifier.

### Update the system

```bash
sudo apt update && sudo apt upgrade -y
```

### Create project directory structure

```bash
cd ~
```

```bash
mkdir ai-ids
```

```bash
cd ai-ids
```

```bash
mkdir -p models data logs scripts
```

### Create Python virtual environment

```bash
python3 -m venv venv
```

### Activate virtual environment

```bash
source venv/bin/activate
```

**Verification:** prompt should show `(venv)` prefix

### Install all Python dependencies

```bash
pip install scikit-learn pandas numpy flask requests joblib streamlit
```

---

## Step 8: Create AI-IDS Scripts

### scripts/generate_data.py — Synthetic Dataset Generator

```bash
nano scripts/generate_data.py
```

```python
import pandas as pd
import numpy as np

np.random.seed(42)

# Normal traffic (8000 samples)
normal = pd.DataFrame({
    'Flow Duration': np.random.randint(0, 100000, 8000),
    'Total Fwd Packets': np.random.randint(1, 50, 8000),
    'Total Backward Packets': np.random.randint(1, 50, 8000),
    'Total Length of Fwd Packets': np.random.randint(0, 5000, 8000),
    'Total Length of Bwd Packets': np.random.randint(0, 5000, 8000),
    'Fwd Packet Length Max': np.random.randint(0, 1500, 8000),
    'Bwd Packet Length Max': np.random.randint(0, 1500, 8000),
    'Flow Bytes/s': np.random.uniform(0, 10000, 8000),
    'Flow Packets/s': np.random.uniform(0, 100, 8000),
    'Label': 'BENIGN'
})

# DDoS traffic (2000 samples)
ddos = pd.DataFrame({
    'Flow Duration': np.random.randint(0, 1000, 2000),
    'Total Fwd Packets': np.random.randint(100, 1000, 2000),
    'Total Backward Packets': np.random.randint(0, 5, 2000),
    'Total Length of Fwd Packets': np.random.randint(5000, 50000, 2000),
    'Total Length of Bwd Packets': np.random.randint(0, 100, 2000),
    'Fwd Packet Length Max': np.random.randint(1000, 1500, 2000),
    'Bwd Packet Length Max': np.random.randint(0, 100, 2000),
    'Flow Bytes/s': np.random.uniform(100000, 1000000, 2000),
    'Flow Packets/s': np.random.uniform(1000, 10000, 2000),
    'Label': 'DDoS'
})

data = pd.concat([normal, ddos]).sample(frac=1).reset_index(drop=True)
data.to_csv('data/cicids_sample.csv', index=False)
print(f"Dataset generated: {len(data)} samples")
print(data['Label'].value_counts())
```

### scripts/train_model.py — Model Training

```bash
nano scripts/train_model.py
```

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

data = pd.read_csv("data/cicids_sample.csv")
X = data.drop(columns=["Label"])
y = data["Label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=50, n_jobs=-1, random_state=42)
model.fit(X_train, y_train)

os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/ids_model.pkl")

print("Model trained and saved to models/ids_model.pkl")
```

### scripts/app.py — Flask Prediction API

```bash
nano scripts/app.py
```

```python
from flask import Flask, request, jsonify
import joblib
import pandas as pd
import os

app = Flask(__name__)

model_path = os.path.join(os.path.dirname(__file__), "../models/ids_model.pkl")
model = joblib.load(model_path)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    features = pd.DataFrame([data["features"]])
    prediction = model.predict(features)[0]
    return jsonify({"prediction": str(prediction)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### scripts/retrain_model.py — Scheduled Retraining

```bash
nano scripts/retrain_model.py
```

```python
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
import os
from datetime import datetime

data = pd.read_csv("data/cicids_sample.csv")
X = data.drop(columns=["Label"])
y = data["Label"]

model = RandomForestClassifier(n_estimators=50, n_jobs=-1, random_state=42)
model.fit(X, y)

os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/ids_model.pkl")

os.makedirs("logs", exist_ok=True)
with open("logs/retrain_log.txt", "a") as f:
    f.write(f"Retrained at {datetime.now()}\n")

print("Model retrained successfully!")
```

### scripts/dashboard.py — Streamlit Dashboard

```bash
nano scripts/dashboard.py
```

```python
import streamlit as st
import pandas as pd
from datetime import datetime

st.title("AI-Powered IDS Dashboard")

if "alerts" not in st.session_state:
    st.session_state.alerts = []

with st.form("alert_form"):
    source_ip = st.text_input("Source IP")
    attack_type = st.selectbox("Attack Type", ["Port Scan", "DDoS", "Brute Force", "Benign"])
    threat_score = st.slider("Threat Score", 0, 100, 50)
    submitted = st.form_submit_button("Add Alert")

    if submitted:
        alert = {
            "timestamp": datetime.now().isoformat(),
            "source_ip": source_ip,
            "attack_type": attack_type,
            "threat_score": threat_score
        }
        st.session_state.alerts.append(alert)

st.subheader("Recent Alerts")
if st.session_state.alerts:
    df = pd.DataFrame(st.session_state.alerts)
    st.dataframe(df)
else:
    st.write("No alerts yet.")
```

---

## Step 9: Generate Data, Train Model, and Run Services

### Generate synthetic dataset

```bash
python scripts/generate_data.py
```

**Expected output:**
```
Dataset generated: 10000 samples
Label
BENIGN    8000
DDoS      2000
```

### Train the model

```bash
python scripts/train_model.py
```

**Expected output:**
```
Model trained and saved to models/ids_model.pkl
```

### Start Flask API (Terminal 1)

```bash
python scripts/app.py
```

**Expected output:**
```
 * Running on http://0.0.0.0:5000
 * Running on http://10.99.99.198:5000
 * Debug mode: on
```

### Test Flask API (Terminal 2)

```bash
curl -X POST http://localhost:5000/predict \
-H "Content-Type: application/json" \
-d '{"features": {"Flow Duration": 1000, "Total Fwd Packets": 500, "Total Backward Packets": 2, "Total Length of Fwd Packets": 25000, "Total Length of Bwd Packets": 50, "Fwd Packet Length Max": 1200, "Bwd Packet Length Max": 50, "Flow Bytes/s": 500000, "Flow Packets/s": 5000}}'
```

**Expected output:**
```json
{"prediction": "DDoS"}
```

### Start Streamlit Dashboard (Terminal 3)

```bash
streamlit run scripts/dashboard.py --server.port 8501 --server.address 0.0.0.0
```

**Access dashboard at:** `http://localhost:8501`

---

## Step 10: Create the OpenWRT VM

### Why
OpenWRT acts as the virtual router, providing NAT, DHCP for the isolated lab network, and Multi-WAN failover via mwan3.

### Download OpenWRT 25.12.4 x86-64 image (on Linux Mint host)

```bash
wget -P ~/Downloads https://downloads.openwrt.org/releases/25.12.4/targets/x86/64/openwrt-25.12.4-x86-64-generic-ext4-combined.img.gz
```

### Extract the image

```bash
cd ~/Downloads
```

```bash
gunzip openwrt-25.12.4-x86-64-generic-ext4-combined.img.gz
```

### Convert to qcow2 format for KVM

```bash
sudo qemu-img convert -f raw \
  ~/Downloads/openwrt-25.12.4-x86-64-generic-ext4-combined.img \
  -O qcow2 /var/lib/libvirt/images/openwrt.qcow2
```

### Create the OpenWRT VM

```bash
virt-install \
  --name openwrt \
  --ram 512 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/openwrt.qcow2,size=1 \
  --import \
  --os-variant linux2022 \
  --network network=nat-lab,model=virtio \
  --network network=isolated-lab,model=virtio \
  --graphics spice \
  --video qxl \
  --boot hd
```

### Access OpenWRT console

Press **Enter** when prompted to activate the console.

**Expected prompt:**
```
root@OpenWrt:/#
```

---

## Step 11: Configure OpenWRT Networking

### Why
By default OpenWRT puts eth0 into a bridge (br-lan). We need eth0 as WAN (nat-lab) and eth1 as LAN (isolated-lab).

### Set root password (required for SSH)

```bash
passwd
```

### Start SSH service

```bash
/etc/init.d/dropbear start
```

### Get temporary IP for SSH access

```bash
udhcpc -i br-lan
```

### Check IP assigned

```bash
ip a show br-lan
```

### SSH into OpenWRT from Linux Mint host

```bash
ssh root@10.99.99.145
```

### Configure WAN and LAN interfaces

```bash
uci set network.wan=interface
uci set network.wan.device='eth0'
uci set network.wan.proto='dhcp'
uci set network.lan.device='eth1'
uci set network.lan.proto='static'
uci set network.lan.ipaddr='192.168.1.1'
uci set network.lan.netmask='255.255.255.0'
uci commit network
/etc/init.d/network restart
```

### Verify WAN got an IP

```bash
ip a show eth0
```

**Expected output:** `inet 10.99.99.146/24`

### Verify internet connectivity

```bash
ping -c 3 8.8.8.8
```

```bash
ping -c 3 google.com
```

---

## Step 12: Install and Configure mwan3 Failover

### Why
mwan3 provides Multi-WAN failover. If the primary WAN goes down, traffic automatically switches to a backup connection.

### Install mwan3 using apk (OpenWRT 25.x uses apk instead of opkg)

```bash
apk update && apk add mwan3 luci-app-mwan3
```

### Write clean mwan3 configuration

```bash
cat > /etc/config/mwan3 << 'EOF'
config globals 'globals'
	option mmx_mask '0x3F00'

config interface 'wan'
	option enabled '1'
	option initial_state 'online'
	option family 'ipv4'
	list track_ip '8.8.8.8'
	list track_ip '1.1.1.1'
	option reliability '1'
	option count '1'
	option timeout '2'
	option interval '5'
	option down '3'
	option up '8'
	option track_method 'ping'

config member 'wan_m1'
	option interface 'wan'
	option metric '1'
	option weight '1'

config policy 'wan_only'
	list use_member 'wan_m1'

config rule 'default_rule_v4'
	option dest_ip '0.0.0.0/0'
	option use_policy 'wan_only'
	option family 'ipv4'
EOF
```

### Enable and start mwan3

```bash
/etc/init.d/mwan3 enable
```

```bash
/etc/init.d/mwan3 restart
```

### Verify mwan3 status

```bash
mwan3 status
```

**Expected output:**
```
interface wan is online and tracking is active
wan (100%)
```

---

## Step 13: Connect sentinel to OpenWRT LAN

### Why
Adding sentinel to the isolated-lab network allows it to communicate with OpenWRT's LAN side and route traffic through the virtual router.

### Add isolated-lab interface to sentinel VM (on Linux Mint host)

```bash
sudo virsh attach-interface xubuntu-ai-ids \
  --type network \
  --source isolated-lab \
  --model virtio \
  --live \
  --persistent
```

### Verify new interface inside sentinel

```bash
ip a
```

**Expected:** new interface `enp7s0` with IP `192.168.1.x`

### Test connectivity to OpenWRT LAN

```bash
ping -c 3 192.168.1.1
```

### Add OpenWRT as default gateway for sentinel

```bash
sudo ip route add default via 192.168.1.1 dev enp7s0 metric 50
```

### Verify traffic routes through OpenWRT

```bash
ping -c 3 8.8.8.8
```

**Verification:** TTL should be 108 (one hop lower than direct), confirming routing through OpenWRT.

---

## Step 14: Save VM Snapshots

### Why
Snapshots save your working state so you can restore if something breaks later.

### Snapshot sentinel

```bash
sudo virsh snapshot-create-as xubuntu-ai-ids "AI-IDS-Working" "Flask+Streamlit+Routing working"
```

### Snapshot OpenWRT

```bash
sudo virsh snapshot-create-as openwrt "OpenWRT-Working" "mwan3+routing working"
```

---

## Troubleshooting

### Problem 1: VirtualBox modules won't unload

**Symptoms:**
```
modprobe: FATAL: Module vboxnetflt is in use.
```

**Resolution:** Kill all VirtualBox processes first:

```bash
sudo pkill -f virtualbox
```

```bash
sudo pkill -f VBoxSVC
```

```bash
sudo pkill -f VBoxXPCOMIPCD
```

```bash
sudo modprobe -r vboxnetadp vboxnetflt vboxdrv
```

---

### Problem 2: KVM device not found

**Symptoms:**
```
WARNING: KVM acceleration not available, using 'qemu'
ls: cannot access '/dev/kvm': No such file or directory
```

**Resolution:**

```bash
sudo modprobe kvm_intel
```

```bash
echo 'kvm_intel' | sudo tee /etc/modules-load.d/kvm.conf
```

---

### Problem 3: Default network not found

**Symptoms:**
```
ERROR: Network not found: no network with matching name 'default'
```

**Resolution:** Use existing networks instead:

```bash
sudo virsh net-list --all
```

Use `nat-lab` instead of `default` in virt-install commands.

---

### Problem 4: Flask returns ValueError on prediction

**Symptoms:**
```
ValueError: invalid literal for int() with base 10: 'DDoS'
```

**Resolution:** Change `int(prediction)` to `str(prediction)` in `scripts/app.py`:

```python
return jsonify({"prediction": str(prediction)})
```

---

### Problem 5: mwan3 shows all interfaces unreachable

**Symptoms:**
```
interface wan is offline and tracking is disabled
```

**Resolution:** Rewrite mwan3 config cleanly using `cat >` instead of individual `uci set` commands. Ensure `track_ip` uses `list` format not `option` format.

---

### Problem 6: OpenWRT network restart hangs

**Symptoms:** Terminal hangs after running `service network restart`

**Resolution:** Use `/etc/init.d/network restart` instead, or reboot:

```bash
reboot
```

---

### Problem 7: Cannot SSH into OpenWRT after reboot

**Symptoms:**
```
ssh: connect to host 10.99.99.145 port 22: No route to host
```

**Resolution:** Check current DHCP leases for new IP:

```bash
sudo virsh net-dhcp-leases nat-lab
```

---

### Problem 8: Streamlit shows "unable to connect"

**Symptoms:** Browser shows connection refused on port 8501

**Resolution:** Run with explicit address binding:

```bash
streamlit run scripts/dashboard.py --server.port 8501 --server.address 0.0.0.0
```

---

## Build Verification Checklist

### Host Setup
- [ ] VirtualBox removed and modules unloaded
- [ ] KVM module loaded (`ls -la /dev/kvm` shows device)
- [ ] virt-manager installed and running
- [ ] User added to `kvm` and `libvirt` groups
- [ ] nat-lab and isolated-lab networks active

### sentinel VM (AI-IDS)
- [ ] Xubuntu 24.04.4 installed and booting
- [ ] Python venv created and activated
- [ ] All pip packages installed
- [ ] Synthetic dataset generated (10,000 samples)
- [ ] Model trained and saved to `models/ids_model.pkl`
- [ ] Flask API running on port 5000
- [ ] Flask returns `{"prediction": "DDoS"}` on test curl
- [ ] Streamlit dashboard accessible at port 8501
- [ ] SPICE guest tools installed for copy/paste

### OpenWRT VM
- [ ] OpenWRT 25.12.4 booting from qcow2
- [ ] eth0 (WAN) gets IP from nat-lab (`10.99.99.x`)
- [ ] eth1 (LAN) has static IP `192.168.1.1`
- [ ] Can ping `8.8.8.8` and `google.com` from OpenWRT
- [ ] mwan3 installed via apk
- [ ] mwan3 status shows `wan is online and tracking is active`
- [ ] SSH accessible via dropbear

### Network Integration
- [ ] sentinel has `enp7s0` interface on isolated-lab (`192.168.1.x`)
- [ ] sentinel can ping OpenWRT LAN (`192.168.1.1`)
- [ ] sentinel traffic routes through OpenWRT (TTL=108 to 8.8.8.8)
- [ ] VM snapshots saved for both VMs

---

## Quick Start Commands

Use these commands to rebuild the project from scratch.

### On Linux Mint Host

```bash
sudo apt install -y virt-manager qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst
sudo usermod -aG libvirt,kvm $USER
sudo modprobe kvm_intel
echo 'kvm_intel' | sudo tee /etc/modules-load.d/kvm.conf
```

### Create OpenWRT VM

```bash
wget -P ~/Downloads https://downloads.openwrt.org/releases/25.12.4/targets/x86/64/openwrt-25.12.4-x86-64-generic-ext4-combined.img.gz
gunzip ~/Downloads/openwrt-25.12.4-x86-64-generic-ext4-combined.img.gz
sudo qemu-img convert -f raw ~/Downloads/openwrt-25.12.4-x86-64-generic-ext4-combined.img -O qcow2 /var/lib/libvirt/images/openwrt.qcow2
virt-install --name openwrt --ram 512 --vcpus 2 --disk path=/var/lib/libvirt/images/openwrt.qcow2,size=1 --import --os-variant linux2022 --network network=nat-lab,model=virtio --network network=isolated-lab,model=virtio --graphics spice --video qxl --boot hd
```

### Create sentinel VM

```bash
virt-install --name sentinel --ram 8192 --vcpus 4 --disk path=/var/lib/libvirt/images/sentinel.qcow2,size=40 --cdrom ~/Downloads/xubuntu-24.04.4-desktop-amd64.iso --os-variant ubuntu24.04 --network network=nat-lab --graphics spice --video qxl --boot cdrom,hd
```

### Inside sentinel VM

```bash
cd ~ && mkdir ai-ids && cd ai-ids && mkdir -p models data logs scripts
python3 -m venv venv
source venv/bin/activate
pip install scikit-learn pandas numpy flask requests joblib streamlit
python scripts/generate_data.py
python scripts/train_model.py
python scripts/app.py &
streamlit run scripts/dashboard.py --server.port 8501 --server.address 0.0.0.0 &
```

### Connect sentinel to OpenWRT (on Linux Mint host)

```bash
sudo virsh attach-interface xubuntu-ai-ids --type network --source isolated-lab --model virtio --live --persistent
```

### Inside sentinel — route through OpenWRT

```bash
sudo ip route add default via 192.168.1.1 dev enp7s0 metric 50
```

---

## Lessons Learned

### Linux & KVM
- VirtualBox and KVM cannot coexist — kernel modules must be unloaded before switching
- KVM modules (`kvm_intel`) must be loaded manually after install and persisted via `/etc/modules-load.d/`
- `virsh net-dhcp-leases` is invaluable for finding VM IPs after reboots
- VM names in virsh may differ from hostnames set during OS install

### Networking
- Virtual networks in libvirt are independent — VMs on different networks cannot communicate without bridging or routing
- OpenWRT's default config puts all interfaces into `br-lan` — must be reconfigured for WAN/LAN separation
- TTL reduction (109→108) confirms traffic is routing through an intermediate hop
- SSH into VMs via their NAT IP makes copy/paste much easier than using the console window

### Python & AI-IDS
- scikit-learn classifiers return the original label type — use `str()` not `int()` when labels are strings like `'DDoS'`
- Synthetic data is sufficient for testing the full pipeline before real datasets are available
- Streamlit requires explicit `--server.address 0.0.0.0` to be accessible outside localhost

### OpenWRT
- OpenWRT 25.x uses `apk` instead of `opkg` for package management
- mwan3 `track_ip` must use `list` format in config files, not `option` format
- Writing config files with `cat >` is more reliable than chaining multiple `uci set` commands
- `dropbear` SSH must be started manually on first boot

---

*Generated from live build session — June 12, 2026*

---

## Step 15: Install and Configure LuCI Web Interface

### Why
LuCI is OpenWRT's web-based management interface. It provides a graphical dashboard for monitoring network status, managing firewall rules, viewing connected clients, and configuring Multi-WAN failover — essential for both blue team defense and understanding what attackers see.

### SSH into OpenWRT from Linux Mint host

```bash
ssh root@10.99.99.146
```

### Install LuCI

```bash
apk update
```

```bash
apk add luci
```

### Start the web server

```bash
/etc/init.d/uhttpd start
```

### Enable autostart on boot

```bash
/etc/init.d/dropbear enable
```

```bash
/etc/init.d/uhttpd enable
```

### Verify both services are running

```bash
netstat -tlnp | grep -E '22|80|443'
```

**Expected output:**
```
tcp   0   0 0.0.0.0:22    0.0.0.0:*   LISTEN   dropbear
tcp   0   0 0.0.0.0:80    0.0.0.0:*   LISTEN   uhttpd
tcp   0   0 0.0.0.0:443   0.0.0.0:*   LISTEN   uhttpd
```

---

## Step 16: Open Firewall for SSH and LuCI Access

### Why
OpenWRT's default WAN zone has `input REJECT` — this blocks SSH (port 22) and HTTP (port 80) from the host machine. We must explicitly allow these ports.

### Allow SSH from WAN

```bash
uci add firewall rule
uci set firewall.@rule[-1].name='Allow-SSH-WAN'
uci set firewall.@rule[-1].src='wan'
uci set firewall.@rule[-1].dest_port='22'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].target='ACCEPT'
uci commit firewall
```

### Allow HTTP (LuCI) from WAN

```bash
uci add firewall rule
uci set firewall.@rule[-1].name='Allow-HTTP-WAN'
uci set firewall.@rule[-1].src='wan'
uci set firewall.@rule[-1].dest_port='80'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].target='ACCEPT'
uci commit firewall
```

### Apply firewall changes

```bash
/etc/init.d/firewall restart
```

### Access LuCI from Linux Mint browser

Open Firefox or Chromium and navigate to:

```
http://10.99.99.146
```

Login with:
- **Username:** `root`
- **Password:** your OpenWRT root password

**Expected:** LuCI dashboard loads showing system status, network interfaces, and connected clients.

---

## LuCI Dashboard Overview

### Key sections for Blue Team lab work

| Menu | Purpose |
|------|---------|
| **Status → Overview** | System info, network status, connected clients |
| **Status → Realtime Graphs** | Live bandwidth, CPU, and connection graphs |
| **Network → Interfaces** | View and edit WAN/LAN configuration |
| **Network → Firewall** | Manage firewall zones and rules visually |
| **Network → Load Balancing** | mwan3 Multi-WAN failover management |
| **System → Software** | Install/remove packages via GUI |
| **System → Scheduled Tasks** | Cron job management |

---

## Troubleshooting: LuCI and SSH Access

### Problem: SSH connection refused despite dropbear running

**Symptoms:**
```
ssh: connect to host 10.99.99.146 port 22: Connection refused
```

**Root Cause:** OpenWRT WAN zone default policy is `REJECT`. SSH is blocked even when dropbear is listening.

**Resolution:** Add explicit firewall rule to allow SSH from WAN:

```bash
uci add firewall rule
uci set firewall.@rule[-1].name='Allow-SSH-WAN'
uci set firewall.@rule[-1].src='wan'
uci set firewall.@rule[-1].dest_port='22'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].target='ACCEPT'
uci commit firewall
/etc/init.d/firewall restart
```

---

### Problem: Browser can't connect to LuCI

**Symptoms:**
```
Firefox can't connect to the server at 10.99.99.146
```

**Root Cause:** Same WAN REJECT policy blocking port 80.

**Resolution:** Add explicit firewall rule to allow HTTP from WAN:

```bash
uci add firewall rule
uci set firewall.@rule[-1].name='Allow-HTTP-WAN'
uci set firewall.@rule[-1].src='wan'
uci set firewall.@rule[-1].dest_port='80'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].target='ACCEPT'
uci commit firewall
/etc/init.d/firewall restart
```

---

### Problem: dropbear and uhttpd don't start after reboot

**Resolution:** Enable autostart for both services:

```bash
/etc/init.d/dropbear enable
/etc/init.d/uhttpd enable
```

---

## Updated Build Verification Checklist

### LuCI Setup
- [ ] LuCI installed via `apk add luci`
- [ ] uhttpd running on ports 80 and 443
- [ ] dropbear running on port 22
- [ ] Both services enabled for autostart
- [ ] SSH accessible from Linux Mint host (`ssh root@10.99.99.146`)
- [ ] LuCI accessible in browser (`http://10.99.99.146`)
- [ ] Firewall rules added for SSH and HTTP from WAN
- [ ] LuCI dashboard loads and shows network status

---

## Updated Lessons Learned

### OpenWRT Firewall
- The default WAN zone policy is `REJECT` for input — always add explicit rules for any service you want accessible from outside the LAN
- Use `uci add firewall rule` followed by `uci set` commands to add rules programmatically
- Always run `/etc/init.d/firewall restart` after committing firewall changes
- LuCI provides a much friendlier interface for managing firewall rules once it's accessible

### Service Management
- OpenWRT services must be both `started` (for current session) and `enabled` (for autostart on boot)
- Use `netstat -tlnp` to verify which ports are actually listening before troubleshooting connectivity
- `dropbear` is OpenWRT's lightweight SSH server — not OpenSSH

---

*Updated — June 12, 2026*

---

## Step 17: Configure Blue/Red Team iptables Firewall Rules

### Why
For a proper blue/red team lab, we need strict firewall rules that:
- Allow only essential traffic (DNS, HTTP, HTTPS, SSH)
- Block everything else from outside the lab subnet
- Log all dropped packets so the AI-IDS can analyze attack attempts

This turns OpenWRT into a realistic security gateway that blue team defends and red team tries to bypass.

### Traffic Policy

| Traffic | Port | Protocol | Action |
|---------|------|----------|--------|
| SSH (lab management) | 22 | TCP | ✅ ACCEPT (subnet only) |
| DNS (name resolution) | 53 | UDP/TCP | ✅ ACCEPT (subnet only) |
| HTTP | 80 | TCP | ✅ ACCEPT (subnet only) |
| HTTPS | 443 | TCP | ✅ ACCEPT (subnet only) |
| DHCP | 67-68 | UDP | ✅ ACCEPT |
| Everything else | any | any | ❌ DROP + LOG |

### Step 1 — Add Log-Dropped-WAN rule via LuCI

In LuCI → Network → Firewall → Traffic Rules → **Add**:

| Field | Value |
|-------|-------|
| Name | `Log-Dropped-WAN` |
| Protocol | `Any` |
| Source zone | `wan` |
| Destination zone | `This device` |
| Action | `drop` |

Click **Save & Apply**

### Step 2 — Apply iptables rules via SSH

**Note:** OpenWRT 25.x uses `conntrack` instead of `state` for connection tracking.

```bash
iptables -F INPUT
```

```bash
iptables -F FORWARD
```

```bash
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

```bash
iptables -A INPUT -i lo -j ACCEPT
```

```bash
iptables -A INPUT -s 10.99.99.0/24 -p tcp --dport 22 -j ACCEPT
```

```bash
iptables -A INPUT -s 10.99.99.0/24 -p udp --dport 53 -j ACCEPT
```

```bash
iptables -A INPUT -s 10.99.99.0/24 -p tcp --dport 53 -j ACCEPT
```

```bash
iptables -A INPUT -s 10.99.99.0/24 -p tcp --dport 80 -j ACCEPT
```

```bash
iptables -A INPUT -s 10.99.99.0/24 -p tcp --dport 443 -j ACCEPT
```

```bash
iptables -A INPUT -p udp --dport 67:68 -j ACCEPT
```

```bash
iptables -A INPUT -j LOG --log-prefix "DROPPED: " --log-level 4
```

```bash
iptables -A INPUT -j DROP
```

### Step 3 — Save rules permanently

```bash
iptables-save > /etc/iptables.rules
```

### Step 4 — Restore rules on boot

```bash
cat > /etc/rc.local << 'EOF'
iptables-restore < /etc/iptables.rules
EOF
```

```bash
chmod +x /etc/rc.local
```

### Step 5 — Verify rules are applied

```bash
iptables -L INPUT -n -v
```

**Expected output:**
```
Chain INPUT (policy ACCEPT)
target     prot opt source         destination
ACCEPT     all  --  anywhere       anywhere    ctstate RELATED,ESTABLISHED
ACCEPT     all  --  anywhere       anywhere
ACCEPT     tcp  --  10.99.99.0/24  anywhere    tcp dpt:22
ACCEPT     udp  --  10.99.99.0/24  anywhere    udp dpt:53
ACCEPT     tcp  --  10.99.99.0/24  anywhere    tcp dpt:53
ACCEPT     tcp  --  10.99.99.0/24  anywhere    tcp dpt:80
ACCEPT     tcp  --  10.99.99.0/24  anywhere    tcp dpt:443
ACCEPT     udp  --  anywhere       anywhere    udp dpts:67:68
LOG        all  --  anywhere       anywhere    LOG level warning prefix "DROPPED: "
DROP       all  --  anywhere       anywhere
```

### Step 6 — Verify logging is working

Generate blocked traffic from Linux Mint host:

```bash
nmap -p 8080 10.99.99.146
```

Check logs on OpenWRT:

```bash
logread | grep "DROPPED" | tail -20
```

**Expected output:**
```
DROPPED: IN=eth0 SRC=10.99.99.1 DST=10.99.99.146 PROTO=TCP DPT=8080
```

---

## Troubleshooting: iptables state module not found

**Symptoms:**
```
iptables v1.8.10 (nf_tables): Couldn't load match `state':No such file or directory
```

**Root Cause:** OpenWRT 25.x uses `conntrack` module instead of the older `state` module.

**Resolution:** Replace `--state` with `--ctstate`:

```bash
# Wrong (old syntax)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Correct (OpenWRT 25.x)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

---

## Updated Build Verification Checklist

### Blue/Red Team Firewall
- [ ] Log-Dropped-WAN rule added in LuCI Traffic Rules
- [ ] iptables rules applied (conntrack, not state)
- [ ] Only ports 22, 53, 80, 443, 67-68 allowed from lab subnet
- [ ] All other traffic logged with "DROPPED: " prefix
- [ ] Rules saved to `/etc/iptables.rules`
- [ ] Rules restore on boot via `/etc/rc.local`
- [ ] `logread | grep DROPPED` shows blocked packets
- [ ] nmap scan from host confirms ports are blocked

---

## Updated Lessons Learned

### Blue/Red Team Lab Design
- Restrict allowed ports to only what's needed — everything else should be dropped and logged
- Always log dropped packets — this data feeds your AI-IDS and helps blue team detect attacks
- Use subnet-scoped rules (`10.99.99.0/24`) so only lab machines can access management ports
- Test firewall rules with nmap from the host before declaring them complete

### iptables on OpenWRT
- OpenWRT 25.x uses `conntrack` instead of `state` for connection tracking
- `iptables-save > /etc/iptables.rules` persists rules across reboots
- Rule order matters — ACCEPT rules must come before the final DROP rule
- Use `iptables -L INPUT -n -v` to verify rules with packet counts

---

## Step 18: Create the gateway VM (dnsmasq + NAT + Sinkhole)

### Why
The gateway VM acts as a full router for client VMs — providing DHCP, DNS, NAT, and DNS sinkhole capabilities. This creates a realistic SOC lab where client traffic flows through a controlled gateway before reaching the internet.

### Create the gateway VM (on Linux Mint host)

```bash
virt-install \
  --name gateway \
  --ram 4096 \
  --vcpus 4 \
  --disk path=/var/lib/libvirt/images/gateway.qcow2,size=20 \
  --cdrom /home/chris/Downloads/xubuntu-24.04.4-desktop-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=isolated-lab,model=virtio \
  --graphics spice \
  --video qxl \
  --boot cdrom,hd
```

### Install Xubuntu with these settings

| Field | Value |
|-------|-------|
| Username | `socadmin` |
| Hostname | `gateway` |
| Installation type | Erase disk and install |

### Fix DNS after first boot (inside gateway VM)

```bash
sudo systemctl disable --now systemd-resolved
sudo rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### Update and install packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y dnsmasq iptables iptables-persistent netfilter-persistent
```

### Configure kernel for IP forwarding and security

```bash
sudo bash -c 'cat > /etc/sysctl.d/99-gateway.conf << EOF
net.ipv4.ip_forward = 1
net.ipv4.conf.all.forwarding = 1
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.core.netdev_max_backlog = 250000
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF'
```

```bash
sudo sysctl -p /etc/sysctl.d/99-gateway.conf
cat /proc/sys/net/ipv4/ip_forward
```

**Expected output:** `1`

---

## Step 19: Create client-lab Network and Add Second Interface

### Create client-lab network (on Linux Mint host)

```bash
cat > /tmp/client-lab.xml << 'EOF'
<network>
  <name>client-lab</name>
  <bridge name='virbr2' stp='on' delay='0'/>
</network>
EOF
```

```bash
sudo virsh net-define /tmp/client-lab.xml
sudo virsh net-start client-lab
sudo virsh net-autostart client-lab
```

### Add client-lab interface to gateway VM

```bash
sudo virsh attach-interface gateway \
  --type network \
  --source client-lab \
  --model virtio \
  --live \
  --persistent
```

---

## Step 20: Configure Gateway Network Interfaces

### Back up netplan config (inside gateway VM)

```bash
sudo cp /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml.backup
sudo nano /etc/netplan/50-cloud-init.yaml
```

```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: false
      addresses:
        - 192.168.1.10/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
    enp7s0:
      dhcp4: false
    enp8s0:
      dhcp4: false
      addresses:
        - 172.16.50.1/24
```

```bash
sudo chmod 600 /etc/netplan/50-cloud-init.yaml
sudo netplan apply
ip a show enp1s0
ip a show enp8s0
```

---

## Step 21: Configure NAT and dnsmasq

### Add NAT masquerading rule

```bash
sudo iptables -t nat -A POSTROUTING -s 172.16.50.0/24 -o enp1s0 -j MASQUERADE
sudo netfilter-persistent save
```

### Configure dnsmasq

```bash
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
sudo systemctl stop dnsmasq
sudo nano /etc/dnsmasq.conf
```

```conf
interface=enp8s0
bind-interfaces
server=8.8.8.8
server=8.8.4.4
local=/lab.local/
domain=lab.local
dhcp-range=172.16.50.50,172.16.50.150,12h
dhcp-option=3,172.16.50.1
dhcp-option=6,172.16.50.1
dhcp-leasefile=/var/lib/misc/dnsmasq.leases
log-queries
log-facility=/var/log/dnsmasq.log
address=/malware.com/0.0.0.0
address=/evil.com/0.0.0.0
address=/phishing-test.local/0.0.0.0
```

```bash
sudo systemctl start dnsmasq
sudo systemctl enable dnsmasq
```

---

## Step 22: Create the Client VM

```bash
virt-install \
  --name client \
  --ram 4096 \
  --vcpus 4 \
  --disk path=/var/lib/libvirt/images/client.qcow2,size=55 \
  --cdrom /home/chris/Downloads/xubuntu-24.04.4-desktop-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=client-lab,model=virtio \
  --graphics spice \
  --video qxl \
  --boot cdrom,hd
```

| Field | Value |
|-------|-------|
| Username | `labuser` |
| Hostname | `client` |

### Install qBittorrent

```bash
sudo apt install -y qbittorrent
```

---

## Step 23: Verify Full Network Chain

```bash
ping -c 3 172.16.50.1
ping -c 3 8.8.8.8
ping -c 3 google.com
ping -c 3 malware.com
```

**Expected sinkhole output:** resolves to `127.0.0.1` ✅

### Allow client subnet through OpenWRT (via SSH on OpenWRT)

```bash
ip route add 172.16.50.0/24 via 192.168.1.10
iptables -A FORWARD -s 172.16.50.0/24 -j ACCEPT
iptables -A FORWARD -d 172.16.50.0/24 -j ACCEPT
```

---

## Final Lab Architecture

```
Internet
    ↕
Linux Mint Host (32GB RAM, 40 cores, i7-12700F)
    ↕ nat-lab (10.99.99.0/24)
OpenWRT (10.99.99.146)
    ├── LuCI web interface
    ├── mwan3 Multi-WAN failover
    ├── iptables blue/red team firewall
    └── packet drop logging
        ↕ isolated-lab (192.168.1.0/24)
gateway (192.168.1.10)
    ├── dnsmasq DHCP + DNS
    ├── DNS sinkhole
    ├── NAT masquerading
    └── IP forwarding
        ↕ client-lab (172.16.50.0/24)
        ├── client (172.16.50.74) — qBittorrent
        └── sentinel (192.168.1.192)
            ├── Flask AI-IDS API (port 5000)
            └── Streamlit Dashboard (port 8501)
```

---

## VM Snapshot History

| VM | Snapshot | Description |
|----|---------|-------------|
| sentinel | AI-IDS-Working | Initial Flask + Streamlit working |
| sentinel | Sentinel-AI-IDS-Working | Routing through OpenWRT |
| sentinel | Sentinel-Full-Lab | Full lab connected |
| openwrt | OpenWRT-Working | Basic routing working |
| openwrt | OpenWRT-LuCI-Firewall | LuCI + firewall rules |
| openwrt | OpenWRT-Full-Lab | Complete lab setup |
| gateway | Gateway-Full-Lab | dnsmasq + NAT + sinkhole |
| client | Client-Full-Lab | qBittorrent + internet working |

---

## Final Build Verification Checklist

### Gateway VM
- [ ] IP forwarding enabled
- [ ] sysctl security tuning applied
- [ ] enp1s0 static IP `192.168.1.10`
- [ ] enp8s0 static IP `172.16.50.1`
- [ ] NAT masquerading rule active
- [ ] dnsmasq running and enabled
- [ ] DHCP serving `172.16.50.50-150`
- [ ] DNS sinkhole blocking `malware.com`

### Client VM
- [ ] Got DHCP IP from gateway (`172.16.50.x`)
- [ ] Can ping gateway (`172.16.50.1`)
- [ ] Internet reachable (`ping 8.8.8.8`)
- [ ] DNS working (`ping google.com`)
- [ ] Sinkhole working (`ping malware.com` → `127.0.0.1`)
- [ ] qBittorrent installed

### Full Lab
- [ ] All 4 VMs running simultaneously
- [ ] All VMs snapshotted
- [ ] Traffic: client → gateway → OpenWRT → internet
- [ ] AI-IDS monitoring on sentinel
- [ ] Firewall logging on OpenWRT
- [ ] DNS sinkhole on gateway

---

## Final Lessons Learned

### Lab Design
- Build in layers — each VM adds a security control
- Test connectivity after each step before moving on
- Static IPs for infrastructure, DHCP for clients
- Snapshots at every milestone saves hours of rebuild time

### dnsmasq
- Remove invalid config lines before starting
- `bind-interfaces` required when specifying a specific interface
- DNS sinkhole redirects to `0.0.0.0` — clients see `127.0.0.1`
- Always back up config files before editing

### SOC Lab Architecture
- Gateway provides DNS visibility into all client requests
- DNS logs feed into AI-IDS on sentinel
- OpenWRT provides perimeter firewall logging
- Layered logging gives full visibility: DNS → firewall → IDS

---

*Final update — June 12, 2026*
