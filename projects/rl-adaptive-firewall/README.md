# RL Adaptive Firewall Lab

A virtual cybersecurity lab built with KVM/libvirt, OpenWrt, and a
self-learning firewall powered by a Deep Q-Network (TensorFlow 2).

## What This Is

Instead of static firewall rules, this firewall uses reinforcement
learning to decide whether to allow, block, rate-limit, or flag each
network connection in real time on live traffic.

## Architecture

client-lan (10.0.98.200)
↓  dnsmasq DHCP from gw-dmz
gw-dmz (10.0.98.1)  ←  RL Firewall + Prometheus + Grafana
↓  NAT through DMZ
OpenWrt (10.0.96.1)  ←  Router/Firewall
↓  libvirt NAT
Internet

## Key Technologies

- **KVM/libvirt** — virtual machines and networks
- **OpenWrt 23.05.3** — real router OS
- **TensorFlow 2.21 / Keras** — DQN policy network
- **Scapy + netfilterqueue** — live packet interception
- **iptables** — real-time rule application
- **Prometheus + Grafana** — live learning dashboard

## Project Structure

| Folder | Contents |
|---|---|
| `docs/` | Full portfolio writeup and lab build guide |
| `scripts/` | Host setup scripts |
| `agent/` | DQN agent — policy network and training loop |
| `capture/` | Packet capture and feature extraction |
| `rules/` | iptables NFQUEUE setup and teardown |
| `metrics/` | Prometheus exporter |
| `dashboard/` | Grafana dashboard JSON |
| `configs/` | systemd service files |

## Skills Demonstrated

Linux · KVM · libvirt · OpenWrt · Python · TensorFlow · Reinforcement Learning ·
iptables · Packet Analysis · Prometheus · Grafana · systemd · Network Segmentation ·
DMZ Design · Troubleshooting · Documentation
