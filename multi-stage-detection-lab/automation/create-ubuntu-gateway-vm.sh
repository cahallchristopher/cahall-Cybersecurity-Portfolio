#!/bin/bash

# Ubuntu Gateway VM Creation Script
# Purpose: Automate creation of Ubuntu Server gateway VM
# Author: Christopher Cahall
# Date: 2026-01-28

set -euo pipefail

# Configuration
VM_NAME="Ubuntu-Gateway-SOAR"
ISO_PATH="$HOME/VirtualBox_ISOs/ubuntu-22.04.5-live-server-amd64.iso"
VM_RAM=2048
VM_DISK_SIZE=20480
VM_CPUS=2

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
error() { echo -e "${RED}[!]${NC} $1" >&2; exit 1; }

# Check if ISO exists
[[ ! -f "$ISO_PATH" ]] && error "Ubuntu ISO not found at $ISO_PATH"

# Check if VM already exists
if VBoxManage list vms | grep -q "\"$VM_NAME\""; then
    error "VM '$VM_NAME' already exists. Delete it first with: VBoxManage unregistervm '$VM_NAME' --delete"
fi

log "Creating VM: $VM_NAME"

# Create VM
VBoxManage createvm --name "$VM_NAME" --ostype Ubuntu_64 --register

# Configure VM
log "Configuring VM settings..."
VBoxManage modifyvm "$VM_NAME" \
    --memory $VM_RAM \
    --cpus $VM_CPUS \
    --boot1 dvd \
    --boot2 disk \
    --boot3 none \
    --boot4 none \
    --firmware bios \
    --rtcuseutc on \
    --graphicscontroller vmsvga \
    --vram 16

# Create disk
log "Creating virtual hard disk (${VM_DISK_SIZE}MB)..."
VBoxManage createhd \
    --filename "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi" \
    --size $VM_DISK_SIZE \
    --format VDI \
    --variant Standard

# Create SATA controller
log "Creating SATA storage controller..."
VBoxManage storagectl "$VM_NAME" \
    --name "SATA Controller" \
    --add sata \
    --controller IntelAhci \
    --portcount 2 \
    --bootable on

# Attach disk
VBoxManage storageattach "$VM_NAME" \
    --storagectl "SATA Controller" \
    --port 0 \
    --device 0 \
    --type hdd \
    --medium "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi"

# Create IDE controller for DVD
log "Creating IDE controller..."
VBoxManage storagectl "$VM_NAME" \
    --name "IDE Controller" \
    --add ide

# Attach ISO
log "Attaching Ubuntu ISO..."
VBoxManage storageattach "$VM_NAME" \
    --storagectl "IDE Controller" \
    --port 0 \
    --device 0 \
    --type dvddrive \
    --medium "$ISO_PATH"

# Configure network
log "Configuring network adapters..."
# Adapter 1: NAT (Internet)
VBoxManage modifyvm "$VM_NAME" \
    --nic1 nat \
    --nictype1 82540EM \
    --cableconnected1 on

# Adapter 2: Internal Network (Lab)
VBoxManage modifyvm "$VM_NAME" \
    --nic2 intnet \
    --intnet2 "SOARLab" \
    --nictype2 82540EM \
    --cableconnected2 on

log "VM created successfully!"
echo ""
echo "VM Details:"
echo "  Name: $VM_NAME"
echo "  RAM: ${VM_RAM}MB (2GB)"
echo "  CPUs: $VM_CPUS"
echo "  Disk: ${VM_DISK_SIZE}MB (20GB)"
echo "  Network 1: NAT (Internet access)"
echo "  Network 2: Internal 'SOARLab' (Lab network)"
echo ""
echo "Start VM with:"
echo "  VBoxManage startvm '$VM_NAME'"
echo ""
echo "Or launch GUI:"
echo "  VirtualBox &"
