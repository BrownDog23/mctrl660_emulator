import socket
import threading
import time

BIND_IP = "0.0.0.0"
PORTS = [6666, 5200, 3800, 38899, 50000, 60000, 10000, 2000, 3000, 1900]

def serve(port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except Exception:
        pass
    s.bind((BIND_IP, port))
    print(f"[UDP:{port}] Listening on {BIND_IP}:{port}")
    while True:
        data, addr = s.recvfrom(8192)
        print(f"[UDP:{port}] RX from {addr} len={len(data)} hex={data.hex()}")

for p in PORTS:
    threading.Thread(target=serve, args=(p,), daemon=True).start()

print("UDP multi sniffer running. Ctrl+C to stop.")
while True:
    time.sleep(3600)