#!/usr/bin/env python3
"""
agent/dqn_agent.py
──────────────────
Deep Q-Network (DQN) agent for the adaptive firewall.

Architecture:
  - Policy network:  state → Q-values for each action
  - Target network:  stable copy updated every N steps (prevents oscillation)
  - Replay buffer:   stores (state, action, reward, next_state, done) tuples
  - Epsilon-greedy:  exploration vs exploitation trade-off

Actions:
  0 = ALLOW          let packet through
  1 = BLOCK_IP       block the source IP entirely
  2 = RATE_LIMIT     slow down this flow (via iptables limit)
  3 = LOG_AND_WATCH  allow but flag for closer inspection
  4 = BLOCK_PORT     block this specific dst port from this src

State:
  10-dimensional feature vector from feature_extractor.py

Reward function:
  +10  blocked a confirmed attack
  +1   allowed clean traffic
  -5   blocked legitimate traffic (false positive)
  -10  allowed confirmed attack (false negative)
  -1   rate-limited clean traffic (minor penalty)
"""

import os
import time
import random
import logging
import threading
from collections import deque
from typing import List, Tuple, Optional

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

log = logging.getLogger(__name__)

# ── Hyperparameters ──────────────────────────────────────────
STATE_DIM       = 10       # must match feature_extractor.FEATURE_DIM
ACTION_DIM      = 5        # ALLOW, BLOCK_IP, RATE_LIMIT, LOG_WATCH, BLOCK_PORT
LEARNING_RATE   = 1e-3
GAMMA           = 0.95     # discount factor — how much future rewards matter
EPSILON_START   = 1.0      # start fully random (explore)
EPSILON_END     = 0.05     # minimum exploration rate
EPSILON_DECAY   = 0.995    # multiply epsilon by this each episode
BUFFER_SIZE     = 50_000   # replay buffer capacity
BATCH_SIZE      = 64       # training batch size
TARGET_UPDATE   = 100      # update target network every N steps
MIN_BUFFER      = 1_000    # don't train until we have this many samples
MODEL_PATH      = os.path.expanduser("~/rl-firewall/models/dqn_policy.keras")

# Action labels for logging
ACTION_NAMES = {
    0: "ALLOW",
    1: "BLOCK_IP",
    2: "RATE_LIMIT",
    3: "LOG_WATCH",
    4: "BLOCK_PORT",
}

# ── Reward shaping ───────────────────────────────────────────
# These are the signals that teach the agent what "good" means.
# Tuning these values is the most important part of RL design.
REWARD = {
    "blocked_attack":      +10.0,
    "allowed_clean":       +1.0,
    "false_positive":      -5.0,   # blocked legit traffic
    "false_negative":      -10.0,  # allowed attack through
    "rate_limit_clean":    -1.0,   # unnecessary rate limit
    "rate_limit_attack":   +5.0,   # good rate limit on attack
    "log_watch_attack":    +2.0,   # flagged an attack for inspection
    "log_watch_clean":     +0.5,   # logged clean (minor reward)
}


# ── Replay Buffer ─────────────────────────────────────────────
class ReplayBuffer:
    """
    Circular buffer storing experience tuples.
    Random sampling breaks correlation between consecutive samples,
    which stabilises DQN training.
    """

    def __init__(self, capacity: int = BUFFER_SIZE):
        self.buffer: deque = deque(maxlen=capacity)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> Tuple:
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states,      dtype=np.float32),
            np.array(actions,     dtype=np.int32),
            np.array(rewards,     dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones,       dtype=np.float32),
        )

    def __len__(self) -> int:
        return len(self.buffer)


# ── Policy Network ────────────────────────────────────────────
def build_network(state_dim: int, action_dim: int) -> keras.Model:
    """
    Small but effective network for this state/action space.
    Three hidden layers with ReLU, output is Q-value per action.
    """
    model = keras.Sequential([
        layers.Input(shape=(state_dim,)),
        layers.Dense(128, activation="relu",
                     kernel_initializer="he_uniform"),
        layers.BatchNormalization(),
        layers.Dense(128, activation="relu",
                     kernel_initializer="he_uniform"),
        layers.BatchNormalization(),
        layers.Dense(64, activation="relu",
                     kernel_initializer="he_uniform"),
        layers.Dense(action_dim, activation="linear"),  # Q-values, no activation
    ], name="dqn_policy")

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="huber",   # more robust than MSE for RL (handles outliers)
    )
    return model


