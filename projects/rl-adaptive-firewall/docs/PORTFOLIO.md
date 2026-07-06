# Building an Adaptive Cybersecurity Lab with a Reinforcement Learning Firewall

*A complete home lab project: virtual networks, OpenWrt routing, and a self-learning firewall built with TensorFlow.*

---

## Final Project Summary

*For the hiring manager who has 60 seconds.*

I built a complete virtual cybersecurity lab on a Linux Mint desktop using KVM virtualization. The lab contains a real OpenWrt router, a gateway server, and client machines connected across isolated virtual networks — all running inside virtual machines on one physical computer.

On top of that infrastructure, I built an adaptive firewall using reinforcement learning. Instead of static rules that someone writes by hand, this firewall watches every network connection, extracts numerical features from the traffic, and uses a deep neural network to decide whether to allow, block, rate-limit, or flag each connection. The agent learns from its own mistakes in real time, updating its policy every four packets.

**What this demonstrates:**

- Designing and building multi-segment virtual networks from scratch
- Configuring OpenWrt as a production router using UCI (the OpenWrt configuration system)
- Writing a packet interception pipeline using Linux kernel netfilter queues
- Implementing a Deep Q-Network in TensorFlow 2 and wiring it to live iptables rules
- Setting up a complete observability stack: Prometheus scraping custom metrics, Grafana dashboards updating every five seconds
- Persistent infrastructure: systemd services, autostart VMs, MAC-locked network profiles
- Real troubleshooting: interface naming conflicts, kernel module loading, IP address collisions, cloud-init overwriting static configs, duplicate Prometheus jobs, nfqueue permission failures

**Technologies:** Linux Mint, KVM/libvirt, OpenWrt 23.05.3, Xubuntu 24.04, Python 3.12, TensorFlow 2.21, Keras, Scapy, netfilterqueue, iptables, Prometheus, Grafana, dnsmasq, NetworkManager, systemd, nmap, hping3, bash

---

## Project Overview

### What I Built

A two-layer virtual network lab with a self-learning firewall sitting in the middle.

The lab has three virtual machines:

- **openwrt** — a tiny but real router running OpenWrt, the same firmware used in millions of home and enterprise routers worldwide
- **gw-dmz** — a Xubuntu Linux server acting as a second-layer gateway, running dnsmasq for DHCP and DNS, iptables for NAT, and the entire RL firewall stack
- **client-lan** — a Xubuntu desktop that represents a regular user on the network

Every packet that the client machine sends to the internet passes through the RL firewall running on gw-dmz. The firewall intercepts it, turns it into numbers, feeds those numbers to a neural network, gets a decision back, and applies that decision as a live iptables rule — all before the packet reaches OpenWrt.

### Why I Built It

Static firewall rules are written by humans before an attack happens. If an attacker uses a technique the rule author did not anticipate, the rule does not catch it.

A reinforcement learning firewall writes its own rules based on what it observes. It can adapt to traffic patterns it has never seen before. It gets better over time rather than staying frozen at whatever someone configured months ago.

This is not a toy concept. DARPA has funded RL-based network defense research. Commercial products like Darktrace use machine learning for exactly this purpose. This project is a working proof of concept of the same core idea, built from open-source components.

### What Real-World Problem It Solves

A traditional firewall blocks port 22 or 443 based on a rule someone wrote. But a modern attack does not always use forbidden ports. Attackers blend into normal traffic patterns — low-and-slow port scans, SYN floods that mimic busy legitimate traffic, credential stuffing that looks like normal login attempts.

The RL firewall looks at the *behaviour* of traffic — packet rate, SYN flag ratios, port entropy, small-packet ratios — not just the port number. It learns what normal looks like and treats deviations as suspicious.

### Why Employers Should Care

This project touches every layer of the network stack. I had to understand how packets move from a virtual machine through a software bridge into a kernel queue, how a Python process can intercept and modify that queue, how TensorFlow runs inference fast enough to not become a bottleneck, and how Prometheus scrapes metrics from a custom Python HTTP server so Grafana can graph the neural network's learning curve in real time.

That is not a tutorial project. That is engineering.

---

## Skills Demonstrated

| Category | Skills |
|---|---|
| **Linux** | systemd, kernel modules, file permissions, process management, package management |
| **Networking** | TCP/IP, routing, NAT, bridges, VLANs, DNS, DHCP, iptables, nfqueue |
| **Virtualization** | KVM, libvirt, virt-install, virt-clone, virt-xml, virsh, veth pairs |
| **Firewalls** | OpenWrt UCI, iptables chains, NFQUEUE, netfilter, hashlimit, conntrack |
| **Programming** | Python 3.12, TensorFlow 2, Keras, Scapy, asyncio, threading |
| **Machine Learning** | Deep Q-Networks, replay buffers, epsilon-greedy exploration, reward shaping |
| **Observability** | Prometheus, Grafana, custom metrics exporters, dashboard design |
| **Security** | Network segmentation, DMZ design, traffic analysis, anomaly detection |
| **Troubleshooting** | Interface naming, IP conflicts, kernel module failures, YAML syntax errors |
| **Documentation** | Reproducible setup guides, architecture diagrams, command-by-command explanations |

---

## Architecture

### Network Diagram

```
                    Internet
                       │
                       │ (your real wifi — never touched)
                       │
              ┌─────────────────┐
              │   Linux Mint    │
              │   Host (KVM)    │
              └────────┬────────┘
                       │
              ┌─────────────────┐
              │   libvirt NAT   │  virbr0  10.0.0.x
              └────────┬────────┘
                       │ eth0 (WAN)
              ┌─────────────────┐
              │    OpenWrt VM   │  openwrt
              │  Router/FW      │
              └──┬──────┬───┬───┘
                 │      │   │
            eth1 │  eth2│   │ eth3
            MGMT │   LAN│   │ DMZ
         10.0.99 │       │   │ 10.0.96
                 │       │   │
          (admin │       │   └──────────────────────┐
           access│       │                          │
           only) │       │                 ┌────────────────┐
                 │       │                 │   gw-dmz VM    │
                 │       │                 │  Xubuntu GW    │
                 │       │                 │                │
                 │       │                 │ enp1s0  enp2s0 │
                 │       │                 │ 10.0.96.x      │
                 │       │                 │         10.0.98.1
                 │       │                 │                │
                 │       │                 │ RL FIREWALL    │
                 │       │                 │ dnsmasq        │
                 │       │                 │ iptables NAT   │
                 │       │                 └───────┬────────┘
                 │       │                         │ 10.0.98.x
                 │       └─────────────────────────┤
                 │                                 │
                 │                        ┌────────────────┐
                 │                        │ client-lan VM  │
                 │                        │ Xubuntu Desktop│
                 │                        │ 10.0.98.200    │
                 │                        └────────────────┘
                 │
         ┌───────────────┐
         │  Mint host    │
         │  veth pairs   │
         │  10.0.99.100  │  (admin reach-in)
         └───────────────┘
```

### What Each Connection Does

**eth0 / WAN:** OpenWrt gets a DHCP lease from libvirt's NAT network. All internet traffic from the lab is masqueraded (hidden) behind this single IP. Your real home network never sees the lab machines.

**eth1 / MGMT (10.0.99.0/24):** Management-only segment. This is how I SSH into OpenWrt from the Mint host. No client VMs are attached here. If the lab breaks, I can always reach OpenWrt through this interface.

**eth3 / DMZ (10.0.96.0/24):** The demilitarised zone. gw-dmz gets its upstream internet connection from here. This is also where the RL firewall receives its first look at traffic before it passes to the LAN.

**enp2s0 / LAN (10.0.98.0/24):** The internal network where client machines live. gw-dmz owns this segment — it runs DHCP, DNS, and NAT for everything on 10.0.98.x.

### RL Firewall Data Flow

