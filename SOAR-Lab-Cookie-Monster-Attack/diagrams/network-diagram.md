```
Internet
                       ↕
                [Host Machine]
                       ↕
              [NAT Adapter (enp0s3)]
                       ↕
    ┌──────────────────────────────────────┐
    │   Ubuntu Gateway VM (10.50.50.1)     │
    │   - dnsmasq (DHCP/DNS)               │
    │   - iptables (NAT/Firewall)          │
    │   - IPv4 forwarding enabled          │
    └──────────────────────────────────────┘
                       ↕
         [Internal Network Adapter (enp0s8)]
                       ↕
         [VirtualBox Internal Network: soarlab]
                       ↕
         ┌──────────────────────────────────┐
         │                                  │
    ┌────────────┐                  ┌───────────────┐
    │  Windows   │                  │  Kali Linux   │
    │  Sensor    │                  │  Attacker     │
    │ 10.50.50.117│ ←──Attack────→  │ 10.50.50.155  │
    └────────────┘                  └───────────────┘
                       ↕
                [LimaCharlie Cloud]
```
