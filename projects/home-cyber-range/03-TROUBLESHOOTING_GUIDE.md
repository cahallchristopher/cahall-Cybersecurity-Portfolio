# Troubleshooting Guide

Every significant issue encountered, with the actual symptoms, diagnostic commands, root cause, and resolution. Organized by category.

---

## Networking & Virtualization

### Issue: Bridges Respawning After Deletion (NetworkManager vs. libvirt)

**Symptoms**
`virsh net-start` failed repeatedly with `error creating bridge interface sw-r0-eth1: File exists`, even immediately after deleting the interface with `ip link del`. The interface returned with the same MAC address after a full host reboot.

**Environment**
Linux Mint host, NetworkManager active, libvirtd active, several leftover bridges and veth pairs from earlier lab sessions.

**Error Messages**
```text
error: Failed to start network lab-mgmt
error: error creating bridge interface sw-r0-eth1: File exists
```

**Investigation Process**
1. Confirmed it was a real bridge (not a simple link) via `ip -d link show sw-r0-eth1`, which printed full STP/bridge parameters
2. Ruled out GNS3/Containerlab: `sudo clab inspect --all` → `no clab`; `ps aux | grep -E 'gns3|clab|containerlab|ovs'` → nothing
3. Ruled out systemd units: `systemctl list-units --state=running | grep -v snap | grep -v docker | grep -v system` → only standard system services
4. Ruled out Docker: `docker ps` showed only an unrelated DNS sinkhole container
5. Rebooted the host entirely to rule out an ephemeral process. The bridge reappeared anyway, with the **same MAC address** — the key clue that this was a saved configuration, not a live process
6. Checked NetworkManager directly: `sudo nmcli con show | grep -E 'sw-r0|bridge'`

**Root Cause**
NetworkManager had persistent saved connection profiles for all four bridges, independently of libvirt's own attempt to create and own bridges of the same name. NetworkManager treated them as its own managed connections and kept recreating them.

**Resolution Steps**
```bash
sudo nmcli con delete <uuid-1>
sudo nmcli con delete <uuid-2>
sudo nmcli con delete <uuid-3>
sudo nmcli con delete <uuid-4>
virsh net-start lab-mgmt
virsh net-start lab-lan
virsh net-start lab-iot
```

**Verification Commands**
```bash
virsh net-list --all
```
```text
 Name       State    Autostart   Persistent
---------------------------------------------
 lab-iot    active   yes         yes
 lab-lan    active   yes         yes
 lab-mgmt   active   yes         yes
 nat-wan    active   yes         yes
```

**Prevention**
Before letting libvirt create a bridge with a given name, check `nmcli con show | grep <name>` first. Treat identical MAC addresses surviving a reboot as a strong signal of a saved configuration rather than a live process — `nmcli`, `systemctl`, and config-file searches are the tools to find the actual owner, not `ip link` alone.

---

### Issue: KVM Acceleration Unavailable

**Symptoms**
```text
error while starting pfsense-1: KVM acceleration cannot be used (/dev/kvm doesn't exist).
```

**Investigation**
```bash
ls -la /dev/kvm
```
Device node didn't exist.

**Root Cause**
The `kvm_intel`/`kvm_amd` kernel module wasn't loaded.

**Resolution**
```bash
sudo modprobe kvm_intel 2>&1 || sudo modprobe kvm_amd 2>&1
```

**Verification**
```bash
ls -la /dev/kvm
```
```text
crw-rw----+ 1 root kvm 10, 232 Jun 15 23:29 /dev/kvm
```

**Prevention**
Add the module to `/etc/modules` or equivalent so it loads automatically at boot instead of requiring a manual `modprobe` after every reboot.

---

### Issue: No VNC Viewer Installed

**Symptoms**
```text
Could not start VNC program with command 'vncviewer localhost:5900': [Errno 2] No such file or directory: 'vncviewer'
```

**Root Cause**
No VNC client installed on the host.

