import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger("ids.rules")

class BaseRule:
    name = "base"
    def __init__(self, config):
        self.config = config
        self.enabled = True

    def _make_alert(self, event, alert_type, severity, description, extra=None):
        return {
            "timestamp":   event.get("timestamp", datetime.now().isoformat()),
            "source_ip":   event.get("source_ip", "0.0.0.0"),
            "alert_type":  alert_type,
            "severity":    severity,
            "description": description,
            "raw_log":     event.get("raw", ""),
            "extra":       extra or {},
        }

    def check(self, event):
        raise NotImplementedError


class BruteForceRule(BaseRule):
    name = "brute_force"
    def __init__(self, config):
        super().__init__(config)
        cfg = config.get("detection", {}).get("brute_force", {})
        self.threshold = int(cfg.get("threshold", 5))
        self.window    = int(cfg.get("window_seconds", 60))
        self.severity  = cfg.get("severity", "HIGH")
        self.enabled   = cfg.get("enabled", True)
        self._tracker  = defaultdict(deque)
        self._alerted  = set()

    def check(self, event):
        if not self.enabled or event.get("source") != "auth_log":
            return None
        if event.get("event_type") != "auth_failed":
            return None
        ip = event.get("source_ip", "")
        if not ip:
            return None
        now    = datetime.now()
        cutoff = now - timedelta(seconds=self.window)
        dq     = self._tracker[ip]
        dq.append(now)
        while dq and dq[0] < cutoff:
            dq.popleft()
        count = len(dq)
        if count >= self.threshold and ip not in self._alerted:
            self._alerted.add(ip)
            return self._make_alert(event, "brute_force", self.severity,
                f"Brute force: {count} failed logins from {ip} in {self.window}s",
                {"attempt_count": count})
        if count < self.threshold:
            self._alerted.discard(ip)
        return None


class CVEPatternRule(BaseRule):
    name = "cve_patterns"
    def __init__(self, config):
        super().__init__(config)
        cfg = config.get("detection", {}).get("cve_patterns", {})
        self.patterns = [p.lower() for p in cfg.get("patterns", [])]
        self.severity  = cfg.get("severity", "CRITICAL")
        self.enabled   = cfg.get("enabled", True)

    def check(self, event):
        if not self.enabled or event.get("event_type") != "http_request":
            return None
        haystack = " ".join([
            event.get("path", ""),
            event.get("user_agent", ""),
            event.get("referrer", ""),
        ]).lower()
        for pattern in self.patterns:
            if pattern in haystack:
                return self._make_alert(event, "cve_exploit", self.severity,
                    f"Exploit pattern '{pattern}' from {event.get('source_ip')} -> {event.get('path')}",
                    {"matched_pattern": pattern})
        return None


class BadCrawlerRule(BaseRule):
    name = "bad_crawlers"
    def __init__(self, config):
        super().__init__(config)
        cfg = config.get("detection", {}).get("bad_crawlers", {})
        self.user_agents = [ua.lower() for ua in cfg.get("user_agents", [])]
        self.severity    = cfg.get("severity", "MEDIUM")
        self.enabled     = cfg.get("enabled", True)

    def check(self, event):
        if not self.enabled or event.get("event_type") != "http_request":
            return None
        ua = event.get("user_agent", "").lower()
        for bad in self.user_agents:
            if bad in ua:
                return self._make_alert(event, "bad_crawler", self.severity,
                    f"Scanner detected: UA contains '{bad}' from {event.get('source_ip')}",
                    {"matched_ua": bad})
        return None


class BadIPRule(BaseRule):
    name = "bad_ips"
    def __init__(self, config):
        super().__init__(config)
        cfg = config.get("detection", {}).get("bad_ips", {})
        self.severity  = cfg.get("severity", "HIGH")
        self.enabled   = cfg.get("enabled", True)
        self.blacklist = set(cfg.get("blacklist", []))
        self._load_file(cfg.get("blocklist_file", ""))

    def _load_file(self, path):
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full = os.path.join(base, path)
        if not os.path.exists(full):
            return
        with open(full) as f:
            for line in f:
                ip = line.strip()
                if ip and not ip.startswith("#"):
                    self.blacklist.add(ip)

    def check(self, event):
        if not self.enabled:
            return None
        ip = event.get("source_ip", "")
        if ip in self.blacklist:
            return self._make_alert(event, "bad_ip", self.severity,
                f"Known malicious IP: {ip}", {"ip": ip})
        return None


class BadReferrerRule(BaseRule):
    name = "bad_referrers"
    def __init__(self, config):
        super().__init__(config)
        cfg = config.get("detection", {}).get("bad_referrers", {})
        self.patterns = [p.lower() for p in cfg.get("patterns", [])]
        self.severity  = cfg.get("severity", "MEDIUM")
        self.enabled   = cfg.get("enabled", True)

    def check(self, event):
        if not self.enabled or event.get("event_type") != "http_request":
            return None
        ref = event.get("referrer", "").lower()
        if not ref or ref == "-":
            return None
        for p in self.patterns:
            if p in ref:
                return self._make_alert(event, "bad_referrer", self.severity,
                    f"Malicious referrer from {event.get('source_ip')}: matched '{p}'",
                    {"matched_pattern": p, "referrer": event.get("referrer")})
        return None


class RateLimitRule(BaseRule):
    name = "rate_limit"
    def __init__(self, config):
        super().__init__(config)
        cfg = config.get("detection", {}).get("rate_limit", {})
        self.max_requests = int(cfg.get("max_requests", 100))
        self.window       = int(cfg.get("window_seconds", 60))
        self.severity     = cfg.get("severity", "MEDIUM")
        self.enabled      = cfg.get("enabled", True)
        self._tracker     = defaultdict(deque)
        self._alerted     = set()

    def check(self, event):
        if not self.enabled or event.get("event_type") != "http_request":
            return None
        ip = event.get("source_ip", "")
        if not ip:
            return None
        now    = datetime.now()
        cutoff = now - timedelta(seconds=self.window)
        dq     = self._tracker[ip]
        dq.append(now)
        while dq and dq[0] < cutoff:
            dq.popleft()
        count = len(dq)
        if count >= self.max_requests and ip not in self._alerted:
            self._alerted.add(ip)
            return self._make_alert(event, "rate_limit", self.severity,
                f"Rate limit exceeded: {count} requests from {ip} in {self.window}s",
                {"request_count": count})
        if count < self.max_requests:
            self._alerted.discard(ip)
        return None


ALL_RULES = [
    BruteForceRule,
    CVEPatternRule,
    BadCrawlerRule,
    BadIPRule,
    BadReferrerRule,
    RateLimitRule,
]

def load_rules(config):
    rules = []
    for RuleClass in ALL_RULES:
        try:
            rules.append(RuleClass(config))
            logger.info(f"[RULES] Loaded: {RuleClass.name}")
        except Exception as e:
            logger.error(f"[RULES] Failed {RuleClass.name}: {e}")
    return rules

