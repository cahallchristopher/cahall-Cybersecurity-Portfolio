import os, sys, json, logging
from functools import wraps
from datetime import datetime
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, Response)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_loader import load_config
from utils.db import (get_db_path, init_db, get_alerts, get_summary,
                      get_blocked_ips, export_alerts_json, export_alerts_csv)
from utils import geoip as geoip_module

config  = load_config()
db_path = get_db_path(config)
init_db(db_path)

app = Flask(__name__, template_folder="templates")
app.secret_key = config["dashboard"]["secret_key"]

DASH_USER = config["dashboard"]["username"]
DASH_PASS = config["dashboard"]["password"]

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if (request.form.get("username") == DASH_USER and
                request.form.get("password") == DASH_PASS):
            session["logged_in"] = True
            session["username"]  = request.form.get("username")
            return redirect(url_for("dashboard"))
        error = "Invalid credentials."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    summary = get_summary(db_path)
    alerts  = get_alerts(db_path, limit=50)
    blocked = get_blocked_ips(db_path)
    for entry in summary.get("top_ips", []):
        try:
            geo = geoip_module.lookup(entry["source_ip"])
            entry["location"] = geoip_module.format_location(geo)
            entry["country"]  = geo.get("country", "")
        except Exception:
            entry["location"] = "Unknown"
            entry["country"]  = ""
    return render_template("index.html",
                           summary=summary,
                           alerts=alerts,
                           blocked=blocked,
                           now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route("/api/summary")
@login_required
def api_summary():
    return jsonify(get_summary(db_path))

@app.route("/api/alerts")
@login_required
def api_alerts():
    return jsonify(get_alerts(
        db_path,
        limit=int(request.args.get("limit", 100)),
        alert_type=request.args.get("type"),
        source_ip=request.args.get("ip"),
    ))

@app.route("/api/timeline")
@login_required
def api_timeline():
    return jsonify(get_summary(db_path).get("timeline", []))

@app.route("/export/json")
@login_required
def export_json():
    return Response(export_alerts_json(db_path),
                    mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=alerts.json"})

@app.route("/export/csv")
@login_required
def export_csv():
    return Response(export_alerts_csv(db_path),
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=alerts.csv"})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    app.run(
        host=config["dashboard"]["host"],
        port=int(config["dashboard"]["port"]),
        debug=False,
    )
