# How to Build the OpenWrt + Gateway + Client Lab

This guide rebuilds a small virtual network on your Linux Mint computer using
free, open-source tools. By the end you will have three virtual machines
talking to each other and to the internet, completely separate from your
real home network.

No prior networking experience is required. Just copy each grey box into
your terminal, one at a time, and press Enter.

---

## What You Are Building

```
Internet
   |
   |  (your Mint computer's wifi/ethernet — never touched)
   |
[ libvirt NAT ]
   |
[ OpenWrt VM ]  <- a tiny virtual router
   |        \
 (MGMT)   (DMZ)
   |          \
   |     [ gw-dmz VM ]  <- a Xubuntu computer acting as a 2nd router
   |          |
   |        (LAN)
   |          |
   |     [ client-lan VM ]  <- a regular Xubuntu desktop
```

Three virtual machines, three virtual networks, one real internet connection
shared safely by all of them.

| Machine | What it is | Address |
|---|---|---|
| `openwrt` | Tiny router OS | WAN, MGMT 10.0.99.1, DMZ 10.0.96.1 |
| `gw-dmz` | Xubuntu acting as 2nd gateway | DMZ 10.0.96.x, LAN 10.0.98.1 |
| `client-lan` | Xubuntu desktop client | LAN 10.0.98.x (auto-assigned) |

---

## Before You Start

You need:

- A computer running **Linux Mint** with **virt-manager / libvirt / KVM** already installed
- At least **20 GB free disk space** (more if you want a bigger client VM)
- An **internet connection** to download the OpenWrt and Xubuntu images
- About **1–2 hours**, mostly waiting for downloads and installers

Everything below uses `sudo`, which means "do this as the administrator."
You'll be asked for your password the first time in each terminal session.

---

## Step 1 — Make a Folder for Everything

Open a terminal and type:

```bash
mkdir -p ~/lab/{scripts,images,notes}
```

This creates:
- `~/lab/scripts` — the setup scripts
- `~/lab/images` — downloaded disk images (OpenWrt, Xubuntu)
- `~/lab/notes` — this guide and any notes you take

---

## Step 2 — Build the OpenWrt Router VM

### 2.1 Download the OpenWrt image

```bash
wget --show-progress -O /tmp/openwrt.img.gz \
  https://downloads.openwrt.org/releases/23.05.3/targets/x86/64/openwrt-23.05.3-x86-64-generic-ext4-combined.img.gz
```

### 2.2 Unpack it

```bash
gunzip -f /tmp/openwrt.img.gz
```

You'll see a message about "trailing garbage ignored" — this is normal and
not a problem.

### 2.3 Move it into place and resize it

OpenWrt images are tiny by default. We resize it so there is room for extra
software later.

```bash
sudo mv /tmp/openwrt.img /var/lib/libvirt/images/openwrt-fresh.img
sudo qemu-img resize /var/lib/libvirt/images/openwrt-fresh.img 1G
sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/openwrt-fresh.img
sudo chmod 644 /var/lib/libvirt/images/openwrt-fresh.img
```

### 2.4 Create the virtual networks

These are the "virtual switches" that connect your VMs together. Think of
each one as an isolated network cable.

```bash
# Internet-facing network (shared with your real internet via NAT)
sudo virsh net-start nat-wan 2>/dev/null || sudo virsh net-define /dev/stdin <<'EOF'
<network>
  <name>nat-wan</name>
  <forward mode="nat"/>
  <bridge name="virbr1" stp="on" delay="0"/>
  <ip address="192.168.122.1" netmask="255.255.255.0">
    <dhcp>
      <range start="192.168.122.2" end="192.168.122.254"/>
    </dhcp>
  </ip>
</network>
EOF

# Three isolated lab networks: MGMT, LAN, DMZ
for net in "lab-mgmt:sw-r0-eth1" "lab-lan:sw-r0-eth2" "lab-dmz:sw-r0-eth3"; do
    name="${net%%:*}"
    br="${net##*:}"
    sudo virsh net-define /dev/stdin <<NETEOF
<network>
  <name>${name}</name>
  <bridge name="${br}"/>
</network>
NETEOF
    sudo virsh net-start "$name"
    sudo virsh net-autostart "$name"
    echo "Created: $name"
done
```

> **If you ever see an error like "bridge name already in use"** it means a
> network from a previous attempt is still hanging around. Fix it with:
> ```bash
> sudo virsh net-destroy <name-shown-in-error>
> sudo virsh net-undefine <name-shown-in-error>
> ```
> Then run the block above again.

### 2.5 Create the OpenWrt virtual machine

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

It only takes a few seconds to start because OpenWrt is tiny.

### 2.6 Connect to OpenWrt and fix its network

OpenWrt doesn't know which of its 4 virtual network cards is which yet —
we have to tell it.

```bash
sudo virsh console openwrt
```

