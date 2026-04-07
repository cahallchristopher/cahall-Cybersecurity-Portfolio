import logging
from collections import defaultdict
from detector.rules import load_rules
from utils.db import insert_alert, mark_ip_blocked
from utils import ip_blocker

logger = logging.getLogger("ids.engine")

class DetectionEngine:
    def __init__(self, config, db_path):
        self.config   = config
        self.db_path  = db_path
        self.rules    = load_rules(config)
        self.blocking_enabled = config.get("ip_blocking", {}).get("enabled", False)
        self.block_threshold  = config.get("ip_blocking", {}).get("repeat_offender_threshold", 3)
        self._ip_alert_counts = defaultdict(int)
        self._blocked_ips     = set()
        logger.info(f"[ENGINE] {len(self.rules)} rules loaded. Blocking: {'ON' if self.blocking_enabled else 'OFF'}")

    def process_event(self, event):
        fired = []
        for rule in self.rules:
            try:
                alert = rule.check(event)
                if alert:
                    alert["id"] = insert_alert(self.db_path, alert)
                    fired.append(alert)
                    self._log_alert(alert)
                    self._maybe_block(alert)
            except Exception as e:
                logger.error(f"Rule {rule.name} error: {e}", exc_info=True)
        return fired

    def process_events(self, events):
        total = 0
        for event in events:
            total += len(self.process_event(event))
        return total

    def _log_alert(self, alert):
        icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        icon  = icons.get(alert["severity"], "⚪")
        logger.warning(
            f"{icon} [{alert['alert_type'].upper()}] "
            f"IP={alert['source_ip']} | {alert['description']}"
        )

    def _maybe_block(self, alert):
        if not self.blocking_enabled:
            return
        ip = alert["source_ip"]
        if ip in self._blocked_ips:
            return
        self._ip_alert_counts[ip] += 1
        if self._ip_alert_counts[ip] >= self.block_threshold:
            if ip_blocker.block_ip(ip, reason=alert["alert_type"]):
                mark_ip_blocked(self.db_path, ip, alert["alert_type"])
                self._blocked_ips.add(ip)

