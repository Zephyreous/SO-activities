#!/usr/bin/env python3
import socket
import subprocess
import signal

HOST = "127.0.0.1"   # Localhost (para prácticas). Cambia a 0.0.0.0 si quieres que escuche en red.
PORT = 5000
BUFFER = 4096

HELP_TEXT = """Comandos disponibles:
  HELP                 - Muestra esta ayuda
  LIST                 - Lista procesos (top 10 por PID)
  INFO <pid>           - Muestra info básica de un proceso
  KILL <pid>           - Envía SIGTERM al proceso (solo si es de tu usuario)
  EXIT                 - Cierra la sesión
"""

def run_cmd(cmd: list[str]) -> str:
    """Ejecuta un comando del sistema y devuelve salida como texto."""
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return out.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR ejecutando comando: {' '.join(cmd)}\n{e.output.strip()}"

def list_processes() -> str:
    # ps simple: PID, USER, %CPU, %MEM, COMMAND
    # limitamos a 10 para que sea legible
    out = run_cmd(["ps", "-eo", "pid,user,pcpu,pmem,comm", "--sort=pid"])
    lines = out.splitlines()
    header = lines[0]
    body = lines[1:11]  # primeros 10 procesos
    return "\n".join([header] + body)

def info_process(pid: str) -> str:
    if not pid.isdigit():
        return "ERROR: PID inválido. Usa INFO <pid> con un número.\n" + HELP_TEXT

    out = run_cmd(["ps", "-p", pid, "-o", "pid,user,stat,pcpu,pmem,etime,cmd"])
    if len(out.splitlines()) < 2:
        return f"No encontré el proceso con PID {pid}."
    return out

def kill_process(pid: str) -> str:
    if not pid.isdigit():
        return "ERROR: PID inválido. Usa KILL <pid> con un número."

    # Validación: que el proceso exista y sea del mismo usuario
    who = run_cmd(["ps", "-p", pid, "-o", "user="]).strip()
    if "ERROR" in who or who == "":
        return f"No encontré el proceso con PID {pid}."

    # Usuario actual (quién corre el servidor)
    me = run_cmd(["whoami"]).strip()

    if who != me:
        return f"DENEGADO: El proceso {pid} pertenece a '{who}', pero el servidor corre como '{me}'."

    try:
        # SIGTERM es "termina de forma amable"
        subprocess.check_call(["kill", "-TERM", pid])
        return f"OK: Enviado SIGTERM a PID {pid}."
    except subprocess.CalledProcessError:
        return f"ERROR: No pude terminar el proceso {pid}. (¿Permisos?)"

def handle_command(cmdline: str) -> str:
    cmdline = cmdline.strip()
    if not cmdline:
        return "Escribe un comando. Usa HELP."

    parts = cmdline.split()
    cmd = parts[0].upper()

    if cmd == "HELP":
        return HELP_TEXT
    if cmd == "LIST":
        return list_processes()
    if cmd == "INFO":
        if len(parts) != 2:
            return "Uso: INFO <pid>\n" + HELP_TEXT
        return info_process(parts[1])
    if cmd == "KILL":
        if len(parts) != 2:
            return "Uso: KILL <pid>\n" + HELP_TEXT
        return kill_process(parts[1])
    if cmd == "EXIT":
        return "BYE"
    return "Comando no reconocido. Usa HELP."

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[SERVIDOR] Escuchando en {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"[SERVIDOR] Conexión de {addr}")
                conn.sendall(b"Bienvenido. Escribe HELP para ver comandos.\n")

                while True:
                    data = conn.recv(BUFFER)
                    if not data:
                        print("[SERVIDOR] Cliente desconectado.")
                        break

                    cmdline = data.decode("utf-8", errors="replace")
                    response = handle_command(cmdline)

                    if response == "BYE":
                        conn.sendall(b"BYE\n")
                        print("[SERVIDOR] Sesión terminada por EXIT.")
                        break

                    conn.sendall((response + "\n").encode("utf-8"))

if __name__ == "__main__":
    main()
