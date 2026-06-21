# Command Reference

Every command used in this build, grouped by tool/category.

## Linux Administration

| Command | Purpose | Notes |
|---|---|---|
| `ip a` | List all interfaces and their IPs | Primary tool for diagnosing the bridge conflict |
| `ip link del <iface>` | Delete a network interface | Doesn't persist if something else (e.g. NetworkManager) owns the config |
| `ip link show <iface>` | Inspect a specific interface | |
| `ip -d link show <iface>` | Inspect with full detail (bridge/STP params) | Used to confirm an interface was genuinely a bridge |
| `ip route show default` | Show the default route | Used repeatedly to verify the host's real uplink was never hijacked by lab interfaces |
| `ip addr add <cidr> dev <iface>` | Assign a static IP | Used for all host-side veth interfaces — never DHCP, by design |
| `ip addr del <cidr> dev <iface>` | Remove an IP from an interface | Used to fix the duplicate-IP conflict |
| `sudo systemctl status <service>` | Check a service's running state | |
| `sudo systemctl restart <service>` | Restart a service | |
| `sudo journalctl -u <service> -n 30 --no-pager` | View recent logs for a systemd unit | Primary tool for reading Suricata's startup errors |
| `tcpdump -i <iface> udp port 514 -A -c 5` | Capture and display packet contents | Used to confirm whether syslog packets were actually leaving/arriving |
| `ps aux \| grep <name>` | Check if a process is running | |
| `nohup <cmd> &` | Run a command persistently in the background, surviving terminal disconnect | Used for the syslog forwarder one-liner |

## Networking / Bridges / veth

| Command | Purpose | Notes |
|---|---|---|
| `sudo nmcli con show` | List NetworkManager connection profiles | Revealed the root cause of the bridge-respawn bug |
| `sudo nmcli con delete <uuid>` | Delete a saved NetworkManager connection | |
| `ip link add <dev1> type veth peer name <dev2>` | Create a veth pair | Core building block for host-to-segment access |
| `ip link set <dev> master <bridge>` | Enslave an interface to a bridge | |
| `ip link set <dev> up` | Bring an interface up | |

## Libvirt / KVM

| Command | Purpose | Notes |
|---|---|---|
| `virsh net-list --all` | List all libvirt networks and their state | |
| `virsh net-define /dev/stdin <<EOF ... EOF` | Define a new libvirt network from inline XML | |
| `virsh net-start <name>` | Start a defined network | |
| `virsh net-autostart <name>` | Set a network to start on boot | |
| `virsh net-destroy <name>` | Stop a running network | |
| `virsh net-undefine <name>` | Remove a network definition | |
| `virsh dominfo <vm>` | Show VM details | |
| `virsh domiflist <vm>` | List a VM's network interfaces | |
| `virsh domifaddr <vm>` | Show a VM's assigned IP addresses | |
| `virsh console <vm>` | Attach to a VM's serial console | |
| `virsh destroy <vm>` | Force-stop a running VM | |
| `virsh undefine <vm> --remove-all-storage` | Delete a VM and its disk | Used to wipe the original half-configured OpenWrt VM |
| `sudo virt-install --name ... --memory ... --disk ... --import --network network=<name>,model=virtio ...` | Create a new VM from an existing disk image, fully scripted | Used for the OpenWrt rebuild — avoided the GUI entirely |
| `qemu-img resize <file> <size>` | Resize a qcow2/raw disk image | Used to fix the too-small pfSense install disk |
| `qemu-img convert -f vmdk -O qcow2 <in> <out>` | Convert a VMware disk to qcow2 | Used for both Metasploitable2 and the Wazuh OVA's disk |
| `qemu-img info <file>` | Show disk image metadata | |
| `modprobe kvm_intel` / `modprobe kvm_amd` | Load the KVM kernel module | Fixed the "/dev/kvm doesn't exist" error |

## GNS3

