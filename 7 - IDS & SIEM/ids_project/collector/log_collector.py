import os
import re
import logging
from datetime import datetime
from utils.db import get_log_offset, set_log_offset

logger = logging.getLogger("ids.collector")

_AUTH_FAILED = re.compile(
    r"(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\S+).*?"
    r"(?:Failed password|Invalid user|authentication failure)"
)
_AUTH_IP = re.compile(r"from\s+(?P<ip>\d+\.\d+\.\d+\.\d+)")
_AUTH_USER = re.compile(r"for\s+(?P<user>\S+)\s+from")
_AUTH_ACCEPTED = re.compile(
    r"(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\S+).*?"
    r"Accepted (?:password|publickey) for (?P<user>\S+) from (?P<ip>\d+\.\d+\.\d+\.\d+)"
)
_HTTP_ACCESS = re.compile(
    r'(?P<ip>\S+)\s+-\s+\S+\s+\[(?P<dt>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d+)\s+\S+'
    r'(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<ua>[^"]*)")?'
)

def _sanitize(v):
    return re.sub(r"[\x00-\x1f\x7f]", "", str(v or ""))[:2048]

def _syslog_ts(month, day, time_str):
    try:
        dt = datetime.strptime(
            f"{datetime.now().year} {month} {day} {time_str}",
            "%Y %b %d %H:%M:%S"
        )
        return dt.isoformat()
    except Exception:
        return datetime.now().isoformat()

def _http_ts(dt_str):
    try:
        return datetime.strptime(
            dt_str.split()[0], "%d/%b/%Y:%H:%M:%S"
        ).isoformat()
    except Exception:
        return datetime.now().isoformat()

def parse_auth_line(line):
    line = _sanitize(line)
    m = _AUTH_FAILED.search(line)
    if m:
        ip_m   = _AUTH_IP.search(line)
        user_m = _AUTH_USER.search(line)
        return {
            "source":     "auth_log",
            "event_type": "auth_failed",
            "timestamp":  _syslog_ts(m.group("month"), m.group("day"), m.group("time")),
            "source_ip":  ip_m.group("ip") if ip_m else "",
            "user":       user_m.group("user") if user_m else "",
            "raw":        line,
            "message":    line,
        }
    m = _AUTH_ACCEPTED.search(line)
    if m:
        return {
            "source":     "auth_log",
            "event_type": "auth_accepted",
            "timestamp":  _syslog_ts(m.group("month"), m.group("day"), m.group("time")),
            "source_ip":  m.group("ip"),
            "user":       m.group("user"),
            "raw":        line,
            "message":    line,
        }
    return {
        "source":     "auth_log",
        "event_type": "auth_generic",
        "timestamp":  datetime.now().isoformat(),
        "source_ip":  "",
        "user":       "",
        "raw":        line,
        "message":    line,
    }

def parse_http_line(line, source="apache_access"):
    line = _sanitize(line)
    m = _HTTP_ACCESS.match(line)
    if not m:
        return None
    return {
        "source":     source,
        "event_type": "http_request",
        "timestamp":  _http_ts(m.group("dt")),
        "source_ip":  m.group("ip"),
        "method":     m.group("method"),
        "path":       _sanitize(m.group("path")),
        "status":     int(m.group("status")),
        "referrer":   _sanitize(m.group("referrer") or ""),
        "user_agent": _sanitize(m.group("ua") or ""),
        "raw":        line,
    }

def parse_syslog_line(line):
    line = _sanitize(line)
    return {
        "source":     "syslog",
        "event_type": "syslog",
        "timestamp":  datetime.now().isoformat(),
        "source_ip":  "",
        "user":       "",
        "message":    line,
        "raw":        line,
    }

_PARSERS = {
    "auth_log":      parse_auth_line,
    "syslog":        parse_syslog_line,
    "apache_access": lambda l: parse_http_line(l, "apache_access"),
    "nginx_access":  lambda l: parse_http_line(l, "nginx_access"),
    "apache_error":  parse_syslog_line,
}

def read_new_lines(log_name, log_path, db_path):
    if not os.path.exists(log_path):
        return []
    offset = get_log_offset(db_path, log_path)
    events = []
    try:
        with open(log_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            if offset > file_size:
                offset = 0
            f.seek(offset)
            raw = f.read()
            new_offset = f.tell()
        parser = _PARSERS.get(log_name)
        if not parser:
            return []
        for raw_line in raw.decode("utf-8", errors="replace").splitlines():
            if raw_line.strip():
                try:
                    event = parser(raw_line)
                    if event:
                        events.append(event)
                except Exception:
                    pass
        set_log_offset(db_path, log_path, new_offset)
    except PermissionError:
        logger.warning(f"Permission denied: {log_path}")
    except Exception as e:
        logger.error(f"Error reading {log_path}: {e}")
    return events

def collect_all(config, db_path):
    all_events = []
    for log_name, log_path in config.get("log_paths", {}).items():
        all_events.extend(read_new_lines(log_name, log_path, db_path))
    return all_events




