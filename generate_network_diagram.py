#!/usr/bin/env python3
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.network import Router
from diagrams.onprem.compute import Server
from diagrams.onprem.network import Internet

graph_attr = {
    "fontsize": "16",
    "bgcolor": "white",
    "dpi": "300"
}

with Diagram(
    "Security Lab Network Architecture",
    show=False,
    filename="01-network-diagram",
    direction="TB",
    graph_attr=graph_attr,
    outformat="png"
):
    internet = Internet("Internet")
    
    with Cluster("VirtualBox NAT Gateway", graph_attr={"bgcolor": "lightblue"}):
        nat_gateway = Router("NAT Gateway")
    
    with Cluster("Internal Network: SecurityLab (10.50.50.0/24)", graph_attr={"bgcolor": "lightgrey"}):
        with Cluster("soarlab - Ubuntu Server 22.04", graph_attr={"bgcolor": "#90EE90"}):
            soarlab = Server("DNSmasq Server\n10.50.50.1\n\nDHCP Server\nDNS Server\nNAT Gateway")
        
        with Cluster("lima_sensor - Debian 12 + XFCE", graph_attr={"bgcolor": "#FFD700"}):
            lima_sensor = Server("Target System\n10.50.50.x (DHCP)\n\nLimaCharlie EDR\nMonitoring Target")
        
        with Cluster("kali_attacker - Kali Linux 2024", graph_attr={"bgcolor": "#FF6B6B"}):
            kali = Server("Attacker System\n10.50.50.x (DHCP)\n\nMetasploit\nNmap\nPentest Tools")
    
    internet >> Edge(label="WAN", color="blue", style="bold") >> nat_gateway
    nat_gateway >> Edge(label="enp0s3 (NAT)", color="blue") >> soarlab
    soarlab >> Edge(label="enp0s8 - Internal\nDHCP/DNS", color="darkgreen", style="bold") >> lima_sensor
    soarlab >> Edge(label="Internal Network\nDHCP/DNS", color="darkgreen", style="bold") >> kali
    lima_sensor >> Edge(label="enp0s8 (NAT)\nLimaCharlie Cloud", color="orange", style="dashed") >> nat_gateway
    kali >> Edge(label="eth1 (NAT)\nUpdates/Tools", color="orange", style="dashed") >> nat_gateway

print("✅ Network diagram generated: 01-network-diagram.png")