```
client-lan sends packet
        │
        ▼
iptables FORWARD chain (gw-dmz)
        │
        ▼  (NEW connections only)
NFQUEUE 0  ◄── kernel holds packet here, waiting
        │
        ▼
feature_extractor.py
  Parse IP/TCP/UDP/ICMP headers
  Update FlowStats (rolling window)
  Compute 10-dimensional feature vector
        │
        ▼
dqn_agent.py (TensorFlow)
  Feed state vector → policy network
  Get Q-values for 5 actions
  Select action (epsilon-greedy)
        │
        ▼
Apply action:
  ALLOW      → pkt.accept()
  BLOCK_IP   → iptables -I FORWARD -s <ip> -j DROP
  RATE_LIMIT → iptables hashlimit rule
  LOG_WATCH  → add to watchlist, accept
  BLOCK_PORT → iptables -I FORWARD -p tcp --dport <port> -j DROP
        │
        ▼
Compute reward
Store transition in replay buffer
Train policy network every 4 packets
        │
        ▼
state_writer.py → agent_state.json
        │
        ▼
metrics/exporter.py → Prometheus port 9101
        │
        ▼
Grafana dashboard (port 3000)
```

---

## Before We Start

### What You Need

**Hardware:**
- Any modern 64-bit PC or laptop
- At least 8 GB RAM (the VMs use about 5 GB total)
- At least 60 GB free disk space

**Software:**
- Linux Mint (any recent version) or Ubuntu 22.04+
- KVM and libvirt installed (`sudo apt install qemu-kvm libvirt-daemon-system virt-manager`)
- An internet connection for downloading images

**Skills assumed:**
- You can open a terminal
- You know how to copy and paste commands
- You do not need to know networking in advance — this document explains everything

**Time:** About 3–4 hours for the full setup including downloads.

**Difficulty:** Intermediate. Every command is explained. Every mistake I made is documented.

---

## Part 1 — The Virtual Network Lab

### Step 1.1 — Create the Project Folder

```bash
mkdir -p ~/lab/{scripts,images,notes}
```

**What this does:**

`mkdir` means "make directory." The `-p` flag means "make the full path, including any parent folders that do not exist yet." The curly braces `{scripts,images,notes}` are a bash shortcut that creates all three folders at once.

Think of this like setting up a filing cabinet before starting a project. Scripts go in one drawer, downloaded images in another, and your notes in the third.

### What Just Happened?

You now have a folder at `~/lab/` with three subfolders inside it. The tilde `~` means your home directory — on Linux Mint that is `/home/yourname/`.

---

### Step 1.2 — Download the OpenWrt Image

```bash
wget --show-progress -O /tmp/openwrt.img.gz \
  https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-23.05.3-x86-64-generic-ext4-combined.img.gz
```

**What each part means:**

- `wget` — a command-line tool for downloading files from the internet, like clicking a download link in a browser but from the terminal
- `--show-progress` — shows a progress bar so you can see how far along the download is
- `-O /tmp/openwrt.img.gz` — save the file to `/tmp/` with this name (`-O` means "output file")
- The long URL — the official OpenWrt download server, version 23.05.3, for 64-bit x86 computers (the same CPU type as your desktop)

OpenWrt is a tiny Linux operating system designed for routers. The full image is only about 11 MB compressed. By comparison, a normal Ubuntu desktop image is over 4 GB.

```bash
gunzip -f /tmp/openwrt.img.gz
```

`gunzip` decompresses the `.gz` file. The `-f` flag means "force" — overwrite the output file if it already exists. After this command you will see a warning about "trailing garbage ignored" — this is normal for OpenWrt images and means everything is fine.

```bash
sudo mv /tmp/openwrt.img /var/lib/libvirt/images/openwrt-fresh.img
sudo qemu-img resize /var/lib/libvirt/images/openwrt-fresh.img 1G
sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/openwrt-fresh.img
sudo chmod 644 /var/lib/libvirt/images/openwrt-fresh.img
```

**Line by line:**

- `sudo mv` — move the file. `sudo` means "do this as the administrator" (Super User DO). You need administrator permission to write to `/var/lib/libvirt/images/` because that folder belongs to the system, not to you.
- `qemu-img resize` — grow the disk image to 1 GB. The original OpenWrt image is about 120 MB. Resizing gives room to install packages later.
- `chown libvirt-qemu:kvm` — change the owner of the file to the `libvirt-qemu` user. libvirt (the virtualization manager) runs as this user, not as you. If it cannot read the file, the VM will not start.
- `chmod 644` — set the file permissions. `644` means: owner can read and write, everyone else can only read.

### What Just Happened?

You downloaded a miniature Linux operating system for routers, decompressed it, gave it more disk space, and placed it where the virtualization software can find it.

### Verify It Worked

```bash
ls -lh /var/lib/libvirt/images/openwrt-fresh.img
```

Expected output:
```
-rw-r--r-- 1 libvirt-qemu kvm 1.0G [date] /var/lib/libvirt/images/openwrt-fresh.img
```

If the size shows something other than 1.0G or the owner is not `libvirt-qemu`, rerun the `chown` and `qemu-img resize` commands.

---

### Step 1.3 — Create the Virtual Networks

Virtual networks are software-defined switches. Instead of plugging a cable into a physical switch, virtual machines connect to these software bridges.

```bash
# Check if nat-wan already exists
sudo virsh net-list --all
```

`virsh` is the command-line tool for managing virtual machines and networks. `net-list --all` shows every network, whether running or stopped.

Create each network one at a time:

```bash
# nat-wan — the internet-facing network
sudo virsh net-define /dev/stdin <<'EOF'
<network>
  <name>nat-wan</name>
  <forward mode="nat"/>
  <bridge name="virbr0" stp="on" delay="0"/>
  <ip address="10.0.0.1" netmask="255.255.255.0">
    <dhcp>
      <range start="10.0.0.2" end="10.0.0.254"/>
    </dhcp>
  </ip>
</network>
EOF
sudo virsh net-start nat-wan
sudo virsh net-autostart nat-wan
```

```bash
# lab-mgmt — management segment (admin access only)
sudo virsh net-define /dev/stdin <<'EOF'
<network>
  <name>lab-mgmt</name>
  <bridge name="sw-r0-eth1"/>
</network>
EOF
sudo virsh net-start lab-mgmt
sudo virsh net-autostart lab-mgmt
```

```bash
# lab-lan — client segment
sudo virsh net-define /dev/stdin <<'EOF'
<network>
  <name>lab-lan</name>
  <bridge name="sw-r0-eth2"/>
</network>
EOF
sudo virsh net-start lab-lan
sudo virsh net-autostart lab-lan
```

```bash
# lab-dmz — DMZ segment for gateway VM
sudo virsh net-define /dev/stdin <<'EOF'
<network>
  <name>lab-dmz</name>
  <bridge name="sw-r0-eth3"/>
</network>
EOF
sudo virsh net-start lab-dmz
sudo virsh net-autostart lab-dmz
```

**What `nat-wan` is:** A NAT network is one where libvirt acts like a tiny router. Virtual machines inside get private IP addresses (10.0.0.x). When they send traffic to the internet, libvirt rewrites the source address to your real IP before sending it out — just like your home router does for your whole house. This means the lab has internet access but is not directly reachable from outside.

**What the isolated networks are:** `lab-mgmt`, `lab-lan`, and `lab-dmz` are "isolated" — they have no gateway and no DHCP server by default. They are just a wire. OpenWrt and the gateway VM provide the intelligence for these segments.

### Mistakes I Made

**"Bridge name already in use"** — This happened when I tried to create `lab-dmz` after a previous failed setup left the bridge `sw-r0-eth3` still registered in the kernel. The fix:

```bash
# Find which libvirt network is using the bridge
sudo virsh net-list --all

# Destroy and undefine the conflicting network
sudo virsh net-destroy lab-iot
sudo virsh net-undefine lab-iot

# Then delete the orphaned bridge from the kernel
sudo ip link set sw-r0-eth3 down
sudo ip link del sw-r0-eth3

# Now create lab-dmz successfully
```

