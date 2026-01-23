network:
  version: 2
  ethernets:
    enp0s3:  # External (NAT)
      dhcp4: true

    enp0s8:  # Internal (SOAR Lab)
      addresses:
        - 10.50.50.1/24
      dhcp4: false
