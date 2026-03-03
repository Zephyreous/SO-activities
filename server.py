from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import os
import datetime
import psutil
import subprocess

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": ["http://127.0.0.1:8080"]}},
    allow_headers=["Content-Type", "X-API-KEY"],
    methods=["GET", "POST", "OPTIONS"],
)

API_KEY = os.environ.get("API_KEY", "CAMBIA_ESTE_TOKEN")

def log_event(event: str):
    with open("activity.log", "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} - {event}\n")

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if not key:
            return jsonify({"error": "Falta header X-API-KEY"}), 401
        if key != API_KEY:
            return jsonify({"error": "API Key inválida"}), 403
        return f(*args, **kwargs)
    return wrapper

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/metrics")
@require_api_key
def metrics():
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    log_event("Consulta /metrics")
    return jsonify({"cpu": cpu, "ram": ram, "disk": disk}), 200

@app.get("/processes")
@require_api_key
def processes():
    result = subprocess.run(
        ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")[:15]
    log_event("Consulta /processes")
    return jsonify({"top_processes": lines}), 200

@app.get("/logs")
@require_api_key
def logs():
    try:
        with open("activity.log", "r") as f:
            lines = f.readlines()[-20:]
        return jsonify({"logs": lines}), 200
    except:
        return jsonify({"logs": []}), 200

if __name__ == "__main__":
    context = ("certs/server.crt", "certs/server.key")
    app.run(host="0.0.0.0", port=5443, ssl_context=context)
