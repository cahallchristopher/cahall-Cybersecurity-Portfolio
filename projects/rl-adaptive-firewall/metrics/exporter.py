#!/usr/bin/env python3
"""
metrics/exporter.py
───────────────────
Exposes RL firewall agent metrics to Prometheus on port 9101.

Metrics exported:
  rl_firewall_packets_total        — total packets processed
  rl_firewall_flows_active         — currently tracked flows
  rl_firewall_blocked_ips          — currently blocked IPs
  rl_firewall_watched_ips          — IPs on watchlist
  rl_firewall_epsilon              — agent exploration rate
  rl_firewall_total_reward         — cumulative reward
  rl_firewall_avg_loss             — average training loss
  rl_firewall_action_total         — counter per action type
  rl_firewall_episodes_total       — completed training episodes
  rl_firewall_buffer_size          — replay buffer fill level

Run alongside rl_firewall.py — reads from shared state file.
"""

import os
import sys
import json
import time
import logging
from prometheus_client import start_http_server, Gauge, Counter, Info
from prometheus_client.core import CollectorRegistry

log = logging.getLogger(__name__)

BASE       = os.path.expanduser("~/rl-firewall")
STATE_FILE = f"{BASE}/logs/agent_state.json"
PORT       = 9101

# ── Prometheus metrics ────────────────────────────────────────
packets_total   = Gauge("rl_firewall_packets_total",   "Total packets processed")
flows_active    = Gauge("rl_firewall_flows_active",    "Active tracked flows")
blocked_ips     = Gauge("rl_firewall_blocked_ips",     "Currently blocked IPs")
watched_ips     = Gauge("rl_firewall_watched_ips",     "IPs on watchlist")
epsilon         = Gauge("rl_firewall_epsilon",         "Agent exploration rate (0=exploit 1=explore)")
total_reward    = Gauge("rl_firewall_total_reward",    "Cumulative reward")
avg_loss        = Gauge("rl_firewall_avg_loss",        "Average training loss (last 100 steps)")
episodes        = Gauge("rl_firewall_episodes_total",  "Completed training episodes")
buffer_size     = Gauge("rl_firewall_buffer_size",     "Replay buffer size")

# Per-action counters
action_counters = {
    "ALLOW":       Gauge("rl_firewall_action_allow",      "ALLOW action count"),
    "BLOCK_IP":    Gauge("rl_firewall_action_block_ip",   "BLOCK_IP action count"),
    "RATE_LIMIT":  Gauge("rl_firewall_action_rate_limit", "RATE_LIMIT action count"),
    "LOG_WATCH":   Gauge("rl_firewall_action_log_watch",  "LOG_WATCH action count"),
    "BLOCK_PORT":  Gauge("rl_firewall_action_block_port", "BLOCK_PORT action count"),
}

ACTION_MAP = {0: "ALLOW", 1: "BLOCK_IP", 2: "RATE_LIMIT", 3: "LOG_WATCH", 4: "BLOCK_PORT"}


def update_metrics(state: dict):
    """Push latest state values into Prometheus gauges."""
    packets_total.set(state.get("packets",       0))
    flows_active.set( state.get("flows",         0))
    blocked_ips.set(  state.get("blocked",       0))
    watched_ips.set(  state.get("watched",       0))
    epsilon.set(      state.get("epsilon",       1.0))
    total_reward.set( state.get("total_reward",  0.0))
    avg_loss.set(     state.get("avg_loss",      0.0))
    episodes.set(     state.get("episodes",      0))
    buffer_size.set(  state.get("buffer_size",   0))

    counts = state.get("action_counts", {})
    for idx, name in ACTION_MAP.items():
        val = counts.get(str(idx), counts.get(idx, 0))
        action_counters[name].set(val)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    log.info(f"Starting RL Firewall metrics exporter on port {PORT}")
    start_http_server(PORT)
    log.info(f"Prometheus metrics available at http://localhost:{PORT}/metrics")
    log.info(f"Reading agent state from {STATE_FILE}")

    while True:
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE) as f:
                    state = json.load(f)
                update_metrics(state)
            else:
                log.warning(f"State file not found: {STATE_FILE} — waiting...")
        except Exception as e:
            log.error(f"Error reading state: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()