Press **Enter** once. You should see a prompt like `root@OpenWrt:/#`.

Now copy and paste this whole block at once:

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

> **Note:** OpenWrt's LAN is deliberately set to `10.0.98.254`, not `.1`,
> because later the `gw-dmz` virtual machine becomes the real gateway for
> the LAN at `10.0.98.1`. This avoids the two machines fighting over the
> same address.

### 2.7 Set up the firewall and DHCP

Still inside the OpenWrt console, paste this whole block:

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
echo "Firewall and DHCP configured."
EOF
sh /tmp/fw.sh
```

> **Why is `dhcp.lan` deleted?** Because `gw-dmz` (a VM we build in Step 4)
> will become the LAN's DHCP server instead of OpenWrt. Only one device on
> a network should hand out addresses at a time.

### 2.8 Set the OpenWrt password

```bash
passwd root
```

Type a password twice (write it down — for example `labpass123`).

### 2.9 Test the internet works

```bash
ping -c 3 8.8.8.8
```

You should see replies. If you do, OpenWrt is online. Press **Ctrl + ]**
to leave the console and return to your normal Mint terminal.

---

## Step 3 — Connect Your Mint Computer to the Lab Networks

This step lets you (the human) reach into the lab from your normal
terminal — for example to SSH into OpenWrt directly.

### 3.1 Create the script

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

echo "Lab host interfaces are up."
echo "ssh root@10.0.99.1   -> OpenWrt MGMT"
echo "ping 10.0.98.1        -> LAN gateway (after gw-dmz is built)"
echo "ping 10.0.96.1        -> OpenWrt DMZ"
```

### 3.2 Run it

```bash
chmod +x ~/lab/scripts/lab-up.sh
sudo bash ~/lab/scripts/lab-up.sh
```

> **Run this script again any time you restart your Mint computer.**
> These connections don't survive a reboot, but everything else does.

### 3.3 Test SSH access to OpenWrt

```bash
ssh root@10.0.99.1
```

Type `yes` if asked about the host key, then enter the password you set
in Step 2.8. If you get a login prompt, it worked! Type `exit` to leave.

---

## Step 4 — Build the Gateway VM (`gw-dmz`)

This is a regular Xubuntu desktop that will act as a second, smaller
router sitting between OpenWrt and your client computer.

### 4.1 Download Xubuntu

```bash
wget -P ~/lab/images/ \
  https://cdimage.ubuntu.com/xubuntu/releases/24.04/release/xubuntu-24.04.4-desktop-amd64.iso
```

This is about 4 GB and may take several minutes.

### 4.2 Create the virtual hard disk

```bash
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/gw-dmz.qcow2 20G
```

### 4.3 Create the virtual machine

```bash
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

### 4.4 Run the installer

Open the **virt-manager** app (search for it in your applications menu, or
type `virt-manager` in a terminal). Double-click **gw-dmz**. A normal
Xubuntu installer window will appear.

Go through it like installing on a real computer:

- Pick your language and keyboard layout
- **Computer's name:** `gw-dmz`
- **Username:** anything you like (e.g. `admin`)
- **Password:** anything you'll remember
- **Disk:** choose "Erase disk and install Xubuntu" — this is safe, it only
  affects the small 20 GB virtual disk, not your real computer
- Let it finish and reboot

### 4.5 Open a terminal inside gw-dmz and check the network cards

```bash
ip addr show
```

You should see two network cards (probably `enp1s0` and `enp2s0`). One of
them should already have an address starting with `10.0.96.` (DMZ) or
`10.0.98.` (LAN). If one shows no address at all, refresh it:

```bash
nmcli device disconnect enp1s0
nmcli device connect enp1s0
```

(Replace `enp1s0` with whichever card has no address.)

### 4.6 Give the LAN-facing card a fixed address

Find out which card is on the LAN network (it's the one with a
`10.0.98.x` address). In our example it was `enp2s0`. The connection
profile is usually called `netplan-enp2s0` — check with:

```bash
nmcli connection show
```

Then set it to a fixed, unchanging address:

```bash
sudo nmcli connection modify netplan-enp2s0 ipv4.method manual ipv4.addresses 10.0.98.1/24
```

> **Important — a common snag:** Ubuntu sometimes has a leftover automatic
> configuration file that fights with this setting. If the address doesn't
> stick, check for it and remove it:
> ```bash
> cat /etc/netplan/50-cloud-init.yaml
> ```
> If it says `dhcp4: true`, remove it and tell Ubuntu not to recreate it:
> ```bash
> sudo rm /etc/netplan/50-cloud-init.yaml
> echo "network: {config: disabled}" | sudo tee /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
> sudo netplan apply
> ```

Confirm it worked:

```bash
ip addr show enp2s0
```

You should see `10.0.98.1/24` listed.

### 4.7 Turn on internet sharing (routing)

```bash
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
```

### 4.8 Install the software that shares the internet and hands out addresses

```bash
sudo apt update
sudo apt install -y dnsmasq iptables-persistent
```

If asked to save firewall rules, choose **Yes** for both questions that
appear.

### 4.9 Set up the traffic-sharing rules

Replace `enp1s0` and `enp2s0` below if your card names are different
(`enp1s0` = the DMZ/uplink side, `enp2s0` = the LAN side).

```bash
sudo iptables -t nat -A POSTROUTING -o enp1s0 -j MASQUERADE
sudo iptables -A FORWARD -i enp2s0 -o enp1s0 -j ACCEPT
sudo iptables -A FORWARD -i enp1s0 -o enp2s0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo netfilter-persistent save
```

### 4.10 Set up dnsmasq to hand out addresses to LAN clients

```bash
sudo systemctl stop dnsmasq
sudo systemctl disable systemd-resolved
sudo rm -f /etc/resolv.conf
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf

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

