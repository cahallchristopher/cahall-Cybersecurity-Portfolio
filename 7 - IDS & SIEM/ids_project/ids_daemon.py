#!/usr/bin/env python3
import sys, os, time, signal, logging, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import load_config
from utils.db import get_db_path, init_db
from collector.log_collector import collect_all
from detector.engine import DetectionEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/ids.log", mode="a"),
    ],
)
logger = logging.getLogger("ids.daemon")

_running = True

def _handle_signal(sig, frame):
    global _running
    logger.info("Shutdown received - stopping.")
    _running = False

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

def _fake_events():
    now = datetime.now().isoformat()
    events = []
    # SSH brute force - 6 failed attempts
    for i in range(6):
        events.append({
            "source":     "auth_log",
            "event_type": "auth_failed",
            "timestamp":  now,
            "source_ip":  "192.168.56.101",
            "user":       "root",
            "raw":        f"Jan 01 12:00:0{i} server sshd[1234]: Failed password for root from 192.168.56.101",
            "message":    "Failed password",
        })
    # SQL injection
    events.append({
        "source":     "apache_access",
        "event_type": "http_request",
        "timestamp":  now,
        "source_ip":  "10.0.0.77",
        "method":     "GET",
        "path":       "/login?id=1' UNION SELECT 1,2--",
        "status":     400,
        "referrer":   "",
        "user_agent": "sqlmap/1.7",
        "raw":        "fake sqli log line",
    })
    # Path traversal
    events.append({
        "source":     "nginx_access",
        "event_type": "http_request",
        "timestamp":  now,
        "source_ip":  "10.0.0.88",
        "method":     "GET",
        "path":       "/../../../../etc/passwd",
        "status":     403,
        "referrer":   "",
        "user_agent": "nikto/2.1.6",
        "raw":        "fake traversal log line",
    })
    # Known bad IP
    events.append({
        "source":     "apache_access",
        "event_type": "http_request",
        "timestamp":  now,
        "source_ip":  "192.168.56.99",
        "method":     "GET",
        "path":       "/",
        "status":     200,
        "referrer":   "",
        "user_agent": "Mozilla/5.0",
        "raw":        "bad ip line",
    })
    # Bad referrer
    events.append({
        "source":     "apache_access",
        "event_type": "http_request",
        "timestamp":  now,
        "source_ip":  "10.0.0.55",
        "method":     "GET",
        "path":       "/index.php",
        "status":     200,
        "referrer":   "http://evil.com/eval(base64_decode(xyz))",
        "user_agent": "Mozilla/5.0",
        "raw":        "bad referrer line",
    })
    # Rate limit flood - 110 requests
    for i in range(110):
        events.append({
            "source":     "nginx_access",
            "event_type": "http_request",
            "timestamp":  now,
            "source_ip":  "10.0.0.99",
            "method":     "GET",
            "path":       f"/api?p={i}",
            "status":     200,
            "referrer":   "",
            "user_agent": "go-http-client/1.1",
            "raw":        f"flood {i}",
        })
    return events

def main():
    parser = argparse.ArgumentParser(description="LightIDS Daemon")
    parser.add_argument("--once",     action="store_true", help="Process logs once and exit")
    parser.add_argument("--simulate", action="store_true", help="Inject fake attack events")
    parser.add_argument("--config",   default=None,        help="Path to config.yaml")
    args = parser.parse_args()

    config  = load_config(args.config)
    db_path = get_db_path(config)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    init_db(db_path)
    poll_interval = int(config.get("monitoring", {}).get("poll_interval", 5))
    engine = DetectionEngine(config, db_path)

    logger.info("=" * 55)
    logger.info("  LightIDS Daemon - Starting")
    logger.info(f"  DB: {db_path}")
    logger.info(f"  Interval: {poll_interval}s | Rules: {len(engine.rules)}")
    logger.info("=" * 55)

    if args.simulate:
        logger.info("Simulation mode - injecting fake events")
        n = engine.process_events(_fake_events())
        logger.info(f"Simulation done: {n} alerts generated")
        return

    if args.once:
        events = collect_all(config, db_path)
        n = engine.process_events(events)
        logger.info(f"One-shot: {len(events)} events, {n} alerts")
        return

    logger.info("Monitoring loop started. Ctrl+C to stop.")
    while _running:
        try:
            events = collect_all(config, db_path)
            if events:
                n = engine.process_events(events)
                logger.info(f"Processed {len(events)} events -> {n} alerts")
        except Exception as e:
            logger.error(f"Loop error: {e}", exc_info=True)
        for _ in range(poll_interval * 2):
            if not _running:
                break
            time.sleep(0.5)
    logger.info("Stopped.")

if __name__ == "__main__":
    main()

