#!/usr/bin/env python3
"""
rl_firewall.py
──────────────
Main process — wires together:
  1. nfqueue packet interception
  2. Feature extraction (FlowStats)
  3. DQN agent decision
  4. iptables rule application
  5. Reward computation and agent training

Run as root:
  sudo ~/rl-firewall/venv/bin/python rl_firewall.py

Safety:
  - All errors default to ACCEPT (never silently drop on crash)
  - teardown_nfqueue.sh restores normal forwarding if this dies
  - Blocked IPs are logged to logs/blocked.log
  - Agent model is saved every 10 episodes
"""

import os
import sys
import time
import signal
import logging
import threading
import subprocess
from typing import Dict, Set

import numpy as np
from scapy.layers.inet import IP, TCP, UDP, ICMP
from netfilterqueue import NetfilterQueue

# ── Path setup ───────────────────────────────────────────────
BASE = os.path.expanduser("~/rl-firewall")
sys.path.insert(0, BASE)

from capture.feature_extractor import FlowTable, FEATURE_DIM
from agent.dqn_agent import DQNAgent, compute_reward, ACTION_NAMES

# ── Logging ──────────────────────────────────────────────────
os.makedirs(f"{BASE}/logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{BASE}/logs/firewall.log"),
    ],
)
log = logging.getLogger(__name__)

blocked_log = logging.getLogger("blocked")
blocked_handler = logging.FileHandler(f"{BASE}/logs/blocked.log")
blocked_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
blocked_log.addHandler(blocked_handler)
blocked_log.setLevel(logging.INFO)

# ── Config ───────────────────────────────────────────────────
QUEUE_NUM       = 0
LAN_IFACE       = "enp2s0"
WAN_IFACE       = "enp1s0"
TRAIN_EVERY     = 4        # train agent every N packets
EPISODE_PACKETS = 500      # end episode every N packets
BLOCK_DURATION  = 300      # seconds before auto-unblocking an IP
RATE_LIMIT_KBPS = 256      # kbps for rate-limited flows

# ── Shared state ─────────────────────────────────────────────
flow_table   = FlowTable()
agent        = DQNAgent()
blocked_ips:  Dict[str, float] = {}   # ip → unblock_time
watched_ips:  Set[str]         = set()
_lock        = threading.Lock()
packet_count = 0
episode_count = 0

# ── iptables helpers ─────────────────────────────────────────
def _run(cmd: str) -> bool:
    try:
        subprocess.run(cmd, shell=True, check=True,
                       capture_output=True, timeout=2)
        return True
    except Exception as e:
        log.error(f"iptables error: {e} | cmd: {cmd}")
        return False


def block_ip(src_ip: str):
    """Block all forwarded traffic from src_ip."""
    with _lock:
        if src_ip in blocked_ips:
            return
        blocked_ips[src_ip] = time.time() + BLOCK_DURATION

    _run(f"iptables -I FORWARD 1 -s {src_ip} -j DROP")
    blocked_log.info(f"BLOCKED {src_ip} for {BLOCK_DURATION}s")
    log.warning(f"[action] BLOCK_IP → {src_ip}")


def unblock_ip(src_ip: str):
    """Remove block rule for src_ip."""
    with _lock:
        blocked_ips.pop(src_ip, None)

    _run(f"iptables -D FORWARD -s {src_ip} -j DROP")
    log.info(f"[action] UNBLOCK → {src_ip}")


def rate_limit_ip(src_ip: str):
    """Rate-limit traffic from src_ip using hashlimit."""
    _run(
        f"iptables -I FORWARD 1 -s {src_ip} "
        f"-m hashlimit --hashlimit-name rl_{src_ip.replace('.','_')} "
        f"--hashlimit-above {RATE_LIMIT_KBPS}kb/s "
        f"--hashlimit-mode srcip -j DROP"
    )
    log.info(f"[action] RATE_LIMIT → {src_ip} @ {RATE_LIMIT_KBPS}kbps")


def block_port(src_ip: str, dst_port: int):
    """Block a specific dst port from src_ip."""
    _run(
        f"iptables -I FORWARD 1 -s {src_ip} "
        f"-p tcp --dport {dst_port} -j DROP"
    )
    log.info(f"[action] BLOCK_PORT → {src_ip}:{dst_port}")


def apply_action(action: int, src_ip: str, dst_port: int):
    """Translate agent action integer into actual iptables rule."""
    if action == 0:   # ALLOW — nothing to do, packet already accepted
        pass
    elif action == 1:  # BLOCK_IP
        block_ip(src_ip)
    elif action == 2:  # RATE_LIMIT
        rate_limit_ip(src_ip)
    elif action == 3:  # LOG_WATCH
        watched_ips.add(src_ip)
        log.info(f"[action] LOG_WATCH → {src_ip} added to watchlist")
    elif action == 4:  # BLOCK_PORT
        block_port(src_ip, dst_port)


