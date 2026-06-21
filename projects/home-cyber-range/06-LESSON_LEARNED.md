# Lessons Learned

## Identical state surviving a reboot means a saved config, not a live process

**What happened:** Bridges I deleted kept reappearing, even across a full host reboot, with the same MAC address every time.

**Why it happened:** I initially searched for *processes* that could be recreating the interfaces (GNS3, Containerlab, Docker, systemd units) — all reasonable first guesses, all wrong. The actual cause was a *saved configuration* (NetworkManager connection profiles) that gets replayed at boot, not a process running continuously.

**What I learned:** A live process and a saved configuration produce the same symptom (the resource keeps coming back) but require completely different diagnostic paths. Identical state across a reboot — especially something as specific as a MAC address — is a strong signal to check config stores (`nmcli`, `/etc/netplan`, `/etc/network`, `systemd-networkd` configs) before chasing processes.

**Professional application:** This is the same diagnostic instinct needed for "why does this server keep reverting a setting" tickets in any sysadmin role — config management tools (Ansible, Puppet, cloud-init, NetworkManager) silently reasserting state is a very common real-world cause that's easy to miss if you only think in terms of "what's running right now."

---

## Trace the actual data path before trusting a GUI's claimed state

**What happened:** Twice during the GNS3/pfSense build, the GUI's visual state didn't match reality — once an ISO was shown as a hard disk without obvious indication, once a link appeared drawn on the canvas but didn't actually exist in the saved topology.

**Why it happened:** GUIs abstract away the underlying config, and that abstraction can desync from the real state, especially after several create/delete/redraw cycles in one session.

**What I learned:** When a GUI's behavior doesn't match the documented/expected config, going straight to the underlying file (in this case, GNS3's `.gns3` JSON project file) resolved both issues faster than continuing to click around the GUI guessing. I now treat "inspect the raw config file directly" as a default troubleshooting step, not a last resort.

**Professional application:** Directly inspired by how I'd troubleshoot any abstraction layer in production — Kubernetes manifests vs. `kubectl describe` output, Terraform state vs. the cloud console, firewall GUI vs. the actual rule set on disk. The GUI is a view of the state, not the state itself.

---

## A correct fix in the wrong layer still looks like "nothing is working"

**What happened:** The syslog-to-Wazuh pipeline had three real, independently-fixable bugs (sysklogd's missing `-r` flag, Wazuh's `<logall>no</logall>` setting, a malformed `<command>` vs `<location>` tag later in the Suricata integration) — and I fixed all of them in sequence, and logs *still* didn't arrive, because the actual blocker the whole time was the firewall correctly enforcing DMZ→LAN isolation.

**Why it happened:** Each individual fix was genuinely necessary and genuinely correct, which made it easy to assume the *next* failure was yet another application-layer config issue, rather than stepping back to check basic network reachability (`ping`) between the two hosts.

**What I learned:** When debugging a multi-hop pipeline, verify connectivity at the lowest layer first (can host A reach host B at all?) before assuming each new symptom needs a new application-layer fix. I now run a basic `ping`/`tcpdump` check between endpoints as step one of any cross-host troubleshooting, even when I'm fairly confident the issue is "higher up."

**Professional application:** This is the OSI-model discipline every network/SOC role expects — work bottom-up (physical/network reachability) before top-down (application config), especially when several layers all have plausible-looking bugs simultaneously.

---

## Old/EOL systems require working around tooling assumptions, not fighting them

**What happened:** Getting Suricata's rule-update tool working on a FIPS-locked Amazon Linux 2 host, and getting syslog forwarding working on a 2008-era Ubuntu 8.04 target, both required abandoning the "standard" tool/method and using a more manual, more portable approach instead.

**Why it happened:** Modern tooling (`suricata-update`, current rule URLs, current EPEL paths) makes assumptions — about crypto policy, about hosting longevity, about package availability — that don't hold on older or differently-configured systems.

**What I learned:** Rather than spending unlimited time forcing the "intended" tool to work, recognizing when to drop to a more manual but more portable approach (downloading rules directly instead of via `suricata-update`; a one-line `nc`-based forwarder instead of fighting sysklogd's exact remote-logging syntax) was the faster and more robust path. The manual approach also happened to be easier to explain and audit.

**Professional application:** Directly relevant to any environment with legacy systems still in production (and most enterprise environments have some) — knowing when "use the standard tool" isn't realistic, and having a manual fallback ready, is a practical skill that pure greenfield experience doesn't teach.

---

## Document the limitation instead of hiding it

**What happened:** Suricata, as currently deployed, only sees LAN-segment traffic — it has no visibility into direct RED→DMZ attack traffic, which is most of what actually happens in this range.

**Why it happened:** I chose the simplest placement (Suricata co-located with Wazuh on LAN) to get a working pipeline established quickly, knowing it wouldn't give full coverage.

**What I learned:** It would have been easy to quietly not mention this limitation and let the README imply full IDS coverage. Writing it down explicitly — including *why* it's limited and what the real fix would look like (a second Suricata instance with a SPAN/mirror view into DMZ/RED traffic) — is more useful to a reader and more honest about the current state of the project.

**Professional application:** Real production documentation (runbooks, architecture decision records, post-incident reviews) is far more useful when it states known gaps plainly. A hiring manager or senior engineer reading "here's what doesn't work yet and why" trusts the rest of the document more than one that implies everything is finished.

---

## Trade-offs and alternatives considered

- **Suricata placement:** considered a dedicated Suricata VM with a SPAN/mirror port into DMZ/RED traffic from the start, but chose co-locating it with Wazuh on LAN for faster time-to-working-pipeline. Documented as a planned improvement rather than implemented now.
- **Wazuh agent vs. syslog forwarding on Metasploitable2:** the standard Wazuh approach is an installed agent, but Metasploitable2's 2008-era OS can't run a modern agent. Syslog forwarding was the realistic alternative, and is arguably more representative of how real SOC teams handle legacy/unsupported systems they can't install agents on.
- **DMZ→LAN syslog exception, narrow vs. broad:** could have simplified troubleshooting by temporarily allowing broader DMZ→LAN access, but chose to scope the exception to exactly UDP/514 from the start and accept the slower debugging process, since a narrow exception is the actually-correct production pattern.

## Future improvements

- Add a second Suricata sensor (or a SPAN/mirror-fed tap) with visibility into RED↔DMZ traffic directly, closing the network-IDS gap documented above
- Automate `kvm_intel`/`kvm_amd` module loading at boot via `/etc/modules`
- Replace the manual one-line netcat syslog forwarder with a small persistent systemd-style init script (Metasploitable2 predates systemd, so this would use an old-style init script) so it survives reboots without manual restart
- Add a second target host with a different vulnerability profile (e.g., a deliberately misconfigured web app) to diversify DMZ beyond Metasploitable2
- Enable logging on the OpenWrt IOT-isolation DROP rules for additional detection-engineering practice

