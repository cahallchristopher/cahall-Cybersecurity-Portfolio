#!/usr/bin/env python3
"""
capture/feature_extractor.py
─────────────────────────────
Sits on NFQUEUE and converts raw packets into feature vectors
that the RL agent can act on.

Each packet is:
  1. Intercepted via nfqueue
  2. Parsed with scapy
  3. Aggregated into a per-flow state
  4. Emitted as a numpy array for the agent

Run as root:
  sudo ~/rl-firewall/venv/bin/python capture/feature_extractor.py
"""

import time
import threading
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional

import numpy as np
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.packet import Packet
from netfilterqueue import NetfilterQueue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/adam/rl-firewall/logs/capture.log"),
    ],
)
log = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
FLOW_WINDOW   = 60      # seconds to track each flow
QUEUE_NUM     = 0       # nfqueue number (matches iptables rule)
MAX_FLOWS     = 10_000  # cap memory usage

# Feature vector indices (keep in sync with agent)
F_PKT_RATE       = 0   # packets per second in this flow
F_BYTE_RATE      = 1   # bytes per second
F_SYN_RATIO      = 2   # SYN packets / total TCP packets
F_PORT_ENTROPY   = 3   # entropy of destination ports (port scan indicator)
F_UNIQUE_DSTS    = 4   # unique destination IPs in last 60s from this src
F_ICMP_RATIO     = 5   # ICMP packets / total packets
F_SMALL_PKT_RATIO= 6   # packets < 64 bytes / total (SYN flood indicator)
F_DST_PORT_NORM  = 7   # normalised destination port (0–1)
F_PROTOCOL       = 8   # 0=TCP 1=UDP 2=ICMP 3=OTHER
F_TIME_OF_DAY    = 9   # hour / 24  (0–1)
FEATURE_DIM      = 10


@dataclass
class FlowStats:
    """Rolling statistics for a single (src_ip, dst_ip, dst_port) flow."""
    src_ip:    str
    dst_ip:    str
    dst_port:  int
    protocol:  int

    # Rolling windows
    timestamps:  deque = field(default_factory=lambda: deque(maxlen=10_000))
    sizes:       deque = field(default_factory=lambda: deque(maxlen=10_000))
    syn_count:   int = 0
    tcp_count:   int = 0
    icmp_count:  int = 0
    total_count: int = 0
    dst_ports_seen: set = field(default_factory=set)
    dst_ips_seen:   set = field(default_factory=set)

    def update(self, size: int, flags: int, protocol: int, dst_port: int, dst_ip: str):
        now = time.time()
        self.timestamps.append(now)
        self.sizes.append(size)
        self.total_count += 1
        self.dst_ports_seen.add(dst_port)
        self.dst_ips_seen.add(dst_ip)

        if protocol == 6:   # TCP
            self.tcp_count += 1
            if flags & 0x02:  # SYN flag
                self.syn_count += 1
        elif protocol == 1:   # ICMP
            self.icmp_count += 1

    def _window_slice(self) -> Tuple[list, list]:
        """Return timestamps and sizes within the last FLOW_WINDOW seconds."""
        cutoff = time.time() - FLOW_WINDOW
        ts = list(self.timestamps)
        sz = list(self.sizes)
        pairs = [(t, s) for t, s in zip(ts, sz) if t >= cutoff]
        if not pairs:
            return [], []
        ts_w, sz_w = zip(*pairs)
        return list(ts_w), list(sz_w)

    def pkt_rate(self) -> float:
        ts, _ = self._window_slice()
        if len(ts) < 2:
            return 0.0
        elapsed = ts[-1] - ts[0]
        return len(ts) / elapsed if elapsed > 0 else 0.0

    def byte_rate(self) -> float:
        ts, sz = self._window_slice()
        if len(ts) < 2:
            return 0.0
        elapsed = ts[-1] - ts[0]
        return sum(sz) / elapsed if elapsed > 0 else 0.0

    def syn_ratio(self) -> float:
        return self.syn_count / self.tcp_count if self.tcp_count > 0 else 0.0

    def port_entropy(self) -> float:
        ports = list(self.dst_ports_seen)
        if len(ports) <= 1:
            return 0.0
        total = len(ports)
        probs = np.array([1.0 / total] * total)
        return float(-np.sum(probs * np.log2(probs + 1e-9)))

    def small_pkt_ratio(self) -> float:
        _, sz = self._window_slice()
        if not sz:
            return 0.0
        small = sum(1 for s in sz if s < 64)
        return small / len(sz)

    def to_feature_vector(self) -> np.ndarray:
        vec = np.zeros(FEATURE_DIM, dtype=np.float32)
        vec[F_PKT_RATE]        = min(self.pkt_rate() / 1000.0, 1.0)
        vec[F_BYTE_RATE]       = min(self.byte_rate() / 1e7, 1.0)
        vec[F_SYN_RATIO]       = self.syn_ratio()
        vec[F_PORT_ENTROPY]    = min(self.port_entropy() / 10.0, 1.0)
        vec[F_UNIQUE_DSTS]     = min(len(self.dst_ips_seen) / 100.0, 1.0)
        vec[F_ICMP_RATIO]      = (
            self.icmp_count / self.total_count if self.total_count > 0 else 0.0
        )
        vec[F_SMALL_PKT_RATIO] = self.small_pkt_ratio()
        vec[F_DST_PORT_NORM]   = min(self.dst_port / 65535.0, 1.0)
        vec[F_PROTOCOL]        = self.protocol / 3.0
        vec[F_TIME_OF_DAY]     = time.localtime().tm_hour / 24.0
        return vec