**Resolution**
```bash
sudo apt install tigervnc-viewer -y
```

---

### Issue: GNS3 "Can't create the link, the destination port is not free"

**Symptoms**
Attempting to connect a second device directly to a port on pfSense that already had one connection.

**Root Cause**
GNS3 links are strictly point-to-point — one cable, two ends, no exceptions.

**Resolution**
Inserted an `Ethernet Switch` node between pfSense's port and the multiple devices needing to share that segment.

---

### Issue: Configured Link Not Actually Connected Despite Correct Node Config

**Symptoms**
A Cloud node was correctly bound to the right host bridge, yet the host still couldn't reach a device behind it.

**Investigation**
Inspected the GNS3 project's `topology.links` array directly:
```bash
python3 -c "
import json
data = json.load(open('cyber-range.gns3'))
for link in data['topology']['links']:
    for node in link['nodes']:
        print(node)
    print('---')
"
```
This showed no link entry at all for the Cloud node in question, despite it appearing visually connected on the canvas.

**Root Cause**
The link had never actually been drawn/saved — a canvas interaction issue, not a configuration issue.

**Resolution**
Redrew the link in the GNS3 GUI.

**Prevention**
When a GNS3 link "looks" connected but traffic doesn't flow, check the project's actual `topology.links` JSON rather than trusting the canvas rendering.

---

## Virtualization: Disk & Image Configuration

### Issue: pfSense — "No disk(s) present to configure"

**Symptoms**
```text
Error
No disk(s) present to configure
```

**Investigation**
Inspected the GNS3 project's node properties directly:
```bash
python3 -c "
import json
data = json.load(open('cyber-range.gns3'))
for node in data['topology']['nodes']:
    if 'pfsense' in node.get('name','').lower():
        print(json.dumps(node['properties'], indent=2))
"
```
Output showed:
```text
"cdrom_image": "",
"hda_disk_image": "pfsense.iso",
"hda_disk_interface": "ide",
```

**Root Cause**
The pfSense ISO had been assigned to the `hda` (primary hard disk) slot instead of the CD-ROM slot. QEMU was presenting the ISO as if it were a writable disk, and there was no actual blank disk for the installer to partition.

**Resolution**
Edited the project file directly (with the GNS3 server stopped, to avoid file-lock conflicts):
```bash
pkill -f gns3server
python3 << 'EOF'
import json
path = "cyber-range.gns3"
with open(path) as f:
    data = json.load(f)
for node in data["topology"]["nodes"]:
    if "pfsense" in node.get("name", "").lower():
        props = node["properties"]
        props["cdrom_image"] = "pfsense.iso"
        props["hda_disk_image"] = "pfsense-hdb.qcow2"
        props["hda_disk_interface"] = "ide"
        props["hdb_disk_image"] = ""
        props["hdb_disk_interface"] = "none"
with open(path, "w") as f:
    json.dump(data, f, indent=4)
EOF
```

**Verification**
Relaunched GNS3, started the node, and the installer progressed to the actual disk-selection screen (`ada0` detected).

**Prevention**
Confirm via the project's `.gns3` file (or the GUI's CD/DVD tab specifically, not just the HDD tab) that an ISO is attached to the CD-ROM slot and a separate blank image is attached to the HDA slot — easy to conflate if "New Image" and "Browse for ISO" are used inconsistently across tabs.

---

### Issue: pfSense — Disk Too Small for Auto-Partitioning

**Symptoms**
```text
Error
These disks are smaller than the amount of requested swap (1g) and/or geli(8) (2g) partitions, which would
take 100% or more of each of the following selected disks: ada0
```

**Root Cause**
An 8GB blank disk was too small for pfSense's automatic UFS partitioning scheme, which reserves a fixed swap + geli allowance regardless of total disk size.

**Resolution**
```bash
pkill -f gns3server
find ~/GNS3/projects/cyber-range -iname "*.qcow2"
qemu-img resize <path-to-hda_disk.qcow2> 16G
```

