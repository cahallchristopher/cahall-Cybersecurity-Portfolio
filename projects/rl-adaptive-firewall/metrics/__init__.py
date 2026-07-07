#!/usr/bin/env python3
"""
metrics/state_writer.py
────────────────────────
Writes RL agent state to a JSON file every 5 seconds
so the Prometheus exporter can read it without importing
TensorFlow (which is too heavy for a sidecar process).

Import and call start_writer(get_state_fn) from rl_firewall.py.
"""

import os
import json
import time
import threading
import logging

log = logging.getLogger(__name__)

BASE       = os.path.expanduser("~/rl-firewall")
STATE_FILE = f"{BASE}/logs/agent_state.json"
INTERVAL   = 5   # seconds between writes


def start_writer(get_state_fn, interval: int = INTERVAL):
    """
    Start background thread that calls get_state_fn() every INTERVAL
    seconds and writes the result to STATE_FILE as JSON.

    get_state_fn should return a dict with keys:
      packets, flows, blocked, watched, epsilon,
      total_reward, avg_loss, episodes, buffer_size, action_counts
    """
    def _write_loop():
        while True:
            try:
                state = get_state_fn()
                os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
                tmp = STATE_FILE + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(state, f)
                os.replace(tmp, STATE_FILE)   # atomic write
            except Exception as e:
                log.error(f"State write error: {e}")
            time.sleep(interval)

    t = threading.Thread(target=_write_loop, daemon=True, name="state-writer")
    t.start()
    log.info(f"State writer started → {STATE_FILE}")
    return t