**Lesson learned:** When tearing down and rebuilding a lab, always run `virsh net-list --all` first to see what is already defined. Do not assume a clean state.

### Verify the Networks

```bash
sudo virsh net-list --all
```

Expected output:
```
 Name       State    Autostart   Persistent
-------------------------------------------
 lab-dmz    active   yes         yes
 lab-lan    active   yes         yes
 lab-mgmt   active   yes         yes
 nat-wan    active   yes         yes
```

All four should show `active` and `yes` for autostart.

---

### Step 1.4 — Create the OpenWrt Virtual Machine

```bash
sudo virt-install \
  --name openwrt \
  --memory 512 \
  --vcpus 1 \
  --disk path=/var/lib/libvirt/images/openwrt-fresh.img,format=raw,bus=virtio \
  --import \
  --os-variant linux2022 \
  --network network=nat-wan,model=virtio \
  --network network=lab-mgmt,model=virtio \
  --network network=lab-lan,model=virtio \
  --network network=lab-dmz,model=virtio \
  --graphics none \
  --console pty,target_type=serial \
  --noautoconsole \
  --boot hd
```

**Flags explained:**

- `--name openwrt` — the name we will use to manage this VM
- `--memory 512` — give the VM 512 MB of RAM. OpenWrt only needs about 64 MB normally, so 512 is generous.
- `--vcpus 1` — one virtual CPU core
- `--disk path=...,format=raw,bus=virtio` — use the image we prepared. `format=raw` tells QEMU the exact disk format. `bus=virtio` uses a faster virtual disk driver than the default.
- `--import` — do not run an installer, just use the disk as-is
- `--os-variant linux2022` — hints to libvirt about what kind of OS this is, used for optimization. OpenWrt does not have its own entry, so `linux2022` is a reasonable generic choice.
- `--network network=nat-wan,model=virtio` — attach to the nat-wan network using the virtio driver (faster than the emulated e1000)
- `--graphics none` — no graphical console (OpenWrt is text-only)
- `--console pty,target_type=serial` — connect a serial console so we can interact with OpenWrt from the terminal
- `--noautoconsole` — do not automatically open the console after creating the VM
- `--boot hd` — boot from the hard disk

You will see a warning: "Requested memory 512 MiB is less than the recommended 2048 MiB." Ignore this. The recommendation is for full desktop Linux, not a 120 MB router OS.

### What Just Happened?

You created a fully functional virtual router with four virtual network cards, connected to four different virtual networks. This is the same as buying a physical router and plugging four ethernet cables into it.

---

### Step 1.5 — Configure OpenWrt

Connect to the OpenWrt console:

```bash
sudo virsh console openwrt
```

Press **Enter** once. You will see the OpenWrt login prompt or a blank line. There is no password yet — just press Enter.

**The OpenWrt configuration problem:** Fresh OpenWrt on x86 does not know which virtual network card is which. It puts eth0 into a LAN bridge by default, which is wrong for our setup. We need eth0 to be WAN (internet-facing) and eth1, eth2, eth3 to be our internal segments.

Run this configuration block:

```bash
cat > /tmp/configure.sh << 'ENDOFSCRIPT'
uci del network.@device[0] 2>/dev/null || true
uci set network.wan.device='eth0'
uci set network.wan.proto='dhcp'
uci set network.wan6.device='eth0'
uci set network.wan6.proto='dhcpv6'
uci set network.mgmt=interface
uci set network.mgmt.device='eth1'
uci set network.mgmt.proto='static'
uci set network.mgmt.ipaddr='10.0.99.1'
uci set network.mgmt.netmask='255.255.255.0'
uci set network.lan=interface
uci set network.lan.device='eth2'
uci set network.lan.proto='static'
uci set network.lan.ipaddr='10.0.98.254'
uci set network.lan.netmask='255.255.255.0'
uci set network.dmz=interface
uci set network.dmz.device='eth3'
uci set network.dmz.proto='static'
uci set network.dmz.ipaddr='10.0.96.1'
uci set network.dmz.netmask='255.255.255.0'
uci commit network
service network restart
sleep 5
ip addr show
ENDOFSCRIPT
sh /tmp/configure.sh
```

**What `uci` is:** UCI stands for Unified Configuration Interface. It is OpenWrt's configuration system. Instead of editing text files directly, you use `uci set` to change settings and `uci commit` to save them. Think of it like a settings menu that you control from the command line.

**Why eth2 gets 10.0.98.254 instead of 10.0.98.1:** The gateway VM (gw-dmz) will take over the role of LAN gateway at 10.0.98.1. If OpenWrt also claimed .1, they would fight over the same address and both would break. By giving OpenWrt .254, it stays on the LAN segment but gets out of the way.

### Verify OpenWrt Network

After the restart:

```bash
ip addr show
```

Expected: eth0 should have a 10.0.0.x address (DHCP from libvirt). eth1 should have 10.0.99.1. eth2 should have 10.0.98.254. eth3 should have 10.0.96.1.

```bash
ping -c 3 8.8.8.8
```

Expected: three successful replies. If this works, OpenWrt has internet.

### Set Root Password and Configure Firewall

Still inside OpenWrt:

```bash
passwd root
```

Choose a password and write it down. I used `labpass123` for the lab environment.

Run the firewall configuration:

```bash
cat > /tmp/fw.sh << 'EOF'
while uci delete firewall.@zone[0] 2>/dev/null; do :; done
while uci delete firewall.@forwarding[0] 2>/dev/null; do :; done
uci add firewall zone
uci set firewall.@zone[-1].name='wan'
uci set firewall.@zone[-1].network='wan wan6'
uci set firewall.@zone[-1].input='REJECT'
uci set firewall.@zone[-1].output='ACCEPT'
uci set firewall.@zone[-1].forward='REJECT'
uci set firewall.@zone[-1].masq='1'
uci set firewall.@zone[-1].mtu_fix='1'
uci add firewall zone
uci set firewall.@zone[-1].name='mgmt'
uci set firewall.@zone[-1].network='mgmt'
uci set firewall.@zone[-1].input='ACCEPT'
uci set firewall.@zone[-1].output='ACCEPT'
uci set firewall.@zone[-1].forward='ACCEPT'
uci add firewall zone
uci set firewall.@zone[-1].name='lan'
uci set firewall.@zone[-1].network='lan'
uci set firewall.@zone[-1].input='ACCEPT'
uci set firewall.@zone[-1].output='ACCEPT'
uci set firewall.@zone[-1].forward='REJECT'
uci add firewall zone
uci set firewall.@zone[-1].name='dmz'
uci set firewall.@zone[-1].network='dmz'
uci set firewall.@zone[-1].input='ACCEPT'
uci set firewall.@zone[-1].output='ACCEPT'
uci set firewall.@zone[-1].forward='REJECT'
uci add firewall forwarding
uci set firewall.@forwarding[-1].src='lan'
uci set firewall.@forwarding[-1].dest='wan'
uci add firewall forwarding
uci set firewall.@forwarding[-1].src='dmz'
uci set firewall.@forwarding[-1].dest='wan'
uci add firewall forwarding
uci set firewall.@forwarding[-1].src='mgmt'
uci set firewall.@forwarding[-1].dest='wan'
uci commit firewall
uci set dhcp.dmz=dhcp
uci set dhcp.dmz.interface='dmz'
uci set dhcp.dmz.start='10'
uci set dhcp.dmz.limit='40'
uci set dhcp.dmz.leasetime='12h'
uci delete dhcp.lan 2>/dev/null || true
uci set dropbear.@dropbear[0].Interface=''
uci set dropbear.@dropbear[0].PasswordAuth='on'
uci set dropbear.@dropbear[0].RootPasswordAuth='on'
uci commit dhcp
uci commit dropbear
service firewall restart
service dnsmasq restart
service dropbear restart
echo "Firewall configured."
EOF
sh /tmp/fw.sh
```