**Verification**
```bash
qemu-img info <path-to-hda_disk.qcow2>
```
Re-ran the installer; partitioning succeeded with Auto (UFS), 16GB, MBR.

**Prevention**
Provision at least 16GB up front for any BSD/UFS-based lab VM rather than minimizing disk size.

---

## DNS & Syslog

### Issue: Syslog Forwarding — Multiple Layered Failures

**Symptoms**
Logs from Metasploitable2 (Ubuntu 8.04) never appeared in Wazuh's archive or alert index, despite the syslog config appearing correct.

**Environment**
Metasploitable2 (sysklogd, Ubuntu 8.04 Hardy, 2008-era), Wazuh 4.9 (Amazon Linux 2), pfSense firewall between them on different network segments.

**Investigation Process — four distinct sub-issues, found in sequence:**

**1. Standard `@host:port` syntax produced zero outbound packets**
```bash
echo "*.* @192.168.1.10:514" | sudo tee -a /etc/syslog.conf
sudo /etc/init.d/sysklogd restart
sudo tcpdump -i eth0 udp port 514 -c 5
```
No packets captured at all leaving the box.

**2. sysklogd needed remote forwarding explicitly enabled**
```bash
cat /etc/default/syslogd
```
```text
SYSLOGD=""
```
The `-r` flag (for remote UDP logging) was unset. Fixed:
```bash
sudo sed -i 's/SYSLOGD=""/SYSLOGD="-r"/' /etc/default/syslogd
sudo /etc/init.d/sysklogd restart
```

**3. Wazuh received packets at the network layer but never archived them**
```bash
sudo grep -i "metasploitable\|192.168.20" /var/ossec/logs/ossec.log
```
showed `wazuh-remoted` accepting the source subnet, but `archives.log` stayed empty. Checked:
```bash
sudo grep -A2 "<logall>" /var/ossec/etc/ossec.conf
```
```text
<logall>no</logall>
```
This silently drops anything from being archived unless it matches an existing rule. Fixed:
```bash
sudo sed -i 's/<logall>no<\/logall>/<logall>yes<\/logall>/' /var/ossec/etc/ossec.conf
sudo systemctl restart wazuh-manager
```

**4. The actual root cause — firewall blocking the traffic entirely**
After fixing 1–3, a direct ping test from Metasploitable2 to Wazuh's IP still failed completely:
```bash
ping -c 3 192.168.1.10
```
```text
3 packets transmitted, 0 received, 100% packet loss
```
This was the firewall doing exactly what it was designed to do — block DMZ from reaching LAN. The syslog traffic needed to reach Wazuh (on LAN) from Metasploitable2 (on DMZ), and the segmentation rules built in Phase 8 correctly prevented it.

**Root Cause**
A combination of three independent, layered issues: sysklogd's remote-forwarding flag being off, Wazuh's `<logall>` setting silently discarding unmatched logs, and — the actual blocker — the firewall correctly enforcing DMZ→LAN isolation, which had no exception for the syslog port.

**Resolution**
Added one narrow pfSense rule: DMZ → LAN allowed on UDP/514 only, positioned above the general DMZ→LAN block rule (first-match-wins ordering matters). Also replaced the fragile native sysklogd config with a simple, portable one-line forwarder that doesn't depend on sysklogd's quirky remote-logging behavior:
```bash
nohup bash -c 'tail -F /var/log/syslog | while read l; do echo "<14>$(date +"%b %d %H:%M:%S") metasploitable: $l" | nc -u -w1 192.168.1.10 514; done' > /dev/null 2>&1 &
```

**Verification**
```bash
sudo tail -f /var/ossec/logs/archives/archives.log
```
Showed Metasploitable2's logs arriving with correct source IP attribution. A real failed SSH login subsequently appeared as a fully parsed, MITRE-tagged alert in the Wazuh dashboard.

