# Screenshots & Visual Documentation

## Network Architecture

### Network Topology Diagram
*Diagram showing Gateway (10.50.50.1), Windows Sensor (10.50.50.117), and Kali Attacker (10.50.50.155)*

![Network Topology](screenshots/network-topology.png)

---

## Gateway Configuration

### dnsmasq Status
*Screenshot showing dnsmasq service running and configured*

![dnsmasq Status](screenshots/dnsmasq-status.png)

### DHCP Leases
*DHCP leases showing both Windows and Kali VMs*

![DHCP Leases](screenshots/dhcp-leases.png)

### NAT Configuration
*iptables NAT rules showing MASQUERADE configuration*

![NAT Rules](screenshots/nat-rules.png)

---

## Windows Sensor

### LimaCharlie Sensor Running
*Windows service showing rphcpsvc running*

![Sensor Service](screenshots/sensor-running.png)

### Network Configuration
*ipconfig showing IP 10.50.50.117 from DHCP*

![Network Config](screenshots/windows-ipconfig.png)

---

## LimaCharlie Dashboard

### Sensor Online
*Dashboard showing Windows sensor connected and online*

![Sensor Online](screenshots/limacharlie-sensor-online.png)

### Detection Rules Configured
*All three D&R rules enabled*

![D&R Rules](screenshots/detection-rules.png)

### Detection Alerts
*Red alerts showing detections triggered*

![Alerts](screenshots/alerts-firing.png)

### Attack Timeline
*Timeline view showing complete attack chain*

![Timeline](screenshots/attack-timeline.png)

### Automated Response
*Network segregation and process termination executed*

![Automated Response](screenshots/automated-response.png)

---

## Attack Simulation

### Sliver C2 Session
*Kali terminal showing established C2 session*

![Sliver Session](screenshots/sliver-session.png)

### Payload Execution
*Cookie Monster implant running on Windows*

![Payload Execution](screenshots/payload-execution.png)

### Credential Theft Attempt
*LSASS access attempt blocked by LimaCharlie*

![Blocked Attack](screenshots/credential-theft-blocked.png)

---

## Results Summary

### Detection Performance
*Metrics showing sub-second detection and response*

![Performance Metrics](screenshots/detection-performance.png)

---

## Notes

Screenshots demonstrate:
- ✅ Complete lab setup and configuration
- ✅ Successful attack simulation
- ✅ Real-time detection and alerting
- ✅ Automated response execution
- ✅ Evidence collection and forensics

*All screenshots taken January 2026 during live lab testing*