**Why delete `dhcp.lan`:** The gateway VM will run its own DHCP server on the LAN segment. Having two DHCP servers on the same network causes chaos — clients randomly get addresses from whichever server responds first. We remove OpenWrt's LAN DHCP entirely.

**What the `masq='1'` on the WAN zone does:** Masquerading is another word for NAT. When a packet from 10.0.98.200 leaves through the WAN interface, OpenWrt rewrites the source address to the WAN IP. The destination server on the internet sees a reply address it can actually route back to, not a private address it cannot reach.

Press **Ctrl+]** to exit the console.

---

### Step 1.6 — Connect Mint Host to the Lab

The veth pairs let your Mint terminal reach into the lab networks directly. Without them, you cannot SSH into OpenWrt or the gateway VM from your host.

Save this as `~/lab/scripts/lab-up.sh`:

```bash
#!/bin/bash
set -euo pipefail
[[ $EUID -ne 0 ]] && { echo "Run with sudo"; exit 1; }

veths="
veth-mgmt-b|master=sw-r0-eth1:veth-mgmt-h|ip=10.0.99.100/24
veth-lan-b|master=sw-r0-eth2:veth-lan-h|ip=10.0.98.100/24
veth-dmz-b|master=sw-r0-eth3:veth-dmz-h|ip=10.0.96.100/24
"

while IFS= read -r line; do
    line="$(echo "$line" | xargs)"
    [[ -z "$line" ]] && continue
    raw_left="${line%%:*}"; raw_right="${line##*:}"
    left_dev="${raw_left%%|*}"; left_opts="${raw_left##*|}"
    right_dev="${raw_right%%|*}"; right_opts="${raw_right##*|}"
    ip link show "$left_dev" &>/dev/null || ip link add "$left_dev" type veth peer name "$right_dev"
    for spec in "${left_dev}|${left_opts}" "${right_dev}|${right_opts}"; do
        dev="${spec%%|*}"; opts="${spec##*|}"
        ip link set "$dev" up
        IFS=',' read -ra opt_list <<< "$opts"
        for opt in "${opt_list[@]}"; do
            key="${opt%%=*}"; val="${opt##*=}"
            [[ "$key" == "master" ]] && ip link set "$dev" master "$val" 2>/dev/null || true
            [[ "$key" == "ip" ]] && { ip addr flush dev "$dev" 2>/dev/null || true; ip addr add "$val" dev "$dev"; }
        done
    done
done <<< "$veths"

echo "Lab interfaces up."
```

```bash
chmod +x ~/lab/scripts/lab-up.sh
sudo bash ~/lab/scripts/lab-up.sh
```

**What a veth pair is:** A veth pair is two virtual network interfaces connected back to back, like a cable with a plug on each end. One end (`veth-mgmt-b`) plugs into the libvirt bridge so it can reach the VMs. The other end (`veth-mgmt-h`) sits on your Mint host with a static IP address so you can connect to it from the terminal.

Think of it like running an ethernet cable from a server rack to your desk — except the cable and the desk are both software.

### Test SSH into OpenWrt

```bash
ssh root@10.0.99.1
```

If you get the OpenWrt login prompt, the lab network is working correctly.

### Mistakes I Made

**SSH refused after setting up veth pairs:** I forgot that the `netplan-enp2s0` NetworkManager profile had a bug — it was locking to the wrong physical interface after the gw-dmz VM was cloned. The MAC address the profile was tracking had changed.

Diagnosis:
```bash
nmcli connection show
ip addr show
```

The tell was that `netplan-enp2s0` was listed as connected to `enp1s0` — the wrong interface. Fix: delete the old profiles and recreate them with explicit interface names and MAC locks.

---

### Step 1.7 — Build the Gateway VM

The gateway VM is a full Xubuntu server sitting between OpenWrt's DMZ and the client LAN. It runs:
- dnsmasq — DHCP server and DNS resolver for 10.0.98.x clients
- iptables — NAT from LAN to DMZ
- The complete RL firewall stack

Download Xubuntu:

```bash
wget -P ~/lab/images/ \
  https://cdimage.ubuntu.com/xubuntu/releases/24.04/release/xubuntu-24.04.4-desktop-amd64.iso
```

Create the disk and VM:

```bash
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/gw-dmz.qcow2 20G

sudo virt-install \
  --name gw-dmz \
  --memory 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/gw-dmz.qcow2,format=qcow2,bus=virtio \
  --cdrom ~/lab/images/xubuntu-24.04.4-desktop-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=lab-dmz,model=virtio \
  --network network=lab-lan,model=virtio \
  --graphics spice \
  --video qxl \
  --noautoconsole \
  --boot cdrom,hd
```

Open virt-manager, double-click gw-dmz, and install Xubuntu normally. Use hostname `gw-dmz`.

### Configure gw-dmz Networking

After install, open a terminal inside gw-dmz.

**Fix the cloud-init DNS conflict** (this will bite you if skipped):

```bash
sudo systemctl disable systemd-resolved
sudo systemctl stop systemd-resolved
sudo rm /etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf
```

**Why:** Ubuntu 24.04 ships with `systemd-resolved` running by default. It intercepts all DNS queries and handles them internally. But it also binds to port 53, which conflicts with dnsmasq. And its stub resolver at 127.0.0.53 breaks when you try to use a custom DNS server. Disabling it and writing a direct `/etc/resolv.conf` fixes both problems.

**Fix the cloud-init netplan conflict:**

```bash
# Check for the problematic file
cat /etc/netplan/50-cloud-init.yaml
```

If you see `dhcp4: true` for any interface, this file will fight with any static IP you try to set. Remove it:

```bash
sudo rm /etc/netplan/50-cloud-init.yaml
echo "network: {config: disabled}" | sudo tee /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
sudo netplan apply
```

**What cloud-init is:** Cloud-init is a tool designed for cloud servers. When a cloud provider spins up a new virtual machine, cloud-init reads configuration from the cloud provider and sets up the network automatically. On a local VM it is unnecessary and gets in the way because it keeps overwriting your manual configuration.

**Create permanent NetworkManager profiles:**

```bash
# Delete any broken profiles
sudo nmcli connection delete netplan-enp2s0 2>/dev/null || true

# DMZ uplink — gets DHCP from OpenWrt
sudo nmcli connection add \
  type ethernet \
  con-name dmz-uplink \
  ifname enp1s0 \
  ipv4.method auto \
  connection.autoconnect yes

# LAN gateway — static IP
sudo nmcli connection add \
  type ethernet \
  con-name lan-gateway \
  ifname enp2s0 \
  ipv4.method manual \
  ipv4.addresses 10.0.98.1/24 \
  connection.autoconnect yes

# Lock each profile to its MAC address so it never binds to the wrong NIC
sudo nmcli connection modify dmz-uplink ethernet.mac-address "52:54:00:ed:88:c1"
sudo nmcli connection modify lan-gateway ethernet.mac-address "52:54:00:a2:b8:71"

sudo nmcli connection up dmz-uplink
sudo nmcli connection up lan-gateway
```

Replace the MAC addresses with the actual values from `ip link show enp1s0` and `ip link show enp2s0`.

**Enable IP forwarding:**

```bash
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
```

**What IP forwarding is:** By default, Linux will not pass packets from one network interface to another. It treats itself as an endpoint, not a router. `ip_forward=1` tells the kernel to act as a router and forward packets between interfaces. Without this, traffic from the LAN would arrive at gw-dmz and stop — it would never reach the internet.

**Install and configure dnsmasq:**

```bash
sudo apt install -y dnsmasq iptables-persistent

sudo tee /etc/dnsmasq.conf > /dev/null << 'EOF'
interface=enp2s0
bind-interfaces
dhcp-range=10.0.98.10,10.0.98.200,255.255.255.0,12h
dhcp-option=3,10.0.98.1
dhcp-option=6,10.0.98.1
server=1.1.1.1
server=8.8.8.8
EOF

sudo systemctl restart dnsmasq
```

