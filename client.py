
Visión general creada por IA
Proyecto desarrolla un servidor Flask (Python/psutil) y cliente TCP para administrar procesos en Ubuntu.

#!/usr/bin/env python3
import socket

HOST = "127.0.0.1"
PORT = 5000
BUFFER = 4096

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        bienvenida = s.recv(BUFFER).decode("utf-8", errors="replace")
        print(bienvenida.strip())

        while True:
            cmd = input("cliente> ").strip()
            if not cmd:
                continue

            s.sendall((cmd + "\n").encode("utf-8"))

            resp = s.recv(BUFFER).decode("utf-8", errors="replace").strip()
            print(resp)

            if resp == "BYE":
                break

if __name__ == "__main__":
    main()
