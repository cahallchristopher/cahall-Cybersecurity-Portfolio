#!/bin/bash
# Kali Linux VM Creation Script
# Purpose: Automate creation of Kali Red Team VM
# Author: Christopher Cahall
# Date: 2026-01-28

set -euo pipefail

# Configuration
VM_NAME="Kali-RedTeam-SOAR"
KALI_VBOX_PATH="${KALI_VBOX_PATH:-}"  # Path to .vbox file
VM_RAM=4096
VM_CPUS=2

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
error() { echo -e "${RED}[!]${NC} $1" >&2; exit 1; }
warn() { echo -e "${YELLOW}[*]${NC} $1"; }

# Check if VM already exists
if VBoxManage list vms | grep -q "\"$VM_NAME\""; then
    warn "VM '$VM_NAME' already exists!"
    echo "Delete it and start fresh? (y/n)"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Deleting existing VM..."
        VBoxManage unregistervm "$VM_NAME" --delete
    else
        error "Exiting. Delete VM manually."
    fi
fi

# Import pre-built Kali VM or create from scratch
if [ -n "$KALI_VBOX_PATH" ] && [ -f "$KALI_VBOX_PATH" ]; then
    log "Importing pre-built Kali VM..."
    VBoxManage import "$KALI_VBOX_PATH" \
        --vsys 0 \
        --vmname "$VM_NAME" \
        --memory $VM_RAM \
        --cpus $VM_CPUS
else
    log "Creating VM from scratch..."
    VBoxManage createvm --name "$VM_NAME" --ostype Debian_64 --register
    
    VBoxManage modifyvm "$VM_NAME" \
        --memory $VM_RAM \
        --cpus $VM_CPUS \
        --vram 128
    
    VBoxManage createhd \
        --filename "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi" \
        --size 81920
fi

# Configure network
log "Configuring network for SOARLab..."
VBoxManage modifyvm "$VM_NAME" \
    --nic1 intnet \
    --intnet1 "SOARLab"

log "✓ VM Created Successfully!"
log "  Name: $VM_NAME"
log "  RAM: ${VM_RAM}MB (4GB)"
log "  Network: Internal 'SOARLab'"
