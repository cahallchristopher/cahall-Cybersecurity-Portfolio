import sqlite3
import json
import os
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_db_path(config):
    return os.path.join(_BASE_DIR, config["database"]["path"])

def get_connection(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = get_connection(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            source_ip   TEXT    NOT NULL,
            alert_type  TEXT    NOT NULL,
            severity    TEXT    NOT NULL,
            description TEXT    NOT NULL,
            raw_log     TEXT,
            blocked     INTEGER DEFAULT 0,
            extra       TEXT
        );
        CREATE TABLE IF NOT EXISTS blocked_ips (
            ip          TEXT PRIMARY KEY,
            blocked_at  TEXT NOT NULL,
            reason      TEXT
        );
        CREATE TABLE IF NOT EXISTS log_offsets (
            log_file    TEXT PRIMARY KEY,
            byte_offset INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()
    print(f"[DB] Ready at {db_path}")

def insert_alert(db_path, alert):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (timestamp,source_ip,alert_type,severity,description,raw_log,extra) VALUES (?,?,?,?,?,?,?)",
        (
            alert.get("timestamp", datetime.now().isoformat()),
            alert["source_ip"],
            alert["alert_type"],
            alert["severity"],
            alert["description"],
            alert.get("raw_log", ""),
            json.dumps(alert.get("extra", {})),
        ),
    )
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id

def mark_ip_blocked(db_path, ip, reason):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO blocked_ips (ip,blocked_at,reason) VALUES (?,?,?)",
        (ip, datetime.now().isoformat(), reason),
    )
    cur.execute("UPDATE alerts SET blocked=1 WHERE source_ip=? AND blocked=0", (ip,))
    conn.commit()
    conn.close()

def get_log_offset(db_path, log_file):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT byte_offset FROM log_offsets WHERE log_file=?", (log_file,))
    row = cur.fetchone()
    conn.close()
    return row["byte_offset"] if row else 0

def set_log_offset(db_path, log_file, offset):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO log_offsets (log_file,byte_offset) VALUES (?,?)",
        (log_file, offset),
    )
    conn.commit()
    conn.close()

def get_alerts(db_path, limit=200, alert_type=None, source_ip=None):
    conn = get_connection(db_path)
    cur = conn.cursor()
    conditions, params = [], []
    if alert_type:
        conditions.append("alert_type=?")
        params.append(alert_type)
    if source_ip:
        conditions.append("source_ip=?")
        params.append(source_ip)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)
    cur.execute(f"SELECT * FROM alerts {where} ORDER BY id DESC LIMIT ?", params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_summary(db_path):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM alerts")
    total = cur.fetchone()["total"]
    cur.execute("SELECT alert_type, COUNT(*) as cnt FROM alerts GROUP BY alert_type")
    by_type = {r["alert_type"]: r["cnt"] for r in cur.fetchall()}
    cur.execute("SELECT severity, COUNT(*) as cnt FROM alerts GROUP BY severity")
    by_severity = {r["severity"]: r["cnt"] for r in cur.fetchall()}
    cur.execute("SELECT source_ip, COUNT(*) as cnt FROM alerts GROUP BY source_ip ORDER BY cnt DESC LIMIT 10")
    top_ips = [dict(r) for r in cur.fetchall()]
    cur.execute("""
        SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour, COUNT(*) as cnt
        FROM alerts WHERE timestamp >= datetime('now','-24 hours')
        GROUP BY hour ORDER BY hour
    """)
    timeline = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) as cnt FROM blocked_ips")
    blocked_count = cur.fetchone()["cnt"]
    conn.close()
    return {
        "total": total,
        "by_type": by_type,
        "by_severity": by_severity,
        "top_ips": top_ips,
        "timeline": timeline,
        "blocked_count": blocked_count,
    }

def get_blocked_ips(db_path):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM blocked_ips ORDER BY blocked_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def export_alerts_json(db_path):
    return json.dumps(get_alerts(db_path, limit=100000), indent=2)

def export_alerts_csv(db_path):
    import csv, io
    alerts = get_alerts(db_path, limit=100000)
    if not alerts:
        return ""
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=alerts[0].keys())
    w.writeheader()
    w.writerows(alerts)
    return out.getvalue()