# ── DQN Agent ────────────────────────────────────────────────
class DQNAgent:
    """
    Full DQN agent with:
      - Policy + target network
      - Epsilon-greedy action selection
      - Experience replay
      - Periodic target network sync
      - Model save/load
    """

    def __init__(self):
        self.policy_net = build_network(STATE_DIM, ACTION_DIM)
        self.target_net = build_network(STATE_DIM, ACTION_DIM)
        self._sync_target()

        self.buffer   = ReplayBuffer()
        self.epsilon  = EPSILON_START
        self.steps    = 0
        self.episodes = 0

        # Metrics for Prometheus/dashboard
        self.total_reward     = 0.0
        self.episode_reward   = 0.0
        self.loss_history:    List[float] = []
        self.action_counts    = {i: 0 for i in range(ACTION_DIM)}
        self._lock            = threading.Lock()

        # Load existing model if available
        if os.path.exists(MODEL_PATH):
            self.load()
            log.info(f"Loaded existing model from {MODEL_PATH}")
        else:
            log.info("Starting with fresh model weights")

    def _sync_target(self):
        """Copy policy network weights to target network."""
        self.target_net.set_weights(self.policy_net.get_weights())

    def select_action(self, state: np.ndarray) -> int:
        """
        Epsilon-greedy action selection.
        With probability epsilon: random action (explore)
        Otherwise: action with highest Q-value (exploit)
        """
        with self._lock:
            if random.random() < self.epsilon:
                action = random.randint(0, ACTION_DIM - 1)
            else:
                q_values = self.policy_net(
                    state.reshape(1, -1), training=False
                ).numpy()[0]
                action = int(np.argmax(q_values))

            self.action_counts[action] += 1
            return action

    def store(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool = False,
    ):
        """Store a transition in the replay buffer."""
        self.buffer.push(state, action, reward, next_state, done)
        self.episode_reward += reward
        self.total_reward   += reward

    def train_step(self) -> Optional[float]:
        """
        Sample a batch and perform one gradient update.
        Returns loss value or None if buffer is too small.
        """
        if len(self.buffer) < MIN_BUFFER:
            return None

        states, actions, rewards, next_states, dones = self.buffer.sample(BATCH_SIZE)

        # Compute target Q-values using the target network (stable)
        next_q = self.target_net(next_states, training=False).numpy()
        max_next_q = np.max(next_q, axis=1)
        targets_full = self.policy_net(states, training=False).numpy()

        for i in range(BATCH_SIZE):
            if dones[i]:
                targets_full[i][actions[i]] = rewards[i]
            else:
                targets_full[i][actions[i]] = (
                    rewards[i] + GAMMA * max_next_q[i]
                )

        # One gradient step
        with self._lock:
            history = self.policy_net.fit(
                states, targets_full,
                batch_size=BATCH_SIZE,
                epochs=1,
                verbose=0,
            )
            loss = float(history.history["loss"][0])

        self.loss_history.append(loss)
        if len(self.loss_history) > 1000:
            self.loss_history.pop(0)

        self.steps += 1

        # Decay epsilon
        if self.epsilon > EPSILON_END:
            self.epsilon *= EPSILON_DECAY

        # Sync target network
        if self.steps % TARGET_UPDATE == 0:
            self._sync_target()
            log.info(
                f"[agent] Target network synced | "
                f"step={self.steps} eps={self.epsilon:.3f} "
                f"loss={loss:.4f} buffer={len(self.buffer)}"
            )

        return loss

    def end_episode(self):
        """Call at the end of each training episode."""
        self.episodes += 1
        ep_reward = self.episode_reward
        self.episode_reward = 0.0

        avg_loss = (
            np.mean(self.loss_history[-100:])
            if self.loss_history else 0.0
        )

        log.info(
            f"[episode {self.episodes}] "
            f"reward={ep_reward:.1f} "
            f"avg_loss={avg_loss:.4f} "
            f"epsilon={self.epsilon:.3f} "
            f"buffer={len(self.buffer)} "
            f"actions={self.action_counts}"
        )

        # Save periodically
        if self.episodes % 10 == 0:
            self.save()

        return ep_reward

    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        """Return Q-values for all actions given a state."""
        return self.policy_net(
            state.reshape(1, -1), training=False
        ).numpy()[0]

    def save(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        self.policy_net.save(MODEL_PATH)
        log.info(f"[agent] Model saved → {MODEL_PATH}")

    def load(self):
        self.policy_net = keras.models.load_model(MODEL_PATH)
        self._sync_target()

    def summary(self) -> dict:
        """Return current agent stats for the dashboard."""
        return {
            "steps":         self.steps,
            "episodes":      self.episodes,
            "epsilon":       round(self.epsilon, 4),
            "buffer_size":   len(self.buffer),
            "total_reward":  round(self.total_reward, 2),
            "avg_loss":      round(
                float(np.mean(self.loss_history[-100:]))
                if self.loss_history else 0.0, 6
            ),
            "action_counts": self.action_counts,
        }


# ── Reward function ───────────────────────────────────────────
def compute_reward(action: int, is_attack: bool, flow_features: np.ndarray) -> float:
    """
    Assign reward based on what action was taken and whether the
    flow turned out to be an attack.

    In a real deployment, 'is_attack' comes from:
      - Signature matching (known bad IPs/ports)
      - Threshold rules (pkt_rate > 0.9 AND syn_ratio > 0.8 → likely attack)
      - Human feedback
      - Honeypot confirmation

    For training we use heuristics on the feature vector.
    """
    pkt_rate   = float(flow_features[0])
    syn_ratio  = float(flow_features[2])
    port_ent   = float(flow_features[3])
    icmp_ratio = float(flow_features[5])
    small_pkts = float(flow_features[6])

    # Heuristic attack confidence (0–1) based on features
    attack_score = (
        0.3 * pkt_rate +
        0.3 * syn_ratio +
        0.2 * port_ent +
        0.1 * icmp_ratio +
        0.1 * small_pkts
    )
    is_attack = is_attack or attack_score > 0.6

    if action == 0:   # ALLOW
        return REWARD["allowed_clean"] if not is_attack else REWARD["false_negative"]
    elif action == 1:  # BLOCK_IP
        return REWARD["blocked_attack"] if is_attack else REWARD["false_positive"]
    elif action == 2:  # RATE_LIMIT
        return REWARD["rate_limit_attack"] if is_attack else REWARD["rate_limit_clean"]
    elif action == 3:  # LOG_WATCH
        return REWARD["log_watch_attack"] if is_attack else REWARD["log_watch_clean"]
    elif action == 4:  # BLOCK_PORT
        return REWARD["blocked_attack"] * 0.8 if is_attack else REWARD["false_positive"] * 0.8
    return 0.0


# ── Quick sanity test ─────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    log.info("Building DQN agent...")
    agent = DQNAgent()
    agent.policy_net.summary()

    log.info("\nRunning 2000 random training steps to verify the loop...")
    for step in range(2000):
        state      = np.random.rand(STATE_DIM).astype(np.float32)
        action     = agent.select_action(state)
        reward     = compute_reward(action, is_attack=random.random() > 0.7,
                                    flow_features=state)
        next_state = np.random.rand(STATE_DIM).astype(np.float32)
        agent.store(state, action, reward, next_state)
        loss = agent.train_step()

        if step % 200 == 0 and step > 0:
            log.info(f"step={step} loss={loss:.4f} eps={agent.epsilon:.3f}")

    agent.end_episode()
    log.info("\nAgent summary:")
    for k, v in agent.summary().items():
        log.info(f"  {k}: {v}")

    log.info("\nDQN agent verified. Ready for Phase 3.")