# ── Auto-unblock thread ───────────────────────────────────────
def unblock_scheduler():
    """Background thread that lifts temporary blocks after BLOCK_DURATION."""
    while True:
        time.sleep(30)
        now = time.time()
        with _lock:
            expired = [ip for ip, t in blocked_ips.items() if t <= now]
        for ip in expired:
            unblock_ip(ip)


# ── Status thread ─────────────────────────────────────────────
def status_printer():
    while True:
        time.sleep(30)
        summary = agent.summary()
        log.info(
            f"[status] pkts={packet_count} "
            f"flows={flow_table.count()} "
            f"blocked={len(blocked_ips)} "
            f"watched={len(watched_ips)} "
            f"eps={summary['epsilon']:.3f} "
            f"reward={summary['total_reward']:.1f} "
            f"loss={summary['avg_loss']:.4f}"
        )


# ── Packet callback ───────────────────────────────────────────
def packet_callback(pkt):
    global packet_count, episode_count

    try:
        payload  = pkt.get_payload()
        scapy_pkt = IP(payload)

        if not scapy_pkt.haslayer(IP):
            pkt.accept()
            return

        ip       = scapy_pkt[IP]
        src_ip   = ip.src
        dst_ip   = ip.dst
        size     = len(payload)
        proto_num = ip.proto
        flags    = 0
        dst_port = 0

        if scapy_pkt.haslayer(TCP):
            dst_port = scapy_pkt[TCP].dport
            flags    = int(scapy_pkt[TCP].flags)
        elif scapy_pkt.haslayer(UDP):
            dst_port = scapy_pkt[UDP].dport

        proto_idx = {6: 0, 17: 1, 1: 2}.get(proto_num, 3)

        # Update flow stats and extract features
        flow     = flow_table.update(src_ip, dst_ip, dst_port, proto_idx, size, flags)
        state    = flow.to_feature_vector()

        # Agent decides
        action   = agent.select_action(state)
        action_name = ACTION_NAMES[action]

        # Apply the decision
        apply_action(action, src_ip, dst_port)

        # Compute reward using feature heuristics
        reward   = compute_reward(action, is_attack=False, flow_features=state)

        # Store transition (next state = same state, simplified online learning)
        next_state = state.copy()
        agent.store(state, action, reward, next_state)

        # Train periodically
        packet_count += 1
        if packet_count % TRAIN_EVERY == 0:
            agent.train_step()

        # End episode periodically
        if packet_count % EPISODE_PACKETS == 0:
            episode_count += 1
            agent.end_episode()

        # Log interesting decisions
        if action != 0:  # anything other than ALLOW
            log.info(
                f"[decision] {src_ip}→{dst_ip}:{dst_port} "
                f"action={action_name} "
                f"pkt_rate={state[0]:.2f} "
                f"syn_ratio={state[2]:.2f} "
                f"reward={reward:.1f}"
            )

        # Always accept at queue level — iptables rules handle drops
        # This prevents the queue from blocking if agent is slow
        pkt.accept()

    except Exception as e:
        log.error(f"Packet callback error: {e}")
        pkt.accept()   # safe default


# ── Signal handler ────────────────────────────────────────────
def shutdown(signum, frame):
    log.info("Shutting down RL firewall...")
    agent.save()
    log.info("Model saved. Run teardown_nfqueue.sh to restore normal forwarding.")
    sys.exit(0)


# ── Main ─────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("  RL Adaptive Firewall — Phase 3: Live Agent")
    log.info("=" * 60)
    log.info(f"  Queue:        NFQUEUE {QUEUE_NUM}")
    log.info(f"  LAN iface:    {LAN_IFACE}")
    log.info(f"  WAN iface:    {WAN_IFACE}")
    log.info(f"  Train every:  {TRAIN_EVERY} packets")
    log.info(f"  Episode size: {EPISODE_PACKETS} packets")
    log.info(f"  Block time:   {BLOCK_DURATION}s")
    log.info("=" * 60)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start background threads
    threading.Thread(target=unblock_scheduler, daemon=True).start()
    threading.Thread(target=status_printer,    daemon=True).start()

    # Bind to nfqueue
    nfq = NetfilterQueue()
    nfq.bind(QUEUE_NUM, packet_callback)

    log.info("Listening on NFQUEUE 0... (Ctrl+C to stop and save model)")
    try:
        nfq.run()
    except KeyboardInterrupt:
        shutdown(None, None)
    finally:
        nfq.unbind()


if __name__ == "__main__":
    main()