### 4.11 Test it

```bash
ping -c 3 8.8.8.8
```

If you get replies, `gw-dmz` has internet and is ready to serve the LAN.

---

## Step 5 — Build the Client VM (`client-lan`)

This is the "ordinary computer" of the lab — the one that will get its
internet through `gw-dmz`, not directly from OpenWrt.

### 5.1 Create the virtual hard disk

```bash
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/client-lan.qcow2 60G
```

(60 GB used here for more headroom — feel free to use 20G like the others.)

### 5.2 Create the virtual machine

```bash
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

### 5.3 Run the installer

Open **virt-manager**, double-click **client-lan**, and install Xubuntu
the same way as before:

- **Computer's name:** `client-lan`
- **Username/password:** anything you like
- **Disk:** erase and install (only affects this VM's virtual disk)

### 5.4 Confirm it's working

Open a terminal inside `client-lan` and run:

```bash
ip addr show
ping -c 3 10.0.98.1
ping -c 3 8.8.8.8
ping -c 3 google.com
```

You should see:
- An address like `10.0.98.1xx` to `10.0.98.200` automatically assigned
- Successful replies from `10.0.98.1` (the gateway)
- Successful replies from `8.8.8.8` (raw internet)
- Successful replies from `google.com` (internet + working DNS names)

If all four work, **the lab is complete and fully functional.**

---

## Daily Use Cheat Sheet

| I want to... | Command |
|---|---|
| Bring the lab host networking up after a reboot | `sudo bash ~/lab/scripts/lab-up.sh` |
| Start the OpenWrt VM | `sudo virsh start openwrt` |
| Start the gateway VM | `sudo virsh start gw-dmz` |
| Start the client VM | `sudo virsh start client-lan` |
| Open the OpenWrt text console | `sudo virsh console openwrt` (Ctrl+] to exit) |
| SSH into OpenWrt | `ssh root@10.0.99.1` |
| Open a graphical VM window | `virt-manager` then double-click the VM |
| Stop a VM | `sudo virsh shutdown <name>` |
| List all VM statuses | `sudo virsh list --all` |
| List all lab networks | `sudo virsh net-list --all` |

---

## How the Whole Thing Fits Together

```
client-lan  (10.0.98.x)
     |  gets internet + address from gw-dmz's dnsmasq
     v
gw-dmz enp2s0  (10.0.98.1)        <- LAN gateway
     |  routes + shares internet
     v
gw-dmz enp1s0  (10.0.96.x)        <- gets address from OpenWrt
     |
     v
OpenWrt eth3 / DMZ  (10.0.96.1)
     |  routes + firewalls + shares internet
     v
OpenWrt eth0 / WAN  (DHCP address)
     |
     v
libvirt NAT  (shared with your real Mint computer)
     |
     v
Your real internet connection (untouched, always safe)
```

Nothing in this lab ever changes your real Wi-Fi, your real DNS, or your
real default route. Everything lives inside virtual machines and virtual
networks that only exist on your computer.

---

## If Something Breaks

**A VM won't get an IP address / no internet:**
Check the chain one hop at a time, starting from the broken machine and
working backward toward the internet, pinging each gateway in turn.

**"Bridge name already in use" when creating a network:**
An old network definition is still around. Find and remove it:
```bash
sudo virsh net-list --all
sudo virsh net-destroy <old-name>
sudo virsh net-undefine <old-name>
```

**A static IP keeps reverting to DHCP on a Xubuntu VM:**
Look for a leftover `/etc/netplan/50-cloud-init.yaml` file overriding your
settings (see Step 4.6).

**You changed something in OpenWrt and it stopped working:**
Re-run the configure block from Step 2.6 and the firewall block from
Step 2.7 — they're safe to run again.

---

*Lab built and documented for a personal home network testing
environment using Linux Mint, KVM/libvirt, OpenWrt 23.05.3, and
Xubuntu 24.04.4.*
