Here's your content reformatted into clean, repository-friendly Markdown with consistent heading levels, callout structure, and improved readability.

# Project Journal

A chronological record of the build process. Each phase captures the objective, actions, failure points, and resolution.

Detailed debug traces are maintained in `TROUBLESHOOTING_GUIDE.md`.

This document records the system's evolution, architectural decisions, and lessons learned throughout the build process.

---

## Phase 1 — Clean Slate: Fresh OpenWrt VM

### Objective

Build a virtual router to isolate lab traffic from the host network without interfering with host DNS or routing.

### Actions

* Removed a legacy DNS-fix script and an associated NetworkManager dispatcher hook left over from earlier work.

* Inspected host interfaces:

  ```bash
  ip a
  ```

* Identified stale bridges (`sw-r0-eth0` through `sw-r0-eth3`) and leftover veth pairs from previous lab sessions.

* Found several veth interfaces holding DHCP leases on the same subnet as the home router, creating a potential routing-confusion risk.

* Chose to rebuild from a clean baseline instead of debugging an unknown environment.

* Downloaded the OpenWrt 23.05.3 x86/64 image.

### Outcome

A fresh OpenWrt VM was deployed using `virt-install`.

The first major issue surfaced immediately while bringing up the underlying libvirt networks. That investigation is covered in Phase 2.

---

## Phase 2 — The NetworkManager vs. libvirt Bridge War

### Objective

Create three isolated libvirt-managed networks:

* `lab-mgmt`
* `lab-lan`
* `lab-iot`

Each network would be bound to its own dedicated Linux bridge.

### Actions

* Defined each network with `virsh net-define`.
* Attempted activation with `virsh net-start`.

### Issues Observed

```text
error: Failed to start network lab-mgmt
error: error creating bridge interface sw-r0-eth1: File exists
```

Deleting the bridge with `ip link del` appeared to succeed, but the interface returned after every reboot with the same MAC address.

This became the key clue: persistent MAC addresses across reboots indicated a saved configuration rather than a process recreating the interface at runtime.

### Investigation

First, rule out active processes that might be recreating the bridges:

```bash
sudo clab inspect --all
ps aux | grep -E 'gns3|clab|containerlab|ovs'
docker ps
systemctl list-units --state=running | grep -v snap | grep -v docker | grep -v system
```

Results:

* No active Containerlab instances.
* No GNS3 or Open vSwitch processes.
* Only an unrelated DNS container was running.
* No other lab-related services were active.

Next, inspect NetworkManager:

```bash
sudo nmcli con show | grep -E 'sw-r0|bridge'
```

### Root Cause

NetworkManager contained persistent connection profiles for all four bridge names.

As a result:

* NetworkManager attempted to recreate and manage the bridges.
* libvirt attempted to create and manage the same bridges.

The competing ownership models caused a continuous conflict.

### Resolution

Delete the stale NetworkManager profiles:

```bash
sudo nmcli con delete <uuid-for-each-bridge>

virsh net-start lab-mgmt
virsh net-start lab-lan
virsh net-start lab-iot
```

### Outcome

```text
Name       State    Autostart   Persistent
-------------------------------------------
lab-iot    active   yes         yes
lab-lan    active   yes         yes
lab-mgmt   active   yes         yes
nat-wan    active   yes         yes
```

NetworkManager no longer contested bridge ownership, and libvirt networks started consistently.

---

## Phase 3 — Building the Router and Labeling Every Door

### Objective

Implement a four-zone network architecture with strict deny-by-default firewall policies.

The design includes four network zones:

* **WAN:** Upstream internet connection
* **MGMT:** Trusted administration network
* **LAN:** General-purpose lab segment
* **IOT:** Lower-trust, isolated segment

The guiding principle was simple: a compromised low-trust device should never be able to access management systems or trusted endpoints.

### Initial Discovery

The default interface assignments did not match the intended design.

OpenWrt assigned:

* `eth0` → LAN
* `eth1` → WAN

Rather than relying on assumptions, the actual interface bindings were verified before any configuration changes were made.