| Command | Purpose | Notes |
|---|---|---|
| `gns3server --version` | Confirm GNS3 server install | |
| `sudo usermod -aG ubridge,libvirt,kvm,wireshark,docker <user>` | Add user to required groups | Required full logout/login to take effect |
| `sudo chmod +s /usr/bin/ubridge` | Set the setuid bit on ubridge | Required even after group membership was correct |
| `pkill -f gns3server` | Stop the GNS3 server process | Used before directly editing project JSON, to avoid file-lock conflicts |
| `python3 -c "import json; ..."` | Read/write GNS3's `.gns3` project file directly | Used multiple times to diagnose issues the GUI didn't surface clearly (disk/ISO misassignment, missing links) |

## OpenWrt (UCI)

| Command | Purpose | Notes |
|---|---|---|
| `cat /etc/config/network` | View interface configuration | |
| `cat /etc/config/firewall` | View firewall zones/rules | |
| `cat /etc/config/dhcp` | View DHCP server configuration | |
| `service network restart` | Apply network config changes | |
| `service firewall restart` | Apply firewall config changes | |
| `service dnsmasq restart` | Apply DHCP/DNS config changes | |
| `service dropbear enable` / `service dropbear start` | Enable and start the SSH daemon | |
| `passwd root` | Set the root password | |
| `opkg update && opkg install luci` | Install the web GUI | |

## Wazuh

| Command | Purpose | Notes |
|---|---|---|
| `sudo /var/ossec/bin/wazuh-control status` | Check status of all Wazuh sub-processes | |
| `sudo systemctl restart wazuh-manager` | Restart the Wazuh manager | Required after every `ossec.conf` change |
| `sudo grep -A5 "<remote>" /var/ossec/etc/ossec.conf` | View the remote-logging config block | |
| `sudo tail -f /var/ossec/logs/ossec.log` | Watch Wazuh's own internal log | |
| `sudo tail -f /var/ossec/logs/archives/archives.log` | Watch all archived (not just alerted) events | Key tool for confirming raw log ingestion before checking the dashboard |

## Suricata

| Command | Purpose | Notes |
|---|---|---|
| `sudo yum install suricata -y` | Install Suricata (via EPEL) | |
| `sudo suricata-update` | Standard rule-update tool | Failed under FIPS — see Troubleshooting Guide |
| `sudo systemctl restart suricata` | Apply rule/config changes | |
| `sudo tail -1 /var/log/suricata/eve.json` | View the latest stats/alert event | |
| `sudo grep '"event_type":"alert"' /var/log/suricata/eve.json` | Filter eve.json for alerts only | |

## Syslog (sysklogd, Metasploitable2)

| Command | Purpose | Notes |
|---|---|---|
| `echo "*.* @192.168.1.10" \| sudo tee -a /etc/syslog.conf` | Add a remote syslog forwarding line | Required correcting from an initial `:514` port-suffix attempt that sysklogd didn't support |
| `cat /etc/default/syslogd` | Check sysklogd's startup flags | Revealed the missing `-r` (remote logging) flag |
| `sudo /etc/init.d/sysklogd restart` | Restart the syslog daemon | |
| `logger -t test "<message>"` | Generate a test log entry | Used repeatedly throughout the syslog troubleshooting |

## Networking Tools (Kali / testing)

| Command | Purpose | Notes |
|---|---|---|
| `nmap -sV --open <ip>` | Scan and identify open ports/service versions | Used to enumerate Metasploitable2 |
| `nmap -sS -p <range> <ip>` | SYN scan a port range | |
| `nc -u -w1 <ip> <port>` | Send a UDP packet via netcat | Core of the syslog forwarder workaround |
| `ssh -J <jumphost> <target>` | SSH through a jump host | Used to reach DMZ-segment Metasploitable2 from the Mint host via Kali |
| `ssh -o "HostKeyAlgorithms=+ssh-rsa,ssh-dss" -o "PubkeyAcceptedKeyTypes=+ssh-rsa,ssh-dss"` | Allow legacy SSH key types | Required for Metasploitable2's 2008-era OpenSSH |

