from __future__ import annotations

from flask import Flask, request, jsonify
import psutil
import subprocess
from typing import Dict, Any, List

app = Flask(__name__)

#Allowlist para Ubuntu (ajusta según tu entorno)
ALLOWED_APPS: Dict[str, List[str]] = {
    "gedit": ["gedit"],
    "calculator": ["gnome-calculator"],
    "xterm": ["xterm"],
    "firefox": ["firefox"],          # si está instalado
    "sleep10": ["sleep", "10"],      # ejemplo “controlado” para pruebas
}

def process_to_dict(p: psutil.Process) -> Dict[str, Any]:
    try:
        with p.oneshot():
            return {
                "pid": p.pid,
                "name": p.name(),
                "status": p.status(),
                "cpu_percent": p.cpu_percent(interval=0.0),
                "memory_mb": round(p.memory_info().rss / (1024 * 1024), 2),
                "user": p.username(),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {"pid": p.pid, "name": "N/A", "status": "N/A", "cpu_percent": None, "memory_mb": None, "user": None}

@app.get("/health")
def health():
    return jsonify({"ok": True, "message": "Servidor activo (Ubuntu)"}), 200

@app.get("/processes")
def list_processes():
    limit = int(request.args.get("limit", 50))
    procs = []
    for p in psutil.process_iter(attrs=[], ad_value=None):
        procs.append(process_to_dict(p))
        if len(procs) >= limit:
            break
    return jsonify({"count": len(procs), "processes": procs}), 200

@app.post("/start")
def start_app():
    """
    JSON: {"app": "gedit"}
    """
    data = request.get_json(silent=True) or {}
    key = (data.get("app") or "").strip().lower()

    if not key:
        return jsonify({"error": "Falta 'app' en el JSON."}), 400

    if key not in ALLOWED_APPS:
        return jsonify({"error": "App no permitida (allowlist).", "allowed_apps": sorted(ALLOWED_APPS.keys())}), 403

    cmd = ALLOWED_APPS[key]
    try:
        proc = subprocess.Popen(cmd, start_new_session=True)
        return jsonify({"message": "Proceso iniciado", "app": key, "pid": proc.pid, "cmd": cmd}), 201
    except FileNotFoundError:
        return jsonify({"error": "Comando no encontrado. Instala la app o ajusta ALLOWED_APPS."}), 500
    except Exception as e:
        return jsonify({"error": "No se pudo iniciar el proceso", "details": str(e)}), 500

@app.post("/stop")
def stop_process():
    """
    JSON: {"pid": 1234}
    """
    data = request.get_json(silent=True) or {}
    pid = data.get("pid")

    if pid is None:
        return jsonify({"error": "Falta 'pid' en el JSON."}), 400

    try:
        pid = int(pid)
    except ValueError:
        return jsonify({"error": "'pid' debe ser entero."}), 400

    try:
        p = psutil.Process(pid)
        p.terminate()
        try:
            p.wait(timeout=3)
            return jsonify({"message": "Proceso terminado (SIGTERM)", "pid": pid}), 200
        except psutil.TimeoutExpired:
            p.kill()
            p.wait(timeout=3)
            return jsonify({"message": "Proceso eliminado (SIGKILL)", "pid": pid}), 200

    except psutil.NoSuchProcess:
        return jsonify({"error": "No existe ese PID", "pid": pid}), 404
    except psutil.AccessDenied:
        return jsonify({"error": "Acceso denegado: permisos insuficientes", "pid": pid}), 403
    except Exception as e:
        return jsonify({"error": "No se pudo detener el proceso", "details": str(e)}), 500

@app.get("/stats/<int:pid>")
def stats(pid: int):
    try:
        p = psutil.Process(pid)
        with p.oneshot():
            cpu = p.cpu_percent(interval=0.2)
            mem_mb = round(p.memory_info().rss / (1024 * 1024), 2)
            return jsonify({
                "pid": pid,
                "name": p.name(),
                "status": p.status(),
                "cpu_percent": cpu,
                "memory_mb": mem_mb,
                "user": p.username(),
                "cmdline": p.cmdline(),
            }), 200
    except psutil.NoSuchProcess:
        return jsonify({"error": "No existe ese PID", "pid": pid}), 404
    except psutil.AccessDenied:
        return jsonify({"error": "Acceso denegado: permisos insuficientes", "pid": pid}), 403

if __name__ == "__main__":
    # Solo localhost: evita que tu servidor se convierta en “control remoto del laboratorio”
    app.run(host="127.0.0.1", port=5000, debug=True)