**What dnsmasq is:** dnsmasq is a lightweight combined DHCP and DNS server. DHCP hands out IP addresses to client machines automatically. DNS translates domain names like `google.com` into IP addresses. By running both in one process on gw-dmz, every client on the LAN gets an address from us and uses us for name resolution.

**Set up NAT:**

```bash
sudo iptables -t nat -A POSTROUTING -o enp1s0 -j MASQUERADE
sudo iptables -A FORWARD -i enp2s0 -o enp1s0 -j ACCEPT
sudo iptables -A FORWARD -i enp1s0 -o enp2s0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo netfilter-persistent save
```

**What MASQUERADE does:** When a packet leaves through `enp1s0` (the DMZ/internet side), MASQUERADE rewrites the source address to the gw-dmz's own IP. The packet looks like it came from gw-dmz, not from the client at 10.0.98.200. Replies come back to gw-dmz, which looks up the original sender in the connection tracking table and forwards the reply correctly.

### Verify the Gateway

```bash
ip addr show       # enp1s0 should have 10.0.96.x, enp2s0 should have 10.0.98.1
ping -c 3 8.8.8.8  # gateway has internet
ping -c 3 10.0.96.1 # can reach OpenWrt
```

---

### Step 1.8 — Build the Client VM

```bash
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/client-lan.qcow2 60G

sudo virt-install \
  --name client-lan \
  --memory 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/client-lan.qcow2,format=qcow2,bus=virtio \
  --cdrom ~/lab/images/xubuntu-24.04.4-desktop-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=lab-lan,model=virtio \
  --graphics spice \
  --video qxl \
  --noautoconsole \
  --boot cdrom,hd
```

Install Xubuntu with hostname `client-lan`. After install, open a terminal and fix DNS:

```bash
sudo systemctl disable systemd-resolved
sudo systemctl stop systemd-resolved
sudo rm /etc/resolv.conf
echo "nameserver 10.0.98.1" | sudo tee /etc/resolv.conf
echo 'Acquire::ForceIPv4 "true";' | sudo tee /etc/apt/apt.conf.d/99force-ipv4
sudo apt install -y openssh-server nmap hping3 curl wget
```

**Why ForceIPv4:** Ubuntu's package manager will try IPv6 addresses first. Our lab networks do not have full IPv6 routing set up, so IPv6 connections time out after 30 seconds before falling back to IPv4. Forcing IPv4 makes apt fast again.

### Verify the Full Chain

From the client-lan terminal:

```bash
ip addr show      # should show 10.0.98.x from dnsmasq
ping -c 3 10.0.98.1   # can reach gateway
ping -c 3 8.8.8.8     # internet works
ping -c 3 google.com  # DNS works
```

If all four succeed, the complete network chain is working: client → gw-dmz → OpenWrt → internet.

---

### Step 1.9 — Make Everything Persistent

Without these steps, the veth pairs disappear on reboot and the VMs do not start automatically.

```bash
# Autostart VMs with libvirt
sudo virsh autostart openwrt
sudo virsh autostart gw-dmz
sudo virsh autostart client-lan

# Load nfqueue kernel module on boot
echo "nfnetlink_queue" | sudo tee /etc/modules-load.d/nfqueue.conf

# Create systemd service for veth pairs
sudo tee /etc/systemd/system/lab-up.service > /dev/null << 'EOF'
[Unit]
Description=Lab virtual network bring-up
After=libvirtd.service
Wants=libvirtd.service

[Service]
Type=oneshot
ExecStart=/bin/bash /home/chris/lab/scripts/lab-up.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable lab-up.service
```

**What systemd is:** systemd is the init system — the first process that runs when Linux boots. It starts all other services in the right order. By creating a `.service` file, we tell systemd to run our `lab-up.sh` script every time the computer starts, after libvirt is ready.

---

## Part 2 — The Reinforcement Learning Firewall

### What Reinforcement Learning Is

Imagine teaching a dog a trick. You do not write down instructions for the dog. Instead, you give it a treat when it does something right and say "no" when it does something wrong. Eventually the dog figures out the right behaviour on its own.

