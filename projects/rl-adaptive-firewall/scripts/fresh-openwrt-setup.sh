
#!/bin/bash
# ============================================================
# fresh-openwrt-setup.sh
# Run on Linux Mint HOST as: sudo bash fresh-openwrt-setup.sh
#
# What this does:
#   1. Tears down the old OpenWrt VM completely
#   2. Cleans up leftover host bridges/veths from old lab
#   3. Downloads fresh OpenWrt 23.05.3 x86/64 image
#   4. Resizes it and places it in /var/lib/libvirt/images/
#   5. Creates the isolated lab bridges via virsh
#   6. Starts nat-wan
#   7. Defines and creates the new VM via virt-install
#   8. Prints exact SSH instructions for first boot
#
# Network layout:
#   eth0 → nat-wan   (WAN  — DHCP from libvirt NAT)
#   eth1 → lab-mgmt  (MGMT — 10.0.99.0/24)
#   eth2 → lab-lan   (LAN  — 10.0.98.0/24  Xubuntu clients)
#   eth3 → lab-dmz   (DMZ  — 10.0.96.0/24  gateway VM)
#
# Your Linux Mint DNS, default route, and wlo1 are never touched.
# ============================================================

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'
BLD='\033[1m'; RST='\033[0m'
log()  { echo -e "${GRN}[setup]${RST} $*"; }
warn() { echo -e "${YLW}[warn]${RST}  $*"; }
die()  { echo -e "${RED}[error]${RST} $*"; exit 1; }

[[ $EUID -ne 0 ]] && die "Run with sudo: sudo bash $0"

# ── Config ───────────────────────────────────────────────────
OPENWRT_VERSION="23.05.3"
OPENWRT_IMG_GZ="openwrt-${OPENWRT_VERSION}-x86-64-generic-ext4-combined.img.gz"
OPENWRT_URL="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/x86/64/${OPENWRT_IMG_GZ}"
DEST="/var/lib/libvirt/images/openwrt-fresh.img"
VM_NAME="openwrt"

# Lab bridges (host side)
LAB_BRIDGES="sw-r0-eth0 sw-r0-eth1 sw-r0-eth2 sw-r0-eth3"

# Libvirt isolated networks (one per lab bridge)
# format: "libvirt-net-name:bridge-name"
LAB_NETS=(
    "lab-mgmt:sw-r0-eth1"
    "lab-lan:sw-r0-eth2"
    "lab-dmz:sw-r0-eth3"
)

# Veths to clean from old setup
OLD_VETHS="veth-mgmt-h veth-lan-h veth-dmz-h veth0 veth-mgmt-b veth-lan-b veth-dmz-b veth1"
# ── End Config ───────────────────────────────────────────────

# ════════════════════════════════════════════════════════════
# STEP 1 — Tear down old VM
# ════════════════════════════════════════════════════════════
log "Step 1/7 — Removing old OpenWrt VM..."
if virsh dominfo "$VM_NAME" &>/dev/null; then
    state=$(virsh domstate "$VM_NAME")
    if [[ "$state" == "running" ]]; then
        log "  Stopping VM..."
        virsh destroy "$VM_NAME" || true
    fi
    log "  Undefining VM (removing all storage)..."
    virsh undefine "$VM_NAME" --remove-all-storage 2>/dev/null || \
    virsh undefine "$VM_NAME" || true
    log "  ✓ Old VM removed"
else
    log "  No existing VM named '$VM_NAME' found, skipping"
fi

# Clean up old image if still present
for old in /var/lib/libvirt/images/openwrt*.img \
           /var/lib/libvirt/images/openwrt*.qcow2; do
    [[ -f "$old" ]] && { rm -f "$old"; log "  ✓ Removed old image: $old"; }
done

# ════════════════════════════════════════════════════════════
# STEP 2 — Clean up old host interfaces
# ════════════════════════════════════════════════════════════
log "Step 2/7 — Cleaning up old lab interfaces..."
for v in $OLD_VETHS; do
    if ip link show "$v" &>/dev/null; then
        ip link del "$v" 2>/dev/null && log "  ✓ Removed $v"
    fi
done
for br in $LAB_BRIDGES; do
    if ip link show "$br" &>/dev/null; then
        ip link set "$br" down 2>/dev/null || true
        ip link del "$br" 2>/dev/null && log "  ✓ Removed bridge $br"
    fi
done

# Clean up old libvirt lab networks
for entry in "${LAB_NETS[@]}"; do
    netname="${entry%%:*}"
    if virsh net-info "$netname" &>/dev/null; then
        virsh net-destroy "$netname" 2>/dev/null || true
        virsh net-undefine "$netname" && log "  ✓ Removed libvirt net: $netname"
    fi
done
log "  ✓ Host interfaces clean"