```bash
ip a
cat /etc/config/network
```

### Actions

* Verified interface-to-role mappings.

* Manually configured:

  * `/etc/config/network`
  * `/etc/config/firewall`
  * `/etc/config/dhcp`

* Bound each logical zone to its confirmed interface (`eth0`–`eth3`).

* Created dedicated DHCP scopes for MGMT, LAN, and IOT.

### Design Decisions

* Bound interfaces using verified device names instead of assumed numbering.

* Built explicit trust boundaries:

  * MGMT: Full trust
  * LAN: WAN-only forwarding
  * IOT: WAN-only forwarding

* Added explicit firewall rules:

  * `Block-IOT-to-LAN`
  * `Block-IOT-to-MGMT`

These rules are technically redundant because the zone policy already denies this traffic. They remain in place because explicit rules are easier to audit than implicit defaults.

* Restarted network and firewall services.
* Performed live connectivity testing.

### Verification

```bash
ping -c 3 8.8.8.8
```

```text
3 packets transmitted, 3 packets received, 0% packet loss
```

### Outcome

The four-zone architecture became fully operational.

| Zone | Purpose                     | Forwarding Policy |
| ---- | --------------------------- | ----------------- |
| MGMT | Administrative access       | WAN, LAN, IOT     |
| LAN  | General-purpose lab traffic | WAN only          |
| IOT  | Lower-trust devices         | WAN only          |

---

## Phase 4 — SSH Access and a Self-Inflicted IP Conflict

### Objective

Enable SSH access to OpenWrt and eliminate reliance on console administration.

### Actions

* Enabled and started the `dropbear` SSH service.
* Verified that port 22 was listening:

```bash
netstat -tlnp | grep 22
```

```text
tcp   0   0   0.0.0.0:22   0.0.0.0:*   LISTEN   1377/dropbear
```

* Attempted SSH access from the host.

### Issues Observed

SSH connections failed even though the service was listening on all interfaces.

### Root Cause

The host-side veth interface connected to the MGMT network used the same IP address as the OpenWrt gateway:

* Host veth: `10.0.99.1/24`
* OpenWrt MGMT gateway: `10.0.99.1/24`

Two devices sharing the same IP address on the same subnet created an address conflict and prevented reliable communication.

### Resolution

Assign a unique address to the host interface:

```bash
sudo ip addr del 10.0.99.1/24 dev veth-mgmt-h
sudo ip addr add 10.0.99.100/24 dev veth-mgmt-h
```

The lab bring-up script was updated to prevent the same issue on the LAN and IOT segments.

### Outcome

```bash
ssh root@10.0.99.1
```

SSH access succeeded immediately, eliminating the need for routine console access.

---

## Closing Summary

The environment stabilized after resolving two separate classes of problems:

1. A host-level ownership conflict between NetworkManager and libvirt.
2. A self-inflicted IP addressing conflict introduced by automation.

Both issues initially appeared to be deeper failures, but each was resolved by identifying the correct layer of the stack rather than continuing to troubleshoot symptoms.

---

## Final Architecture

| Zone | Purpose                     | Trust Level | Allowed Forwarding                          |
| ---- | --------------------------- | ----------- | ------------------------------------------- |
| WAN  | Upstream internet access    | Untrusted   | N/A                                         |
| MGMT | Administrative access       | Trusted     | WAN, LAN, IOT                               |
| LAN  | General-purpose lab segment | Restricted  | WAN only                                    |
| IOT  | Lower-trust segment         | Low trust   | WAN only; explicitly denied to LAN and MGMT |

---

## Key Lessons Learned

* Never assume interface-to-role assignments in a virtual appliance. Verify them using `ip a` and configuration files before making changes.
* Persistent state across reboots, such as identical MAC addresses, usually indicates a saved configuration rather than a running process.
* Treat automation scripts as potential sources of configuration drift.
* Layer explicit deny rules on top of default policies to improve auditability.
* Validate every phase with live testing. Configuration files are only the starting point; actual network behavior is the final proof.