**Prevention**
When debugging a multi-hop log pipeline across segmented networks, verify connectivity at the network layer (`ping`, `tcpdump`) *before* assuming the issue is in application-layer config — in this case, three real config issues were fixed before the actual blocking cause (the firewall) was even considered.

---

## Linux Administration: Legacy & EOL Systems

### Issue: EPEL Repository Unavailable on Amazon Linux 2

**Symptoms**
```bash
sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
```
```text
Cannot open: https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm. Skipping.
Error: Nothing to do
```

**Root Cause**
Fedora's EPEL project no longer hosts the EL7 release package at that path; the URL pattern documented in most tutorials is stale.

**Resolution**
```bash
sudo amazon-linux-extras install epel -y
```
This is the AWS-maintained installation path specifically for Amazon Linux 2 and doesn't depend on Fedora's external hosting.

**Verification**
```bash
sudo yum search snort
```
Returned actual results, confirming the repo was active.

**Prevention**
For Amazon Linux 2 specifically, prefer `amazon-linux-extras` over manually-sourced EPEL RPM URLs, since AWS maintains that path directly.

---

### Issue: suricata-update Fails with FIPS/MD5 Error

**Symptoms**
```text
ValueError: error:060800A3:digital envelope routines:EVP_DigestInit_ex:disabled for fips
```

**Investigation**
```bash
cat /proc/sys/crypto/fips_enabled
openssl version
```
```text
1
OpenSSL 1.0.2k-fips  26 Jan 2017
```

**Root Cause**
The host has kernel-level FIPS mode enabled, which disables MD5 system-wide. `suricata-update`'s Python code uses MD5 purely for generating temp filenames (not for any security-relevant purpose), but Python's `hashlib.md5()` call fails outright under FIPS regardless of intent.

**Resolution**
Bypassed `suricata-update` entirely and downloaded/extracted the Emerging Threats ruleset manually:
```bash
wget https://rules.emergingthreats.net/open/suricata/emerging.rules.tar.gz
tar xzf emerging.rules.tar.gz
sudo cp rules/*.rules /var/lib/suricata/rules/
```

**Prevention**
On any FIPS-mode host, expect Python tools that use MD5 for non-cryptographic purposes (caching, temp filenames) to fail outright rather than warn. Check `/proc/sys/crypto/fips_enabled` early when a tool throws an unexplained `EVP_DigestInit_ex` error.

---

### Issue: Emerging Threats Ruleset URL Returns 410 Gone for Old Suricata Version

**Symptoms**
```bash
wget https://rules.emergingthreats.net/open/suricata-4.1.10/emerging.rules.tar.gz
```
```text
HTTP request sent, awaiting response... 410 Gone
```

**Root Cause**
Emerging Threats only hosts version-specific rule archives for a limited window; Suricata 4.1.10 (released 2019) had been pruned from their CDN.

**Resolution**
Used the generic/latest path instead, which Suricata 4.x can still mostly parse:
```bash
wget https://rules.emergingthreats.net/open/suricata/emerging.rules.tar.gz
```

**Prevention**
For old/pinned software versions, check whether a vendor's "latest" or "generic" rule/package path is more reliable than a version-pinned one that may have been pruned.

---

### Issue: Majority of Downloaded Suricata Rules Fail to Parse

**Symptoms**
```text
[ERRCODE: SC_ERR_RULE_KEYWORD_UNKNOWN(102)] - unknown rule keyword 'tls.certs'.
```
repeated for thousands of rules.

**Investigation**
```bash
sudo tail -1 /var/log/suricata/eve.json | grep -o '"rules_loaded":[0-9]*\|"rules_failed":[0-9]*'
```
```text
"rules_loaded":5217,"rules_failed":43789
```

**Root Cause**
The downloaded 2024-era ruleset makes heavy use of the `tls.certs` sticky-buffer keyword (used to fingerprint C2 frameworks like Sliver and Havoc by their TLS certificate fields), introduced in a Suricata version newer than the installed 4.1.10. Suricata gracefully skipped every rule using that keyword rather than crashing.