class FlowTable:
    """Thread-safe table of active flows."""

    def __init__(self):
        self._flows: Dict[Tuple, FlowStats] = {}
        self._lock = threading.Lock()

    def key(self, src_ip: str, dst_ip: str, dst_port: int, protocol: int) -> Tuple:
        return (src_ip, dst_ip, dst_port, protocol)

    def update(
        self,
        src_ip: str, dst_ip: str,
        dst_port: int, protocol: int,
        size: int, flags: int,
    ) -> FlowStats:
        k = self.key(src_ip, dst_ip, dst_port, protocol)
        with self._lock:
            if k not in self._flows:
                if len(self._flows) >= MAX_FLOWS:
                    # evict oldest flow
                    oldest = next(iter(self._flows))
                    del self._flows[oldest]
                self._flows[k] = FlowStats(
                    src_ip=src_ip, dst_ip=dst_ip,
                    dst_port=dst_port, protocol=protocol,
                )
            flow = self._flows[k]
            flow.update(size, flags, protocol, dst_port, dst_ip)
            return flow

    def get(self, src_ip: str, dst_ip: str, dst_port: int, protocol: int) -> Optional[FlowStats]:
        k = self.key(src_ip, dst_ip, dst_port, protocol)
        with self._lock:
            return self._flows.get(k)

    def count(self) -> int:
        with self._lock:
            return len(self._flows)


# ── Global flow table (shared with agent) ────────────────────
flow_table = FlowTable()

# ── Packet callback ──────────────────────────────────────────
# This is called for EVERY packet intercepted by nfqueue.
# Keep it fast — heavy ML inference runs in the agent, not here.

_accept_all = True   # set False when agent is ready to make decisions

def packet_callback(pkt):
    """
    Parse packet, update flow stats, accept or drop based on agent decision.
    For Phase 1 (capture only) we always ACCEPT and just log features.
    """
    try:
        payload = pkt.get_payload()
        scapy_pkt: Packet = IP(payload)

        if not scapy_pkt.haslayer(IP):
            pkt.accept()
            return

        ip   = scapy_pkt[IP]
        src  = ip.src
        dst  = ip.dst
        size = len(payload)
        proto_num = ip.proto
        flags = 0
        dst_port = 0

        if scapy_pkt.haslayer(TCP):
            dst_port = scapy_pkt[TCP].dport
            flags    = int(scapy_pkt[TCP].flags)
        elif scapy_pkt.haslayer(UDP):
            dst_port = scapy_pkt[UDP].dport
        elif scapy_pkt.haslayer(ICMP):
            proto_num = 1

        # Map protocol to 0–3
        proto_idx = {6: 0, 17: 1, 1: 2}.get(proto_num, 3)

        flow = flow_table.update(src, dst, dst_port, proto_idx, size, flags)
        features = flow.to_feature_vector()

        log.debug(
            f"{src}:{dst_port} → features: "
            f"pkt_rate={features[F_PKT_RATE]:.3f} "
            f"syn_ratio={features[F_SYN_RATIO]:.3f} "
            f"port_entropy={features[F_PORT_ENTROPY]:.3f}"
        )

        # Phase 1: always accept, just observe
        pkt.accept()

    except Exception as e:
        log.error(f"Error processing packet: {e}")
        pkt.accept()   # safe default — never drop on error


# ── Main ─────────────────────────────────────────────────────
def main():
    log.info("Starting RL Firewall — Phase 1: Capture & Feature Extraction")
    log.info(f"Feature vector dimension: {FEATURE_DIM}")
    log.info(f"Flow window: {FLOW_WINDOW}s  |  Max flows: {MAX_FLOWS}")
    log.info("Binding to NFQUEUE 0 — make sure iptables rule is set")

    nfq = NetfilterQueue()
    nfq.bind(QUEUE_NUM, packet_callback)

    # Status thread — prints flow table stats every 10s
    def status():
        while True:
            time.sleep(10)
            log.info(f"Active flows: {flow_table.count()}")

    t = threading.Thread(target=status, daemon=True)
    t.start()

    try:
        log.info("Listening... (Ctrl+C to stop)")
        nfq.run()
    except KeyboardInterrupt:
        log.info("Stopped.")
    finally:
        nfq.unbind()


if __name__ == "__main__":
    main()