# ════════════════════════════════════════════════════════════
# STEP 3 — Download fresh OpenWrt image
# ════════════════════════════════════════════════════════════
log "Step 3/7 — Downloading OpenWrt ${OPENWRT_VERSION}..."
TMP="/tmp/${OPENWRT_IMG_GZ}"
if [[ -f "$TMP" ]]; then
    warn "  Already downloaded at $TMP, skipping download"
else
    wget --show-progress -O "$TMP" "$OPENWRT_URL"
fi

log "  Decompressing..."
gunzip -f "$TMP"
EXTRACTED="/tmp/${OPENWRT_IMG_GZ%.gz}"

log "  Moving to $DEST..."
mv "$EXTRACTED" "$DEST"

log "  Resizing to 1G for package headroom..."
qemu-img resize "$DEST" 1G

# Fix ownership so libvirt can read it
chown libvirt-qemu:kvm "$DEST" 2>/dev/null || \
chown root:root "$DEST"
chmod 644 "$DEST"
log "  ✓ Image ready: $DEST"

# ════════════════════════════════════════════════════════════
# STEP 4 — Ensure nat-wan is running
# ════════════════════════════════════════════════════════════
log "Step 4/7 — Starting nat-wan network..."
if virsh net-info nat-wan &>/dev/null; then
    state=$(virsh net-info nat-wan | awk '/Active/{print $2}')
    if [[ "$state" != "yes" ]]; then
        virsh net-start nat-wan
    fi
    virsh net-autostart nat-wan
    log "  ✓ nat-wan active and set to autostart"
else
    warn "  nat-wan not found — creating a standard NAT network..."
    virsh net-define /dev/stdin <<'NATEOF'
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
NATEOF
    virsh net-start nat-wan
    virsh net-autostart nat-wan
    log "  ✓ nat-wan created and started"
fi

# ════════════════════════════════════════════════════════════
# STEP 5 — Create isolated lab networks in libvirt
# ════════════════════════════════════════════════════════════
log "Step 5/7 — Creating isolated lab networks..."
for entry in "${LAB_NETS[@]}"; do
    netname="${entry%%:*}"
    brname="${entry##*:}"

    if virsh net-info "$netname" &>/dev/null; then
        warn "  $netname already exists, skipping"
        continue
    fi

    virsh net-define /dev/stdin <<NETEOF
<network>
  <name>${netname}</name>
  <bridge name="${brname}"/>
</network>
NETEOF
    virsh net-start "$netname"
    virsh net-autostart "$netname"
    log "  ✓ Created isolated net: $netname → bridge $brname"
done

# ════════════════════════════════════════════════════════════
# STEP 6 — Define and create the VM
# ════════════════════════════════════════════════════════════
log "Step 6/7 — Defining new OpenWrt VM..."

virt-install \
  --name "$VM_NAME" \
  --memory 512 \
  --vcpus 1 \
  --disk "path=${DEST},format=raw,bus=virtio" \
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

log "  ✓ VM defined and started"

sleep 3

# ════════════════════════════════════════════════════════════
# STEP 7 — Print next steps
# ════════════════════════════════════════════════════════════
NATWANIP=$(virsh net-dumpxml nat-wan 2>/dev/null | grep -oP '(?<=address=")[^"]+' | head -1 || echo "192.168.122.1")

echo ""
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
echo -e "${GRN}  Fresh OpenWrt VM is booting!${RST}"
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
echo ""
echo -e "  Interface map inside OpenWrt:"
echo -e "  ${BLD}eth0${RST} → nat-wan   (WAN  — gets DHCP from libvirt)"
echo -e "  ${BLD}eth1${RST} → lab-mgmt  (MGMT — 10.0.99.0/24)"
echo -e "  ${BLD}eth2${RST} → lab-lan   (LAN  — 10.0.98.0/24  Xubuntu clients)"
echo -e "  ${BLD}eth3${RST} → lab-dmz   (DMZ  — 10.0.96.0/24  gateway VM)"
echo ""
echo -e "  ${YLW}Connect to OpenWrt console:${RST}"
echo -e "    ${BLD}virsh console openwrt${RST}"
echo -e "    (press Enter once if blank, Ctrl+] to exit)"
echo ""
echo -e "  ${YLW}Or SSH in after WAN gets a lease (~15 sec):${RST}"
echo -e "    ${BLD}ssh root@\$(arp -n | grep \$(virsh domiflist openwrt | awk '/nat-wan/{print \$5}') | awk '{print \$1}')${RST}"
echo -e "    (no password by default on fresh OpenWrt)"
echo ""
echo -e "  ${YLW}Next scripts to run:${RST}"
echo -e "    1. ${BLD}sudo bash ~/lab/scripts/lab-up.sh${RST}         ← host veth pairs"
echo -e "    2. ${BLD}sudo bash ~/lab/scripts/openwrt-configure.sh${RST} ← OpenWrt config"
echo ""
echo -e "${BLD}════════════════════════════════════════════════════════${RST}"