Reinforcement learning works the same way. An *agent* (the firewall's brain) takes *actions* (allow, block, rate-limit). The environment (real network traffic) gives back a *reward* (positive number for good decisions, negative for bad ones). Over thousands of decisions, the agent learns which actions lead to the highest total reward.

### The 10-Feature State Vector

Every packet is converted into 10 numbers before the neural network sees it:

| Index | Name | What It Measures | Attack Indicator |
|---|---|---|---|
| 0 | pkt_rate | Packets per second (normalised) | High = flood |
| 1 | byte_rate | Bytes per second (normalised) | High = data exfiltration |
| 2 | syn_ratio | SYN packets / total TCP packets | High = SYN flood |
| 3 | port_entropy | Randomness of destination ports | High = port scan |
| 4 | unique_dsts | Unique destination IPs seen | High = scanning |
| 5 | icmp_ratio | ICMP packets / total | High = ICMP flood |
| 6 | small_pkt_ratio | Packets under 64 bytes | High = SYN flood |
| 7 | dst_port_norm | Destination port / 65535 | Context signal |
| 8 | protocol | TCP/UDP/ICMP/other | Context signal |
| 9 | time_of_day | Hour / 24 | Baseline context |

A SYN flood produces a vector where `pkt_rate=1.0`, `syn_ratio=1.0`, and `small_pkt_ratio=1.0` simultaneously. Normal web browsing might show `pkt_rate=0.02`, `syn_ratio=0.1`, `port_entropy=0.0`. The neural network learns to separate these patterns.

### The 5 Actions

| ID | Name | What It Does |
|---|---|---|
| 0 | ALLOW | Accept the packet, do nothing |
| 1 | BLOCK_IP | Insert `iptables -I FORWARD -s <ip> -j DROP` |
| 2 | RATE_LIMIT | Insert hashlimit rule capping bandwidth from this IP |
| 3 | LOG_WATCH | Accept but add to watchlist for closer monitoring |
| 4 | BLOCK_PORT | Insert rule blocking this specific port from this IP |

### The Reward Function

```
+10  blocked a confirmed attack
+1   allowed clean traffic
-5   blocked legitimate traffic (false positive)
-10  allowed confirmed attack (false negative)
+5   rate-limited an attack (good catch, soft action)
-1   rate-limited clean traffic (unnecessary)
+2   logged an attack for inspection
+0.5 logged clean traffic
```

The asymmetry is intentional. False negatives (letting attacks through) are penalised twice as harshly as false positives (blocking clean traffic). For a security system, missing an attack is worse than occasionally inconveniencing a legitimate user.

### The DQN Architecture

```
Input: 10 features
    │
    ▼
Dense(128, ReLU)
    │
BatchNormalization
    │
Dense(128, ReLU)
    │
BatchNormalization
    │
Dense(64, ReLU)
    │
Dense(5, linear)  ← Q-value for each action
    │
    ▼
Output: 5 Q-values
Select action with highest Q-value (or random during exploration)
```

Total parameters: 27,525 — tiny by ML standards. This is intentional. A firewall needs to make decisions in milliseconds. A small network is fast enough.

**Why Huber loss instead of MSE:** Mean squared error (MSE) squares the error, which means very large errors (outliers) dominate training and cause instability. Huber loss behaves like MSE for small errors and like MAE for large errors. This makes RL training much more stable when early random actions produce large negative rewards.

**Why a target network:** The DQN algorithm uses two copies of the network — a policy network (updated every training step) and a target network (updated every 100 steps). If we trained against the policy network itself, the target values would chase the network weights and the training would spiral. The stable target network prevents this.

---

### Step 2.1 — Install the Python Stack

On gw-dmz:

```bash
mkdir -p ~/rl-firewall/{agent,capture,rules,metrics,dashboard,logs,models}
cd ~/rl-firewall
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install scapy netfilterqueue tensorflow numpy pandas prometheus-client flask
```

**What a virtual environment is:** `python3 -m venv venv` creates an isolated Python installation inside the `venv` folder. Packages you install inside it do not affect the system Python. This prevents version conflicts and makes the project portable.

**Why netfilterqueue:** This is the Python binding for Linux's NFQUEUE system. It lets Python code intercept packets that the kernel has held in the queue, inspect them, and decide to accept or drop them. Without this, we cannot hook Python into the live packet stream.

**Why Scapy:** Scapy is a Python library that can parse every common network protocol. Given raw bytes from the kernel, Scapy turns them into structured objects: `packet[IP].src`, `packet[TCP].flags`, `packet[UDP].dport`. This is much easier than writing your own packet parser.

### Step 2.2 — Load the Kernel Module

```bash
sudo modprobe nfnetlink_queue
```

**What this does:** `modprobe` loads a kernel module — a piece of code that extends what the Linux kernel can do without rebooting. `nfnetlink_queue` is the module that implements the NFQUEUE system. Without it, creating a queue fails with `OSError: Failed to create queue 0`.

### Mistakes I Made

**OSError: Failed to create queue 0 even after loading the module:**

```bash
sudo cat /proc/net/netfilter/nfnetlink_queue
```

Output: `0  18374  0 2  4016  0  0  3  1`

The first column (0) is the queue number. The second column (18374) is the PID of the process holding it. A previous run of the script had not cleaned up. Fix:

```bash
sudo kill -9 18374
```

**Lesson learned:** Always check `/proc/net/netfilter/nfnetlink_queue` before starting the agent. If a PID appears there, kill it first.

---

### Step 2.3 — Set Up nfqueue iptables Rules

```bash
sudo bash ~/rl-firewall/rules/setup_nfqueue.sh
```

The script runs:

```bash
iptables -F FORWARD
iptables -P FORWARD DROP
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -i enp2s0 -o enp1s0 -m state --state NEW -j NFQUEUE --queue-num 0
iptables -A FORWARD -i enp1s0 -o enp2s0 -m state --state NEW -j NFQUEUE --queue-num 0
```

**Why only NEW connections go to the queue:** Connection tracking (`conntrack`) tracks the state of every TCP connection. Once a connection is established, subsequent packets are `RELATED` or `ESTABLISHED` and skip the queue entirely — they are allowed through immediately. Only the *first* packet of a new connection needs the agent's decision. This dramatically reduces the load on the RL agent.

**Why default FORWARD policy is DROP:** This is the "fail closed" principle. If the RL agent crashes and stops processing the queue, new connection packets queue up but are never released. The iptables default DROP means they eventually time out safely rather than slipping through. You can always restore normal forwarding with the teardown script.

### The Safety Net

```bash
sudo bash ~/rl-firewall/rules/teardown_nfqueue.sh
```

Always keep this handy. If the RL agent crashes or gets into a bad state, running the teardown script instantly restores normal forwarding. This is the most important operational procedure in the whole project.

---

### Step 2.4 — Run the Live Firewall

```bash
cd ~/rl-firewall
sudo venv/bin/python rl_firewall.py
```

In a second terminal:

```bash
tail -f ~/rl-firewall/logs/firewall.log
```

From client-lan, generate traffic:

```bash
sudo bash ~/traffic_sim.sh 5
```

You will see decisions appearing in real time:

```
[decision] 10.0.98.200→8.8.8.8:0 action=LOG_WATCH pkt_rate=0.00 syn_ratio=0.00 reward=0.5
[decision] 10.0.98.200→104.20.23.154:80 action=BLOCK_PORT pkt_rate=0.00 syn_ratio=0.00 reward=-4.0
```

**Early behaviour:** With epsilon at 1.0 (fully random), the agent makes random decisions including blocking legitimate traffic. This is expected and necessary — it is *exploring* the space of possible actions to discover which ones lead to good rewards. As the replay buffer fills past 1000 samples and training begins, epsilon decays and the agent starts exploiting what it has learned.

### Mistakes I Made

**Agent blocking the only client during exploration:**

The agent randomly chose `BLOCK_IP` on `10.0.98.200` (the only client machine). This inserted a DROP rule and the client lost all connectivity — including the ability to generate more training data.

Fix: add a training whitelist that downgrades BLOCK_IP to LOG_WATCH for known safe IPs during the exploration phase:

```python
SAFE_IPS = {"10.0.98.200", "10.0.98.100"}

def apply_action(action, src_ip, dst_port):
    if src_ip in SAFE_IPS and action in (1, 4):
        action = 3  # downgrade to LOG_WATCH
```

**Lesson learned:** In a learning environment where you control the traffic source, protect that source from being blocked. In a production deployment, you would instead tune epsilon decay faster and seed the replay buffer with pre-labelled traffic before going live.

---

## Part 3 — Observability

### Prometheus

Prometheus is a time-series database that regularly scrapes metrics from HTTP endpoints. The RL firewall exposes its metrics on port 9101. Prometheus collects them every 5 seconds and stores them.

```bash
sudo apt install -y prometheus prometheus-node-exporter
```

Add the RL firewall scrape target to `/etc/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'rl_firewall'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:9101']
```

### Grafana

Grafana reads from Prometheus and draws graphs.

```bash
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install -y grafana
sudo systemctl enable --now grafana-server
```

Access Grafana at `http://10.0.98.1:3000`. Default credentials: `admin` / `admin`.

Add Prometheus as a data source: Connections → Data Sources → Add → Prometheus → URL: `http://localhost:9090` → Save & Test.

Import the dashboard JSON file from `~/rl-firewall/dashboard/rl_firewall_dashboard.json`.

### Metrics Exposed

| Metric | What It Tracks |
|---|---|
| `rl_firewall_packets_total` | Total packets the agent has decided on |
| `rl_firewall_flows_active` | Currently tracked flows in the flow table |
| `rl_firewall_blocked_ips` | IPs currently under a DROP rule |
| `rl_firewall_epsilon` | Exploration rate (1.0 = random, 0.05 = learned) |
| `rl_firewall_total_reward` | Cumulative reward over all decisions |
| `rl_firewall_avg_loss` | Average training loss for the last 100 gradient steps |
| `rl_firewall_action_*` | Count of each action type taken |
| `rl_firewall_buffer_size` | Number of transitions stored in replay buffer |

### Mistakes I Made

**Duplicate job name in prometheus.yml:** I ran the `tee -a` command twice by mistake. Prometheus refused to start with: `found multiple scrape configs with job name "rl_firewall"`. Fix: view the full config file, identify the duplicate, rewrite the file from scratch with a heredoc.

**State file permission denied:** The RL firewall runs as root (required for iptables). It writes `agent_state.json` to `/root/rl-firewall/logs/`. The metrics exporter ran as the `adam` user and could not read `/root/`. Fix: run the exporter as root too with `sudo venv/bin/python metrics/exporter.py`.

**Port already in use:** Starting the exporter twice left port 9101 bound. Fix: `sudo pkill -f exporter.py` before restarting.

---

## Part 4 — Cloning the Lab

Cloning creates a second independent lab environment from snapshots of the existing VMs.

```bash
sudo virsh destroy gw-dmz
sudo virsh destroy client-lan

sudo virt-clone \
  --original gw-dmz \
  --name gw-dmz-clone \
  --file /var/lib/libvirt/images/gw-dmz-clone.qcow2

sudo virt-clone \
  --original client-lan \
  --name client-lan-clone \
  --file /var/lib/libvirt/images/client-lan-clone.qcow2
```

`virt-clone` copies the disk image and generates new MAC addresses automatically. New MACs prevent ARP conflicts when both original and clone are on the same bridge.

Create new isolated networks for the clone pair:

```bash
sudo virsh net-define /dev/stdin <<'EOF'
<network>
  <name>lab-dmz2</name>
  <bridge name="sw-r1-dmz"/>
</network>
EOF
sudo virsh net-start lab-dmz2
sudo virsh net-autostart lab-dmz2
```

Rewire the clones to the new networks using their new MAC addresses:

```bash
sudo virsh domiflist gw-dmz-clone   # note the MACs
sudo virt-xml gw-dmz-clone --remove-device --network mac=<old-dmz-mac>
sudo virt-xml gw-dmz-clone --remove-device --network mac=<old-lan-mac>
sudo virt-xml gw-dmz-clone --add-device --network network=lab-dmz2,model=virtio
sudo virt-xml gw-dmz-clone --add-device --network network=lab-lan2,model=virtio
```

Add two new interfaces to OpenWrt for the clone environment:

```bash
sudo virsh shutdown openwrt
sudo virt-xml openwrt --add-device --network network=lab-dmz2,model=virtio
sudo virt-xml openwrt --add-device --network network=lab-lan2,model=virtio
sudo virsh start openwrt
```

Configure the new interfaces in OpenWrt:

```bash
uci set network.dmz2=interface
uci set network.dmz2.device='eth4'
uci set network.dmz2.proto='static'
uci set network.dmz2.ipaddr='10.0.196.1'
uci set network.dmz2.netmask='255.255.255.0'
uci set network.lan2=interface
uci set network.lan2.device='eth5'
uci set network.lan2.proto='static'
uci set network.lan2.ipaddr='10.0.198.254'
uci set network.lan2.netmask='255.255.255.0'
uci commit network
service network restart
```

Reconfigure gw-dmz-clone with new subnet addresses (10.0.196.x and 10.0.198.x) and update its dnsmasq to serve the new range. The result is two completely independent lab environments sharing one OpenWrt router.

---

## Security Best Practices Applied

### Network Segmentation

Every segment is isolated by default. Traffic between segments only flows if an explicit forwarding rule exists in OpenWrt. The LAN cannot reach the MGMT segment. The DMZ cannot reach the LAN directly. This limits blast radius — if client-lan is compromised, the attacker cannot pivot to the management plane without going through two firewalls.

### Management Network Isolation

The MGMT segment (10.0.99.0/24) has no client machines. Only the Mint host's veth pair has an address there. This means administrative access to OpenWrt requires being on the host machine. A compromised client VM cannot reach the router's management interface.

### Default Deny Firewall

The RL firewall sets iptables default FORWARD policy to DROP before starting the nfqueue rules. This means any packet not explicitly handled falls off the bottom and is silently discarded. Explicit ACCEPT rules are required for traffic to pass.

### MAC-Locked Network Profiles

After experiencing interface name confusion during VM cloning, I locked each NetworkManager connection profile to the physical MAC address of its intended NIC. Even if Linux assigns interface names in a different order, the profile binds to the correct hardware.

### Automatic Unblocking

The RL agent's block rules expire after 300 seconds. A background thread checks every 30 seconds and removes expired DROP rules. This prevents the firewall from permanently locking out legitimate hosts due to early-training false positives.

---

## Troubleshooting Reference

### Network Connectivity

```bash
ip addr show                    # show all interface addresses
ip route show                   # show routing table
ping -c 3 10.0.98.1            # test gateway reachability
ping -c 3 8.8.8.8              # test internet (bypass DNS)
ping -c 3 google.com           # test DNS + internet
traceroute 8.8.8.8             # show each hop to internet
```

### iptables

```bash
sudo iptables -L FORWARD -n -v   # show all forward rules with packet counts
sudo iptables -t nat -L -n -v    # show NAT rules
sudo iptables -F FORWARD         # flush (delete) all forward rules
sudo iptables -P FORWARD ACCEPT  # set default policy to accept
```

### libvirt / VMs

```bash
sudo virsh list --all            # list all VMs and their states
sudo virsh domiflist openwrt     # show OpenWrt's network interfaces
sudo virsh net-list --all        # list all virtual networks
sudo virsh console openwrt       # connect to OpenWrt text console
sudo virsh start openwrt         # start a stopped VM
sudo virsh destroy openwrt       # force-stop a VM (like pulling the power)
```

### nfqueue

```bash
sudo cat /proc/net/netfilter/nfnetlink_queue   # show queue status and holding PID
sudo modprobe nfnetlink_queue                  # load kernel module
lsmod | grep nf                               # verify module is loaded
```

### NetworkManager

```bash
nmcli connection show            # list all connection profiles
nmcli device status              # show device state
nmcli connection up <name>       # activate a connection
nmcli connection modify <name> ipv4.method manual ipv4.addresses 10.0.98.1/24
```

### Services

```bash
sudo systemctl status prometheus grafana-server dnsmasq --no-pager
sudo journalctl -u grafana-server -f    # live logs for grafana
sudo systemctl restart prometheus       # restart prometheus
```

### RL Firewall Logs

```bash
tail -f ~/rl-firewall/logs/firewall.log   # live agent decisions
tail -f ~/rl-firewall/logs/blocked.log    # blocked IP log
cat ~/rl-firewall/logs/agent_state.json   # current agent stats
curl -s http://localhost:9101/metrics | grep rl_firewall   # prometheus metrics
```

---

## Lessons Learned

**Interface names cannot be assumed.** After cloning a VM, the new VM's network interfaces got the same names (`enp1s0`, `enp2s0`) but the MAC addresses changed. NetworkManager's profile was tracking the old MAC — so it bound to the wrong physical card. The fix was to explicitly lock each profile to the MAC it should follow. I now verify interface-to-profile binding immediately after any VM clone operation.

**Cloud-init is persistent and aggressive.** On Ubuntu 24.04, the `/etc/netplan/50-cloud-init.yaml` file gets regenerated if you do not tell cloud-init to stop managing network configuration. I removed the file once and it came back on reboot. The correct fix is to create `/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` with `network: {config: disabled}` — this tells cloud-init to leave networking alone permanently.

**Two DHCP servers on one network causes unpredictable failures.** When I forgot to disable OpenWrt's DHCP on the LAN segment, some clients got addresses from OpenWrt and some from gw-dmz. The ones from OpenWrt had the wrong gateway (10.0.98.254 instead of 10.0.98.1) and could not route through the RL firewall at all. Always verify that exactly one DHCP server exists per segment.

**Prometheus YAML is whitespace-sensitive.** Using `tee -a` (append mode) twice created a duplicate job name. Prometheus refused to start with a cryptic error. Now I always view the full config file before restarting Prometheus and use heredocs to write the entire file at once rather than appending.

**An RL agent in full exploration mode will block its only training source.** Early in training, epsilon is 1.0 meaning purely random actions. The agent randomly selected BLOCK_IP for the only client on the network. This stopped all training data. The fix was to add a whitelist that downgrades block actions to log-watch for known training hosts.

**Kernel modules do not persist across reboots by default.** `modprobe nfnetlink_queue` works for the current session only. After a reboot, the module is gone and the RL agent fails silently. Adding the module name to `/etc/modules-load.d/nfqueue.conf` makes it load at boot automatically.

---

## What I Would Add Next

**WireGuard VPN:** Add a WireGuard endpoint on OpenWrt so I can reach the lab securely from outside the house. This would also let me test the RL firewall against actual remote attack simulation.

**Wazuh SIEM:** Deploy Wazuh on a dedicated VM to collect logs from OpenWrt, gw-dmz, and client-lan. Feed Wazuh alerts back into the RL reward function as confirmation labels — replacing the heuristic reward with ground-truth signals from a real security tool.

**Pre-training on labelled datasets:** The UNSW-NB15 and CIC-IDS-2018 datasets contain millions of labelled packets. Pre-training the DQN on this data before connecting it to live traffic would dramatically accelerate convergence.

**PPO instead of DQN:** Proximal Policy Optimization (PPO) is generally more stable than DQN for continuous training environments. A future version would switch from value-based to policy-gradient learning.

**Ansible for reproducibility:** Every manual configuration step in this guide should eventually be an Ansible playbook. A single `ansible-playbook site.yml` should be able to rebuild the entire lab from scratch.

**Security Onion:** Replace the custom observability stack with Security Onion for full IDS, NSM, and SIEM capabilities. The RL firewall would become one component feeding into a professional security operations platform.

---

## Folder Structure

```
~/lab/
├── scripts/
│   ├── fresh-openwrt-setup.sh    # builds OpenWrt VM from scratch
│   ├── lab-up.sh                 # creates host veth pairs
│   └── openwrt-configure.sh      # configures OpenWrt interfaces
├── images/
│   └── xubuntu-24.04.4-desktop-amd64.iso
└── notes/
    ├── HOW-TO-BUILD-THE-LAB.md   # step-by-step lab guide
    └── PORTFOLIO.md              # this document

~/rl-firewall/
├── venv/                         # Python virtual environment
├── capture/
│   ├── __init__.py
│   └── feature_extractor.py      # nfqueue binding and flow stats
├── agent/
│   ├── __init__.py
│   └── dqn_agent.py              # DQN policy network and training loop
├── rules/
│   ├── setup_nfqueue.sh          # set iptables NFQUEUE rules
│   └── teardown_nfqueue.sh       # restore normal forwarding
├── metrics/
│   ├── exporter.py               # Prometheus HTTP metrics server
│   └── state_writer.py           # writes agent_state.json
├── dashboard/
│   └── rl_firewall_dashboard.json # Grafana dashboard definition
├── logs/
│   ├── firewall.log              # live agent decisions
│   ├── blocked.log               # blocked IP records
│   └── agent_state.json          # current agent stats (read by Prometheus)
├── models/
│   └── dqn_policy.keras          # saved model weights
├── traffic_sim.sh                # generates normal and attack traffic
└── rl_firewall.py                # main process — wires everything together
```

---

## Beginner Glossary

**Agent** — In reinforcement learning, the decision-maker. In this project, the DQN neural network that decides whether to allow or block each connection.

**Bridge** — A virtual switch inside the Linux kernel. Virtual machines connect to bridges the same way physical computers connect to a network switch.

**DHCP** — Dynamic Host Configuration Protocol. The system that automatically gives an IP address to a device when it joins a network. Like a receptionist handing out visitor badges.

**DQN** — Deep Q-Network. A type of reinforcement learning algorithm that uses a neural network to estimate the value (Q-value) of taking each action in each state.

**DMZ** — Demilitarised Zone. In networking, a segment that sits between the internal network and the internet, used for servers that need to be partially accessible from outside.

**DNS** — Domain Name System. Translates domain names (`google.com`) into IP addresses (`142.251.32.14`). Like a phone book for the internet.

**Epsilon** — In epsilon-greedy RL, the probability of taking a random action instead of the learned best action. Starts at 1.0 (fully random) and decays toward 0.05 (mostly learned).

**Feature vector** — A list of numbers that describes the current state of something. In this project, 10 numbers describing a network flow (packet rate, SYN ratio, etc.).

**Firewall** — Software (or hardware) that controls which network traffic is allowed to pass based on rules. Like a security guard checking IDs.

**Grafana** — A web application for creating dashboards that visualise time-series data. Reads from Prometheus and draws graphs.

**iptables** — The Linux kernel's built-in firewall tool. Commands written with `iptables` tell the kernel what to do with packets.

**KVM** — Kernel-based Virtual Machine. A Linux kernel feature that allows running multiple virtual machines with near-native performance.

**libvirt** — A toolkit for managing virtual machines. `virsh` is its command-line tool, virt-manager is its graphical interface.

**NAT** — Network Address Translation. Rewrites the source or destination address of a packet. Used to share one public IP among many private devices.

**NetworkManager** — A Linux service that manages network connections. Stores connection profiles and brings interfaces up automatically.

**NFQUEUE** — Netfilter Queue. A Linux kernel mechanism that lets user-space programs (like Python) receive and decide the fate of packets.

**Prometheus** — A monitoring system and time-series database. Scrapes metrics from HTTP endpoints and stores them.

**Replay buffer** — In DQN, a memory that stores past (state, action, reward, next_state) tuples. Random samples from this memory are used for training, which prevents the network from overfitting to recent experience.

**Reward** — A numerical signal that tells the RL agent whether its last action was good (positive) or bad (negative).

**Scapy** — A Python library for constructing and parsing network packets.

**SSH** — Secure Shell. An encrypted protocol for logging into and running commands on a remote computer.

**Subnet** — A portion of a larger network, defined by an IP address range. `10.0.98.0/24` means all addresses from 10.0.98.0 to 10.0.98.255.

**systemd** — The init system on most modern Linux distributions. Manages all services, starts them in the right order at boot.

**TensorFlow** — An open-source machine learning framework developed by Google. Used here for building and training the DQN neural network.

**UCI** — Unified Configuration Interface. OpenWrt's configuration system. All settings are stored in a structured format and modified with `uci set` / `uci commit`.

**veth pair** — A pair of virtual ethernet interfaces connected back-to-back. One end can be attached to a bridge; the other gets an IP address for host access.

**Virtual machine (VM)** — A software computer running inside a real computer. Has its own operating system, disk, and network interfaces, but shares the physical hardware.

**virsh** — The command-line tool for managing virtual machines via libvirt.

---

## Complete Command Reference

### Network Diagnostics

```bash
ip addr show                          # show all interfaces and addresses
ip route show                         # show routing table
ip link show                          # show link-layer info including MAC
bridge link                           # show bridge port memberships
ss -tlnp                              # show listening TCP ports
ping -c 3 <host>                      # test connectivity
traceroute <host>                     # trace packet path
tcpdump -i enp2s0 -n                  # capture live packets on interface
```

### libvirt / KVM

```bash
sudo virsh list --all                 # all VMs and states
sudo virsh start <vm>                 # start VM
sudo virsh shutdown <vm>              # graceful shutdown
sudo virsh destroy <vm>               # force stop
sudo virsh console <vm>               # connect text console
sudo virsh domiflist <vm>             # list VM network interfaces
sudo virsh net-list --all             # list all virtual networks
sudo virsh net-start <net>            # start a network
sudo virsh net-destroy <net>          # stop a network
sudo virsh net-undefine <net>         # delete a network definition
sudo virsh autostart <vm>             # enable VM autostart
sudo virt-install ...                 # create a new VM
sudo virt-clone --original <vm> ...   # clone a VM
sudo virt-xml <vm> --add-device ...   # add device to VM
sudo qemu-img create -f qcow2 ...     # create a virtual disk
sudo qemu-img resize <disk> <size>    # resize a virtual disk
```

### iptables

```bash
sudo iptables -L FORWARD -n -v        # list forward rules
sudo iptables -t nat -L -n -v         # list NAT rules
sudo iptables -F FORWARD              # flush forward chain
sudo iptables -P FORWARD DROP         # set default policy
sudo iptables -I FORWARD 1 -s <ip> -j DROP    # insert block rule
sudo iptables -D FORWARD -s <ip> -j DROP      # remove block rule
sudo netfilter-persistent save        # persist iptables rules across reboots
```

### OpenWrt UCI

```bash
uci show network                      # show all network config
uci set network.wan.device='eth0'     # set a value
uci commit network                    # save changes
service network restart               # apply changes
uci show firewall | grep zone         # show firewall zones
```

### Python / RL Firewall

```bash
source ~/rl-firewall/venv/bin/activate              # activate virtualenv
sudo venv/bin/python rl_firewall.py                 # start the firewall
sudo venv/bin/python metrics/exporter.py            # start metrics exporter
sudo pkill -f rl_firewall.py                        # stop the firewall
sudo cat /proc/net/netfilter/nfnetlink_queue        # check queue status
tail -f ~/rl-firewall/logs/firewall.log             # watch live decisions
```

### Package Management

```bash
sudo apt update                       # refresh package lists
sudo apt install -y <package>         # install a package
pip install <package>                 # install Python package into venv
```

---

*Built on Linux Mint with KVM, OpenWrt, TensorFlow, Prometheus, and Grafana.*
*All components are open source.*
*Total cost: $0.*