**Resolution**
Accepted the 5,217 successfully-loaded rules as the working baseline rather than chasing full compatibility with a 5-version-newer ruleset; supplemented with hand-written custom rules targeting the specific lab's known vulnerable services (see `COMMAND_REFERENCE.md`).

**Prevention**
When pairing an old, pinned tool version with a current community ruleset, expect a compatibility gap and verify `rules_loaded` vs. `rules_failed` counts rather than assuming a non-crashing start means full ruleset coverage.

---

### Issue: Wazuh Not Ingesting Suricata Alerts Despite Correct File Path

**Symptoms**
Suricata's `eve.json` was confirmed (via direct `tail`) to contain alert entries, but none appeared in Wazuh's dashboard.

**Investigation**
```bash
sudo grep -A3 "<localfile>" /var/ossec/etc/ossec.conf | grep -A3 "suricata\|eve.json"
```
```text
<command>/var/log/suricata/eve.json</command>
```

**Root Cause**
The config used the `<command>` tag (intended for monitoring the *output of a command*) instead of `<location>` (intended for tailing a *file*). Wazuh was silently trying to execute the file path as a shell command rather than reading it as a log file.

**Resolution**
```bash
sudo sed -i 's|<command>/var/log/suricata/eve.json</command>|<location>/var/log/suricata/eve.json</location>|' /var/ossec/etc/ossec.conf
sudo systemctl restart wazuh-manager
```

**Verification**
Triggered a known-working custom test rule (`signature_id: 9000001`, alerts on any ICMP) and confirmed it appeared in Wazuh's `wazuh-alerts-*` index within seconds, tagged `rule.groups: ids, suricata`.

**Prevention**
When integrating a JSON log source into Wazuh, double-check the exact tag name (`<location>` vs `<command>`) — both are valid Wazuh config elements with very different meanings, and a typo doesn't throw a config error, it just silently never ingests anything.

---

## Firewall Configuration

### Issue: Firewall Rules Scoped to TCP Only, Missing ICMP/UDP

**Symptoms**
Ping tests between segments behaved inconsistently with the intended design even after rules were added.

**Investigation**
Reviewed the rule list directly in the pfSense GUI and noticed every rule's Protocol column showed `IPv4 TCP` instead of `IPv4 *` (Any).

**Root Cause**
Rules had been created with Protocol explicitly set to TCP, so ICMP (ping) and UDP (DNS, syslog) traffic matched neither the allow nor the block rule and fell through to pfSense's implicit default-deny — producing behavior that looked like "the rule isn't working" when actually the rule simply didn't apply to that protocol at all.

**Resolution**
Edited each rule (both DMZ and RED tabs) and changed Protocol from TCP to Any.

**Verification**
```bash
ping -c 2 -W 2 192.168.1.1     # blocked as intended
ping -c 2 192.168.20.1          # allowed as intended
```

**Prevention**
When writing segmentation rules intended to be a blanket allow/block for a zone relationship, explicitly set Protocol to Any unless there's a specific reason to scope it — TCP-only is easy to default to without noticing, especially when copying a rule template.

---

## Application Deployment

### Issue: Kali Pre-Built QEMU Image 404
**Symptoms**
```text
HTTP request sent, awaiting response... 404 Not Found
```
when downloading Kali's official pre-built `.7z` QEMU image using a guessed version-specific filename.

**Root Cause**
Kali's download paths are version-specific and change with each release; a guessed filename for the "current" version was wrong.

**Resolution**
Switched to the standard installer ISO approach (same proven pattern already used successfully for OpenWrt and pfSense) rather than continuing to guess pre-built image filenames:
```bash
wget https://cdimage.kali.org/kali-2026.1/kali-linux-2026.1-installer-amd64.iso
```

**Prevention**
For any vendor's pre-built VM images, confirm the exact current filename from the vendor's download page rather than constructing it from a remembered pattern — release naming conventions and version numbers shift often.

