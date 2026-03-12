import socket
import threading

HOST = "0.0.0.0"
PORTS = [443, 5200, 6666]

def serve(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port))
        s.listen(5)
        print(f"[TCP] Listening on {HOST}:{port}")
        while True:
            conn, addr = s.accept()
            print(f"[TCP:{port}] Connection from {addr}")
            try:
                data = conn.recv(4096)
                print(f"[TCP:{port}] RX {len(data)} bytes: {data.hex()}")
            except Exception as e:
                print(f"[TCP:{port}] recv error: {e}")
            finally:
                try:
                    conn.close()
                except:
                    pass

for p in PORTS:
    threading.Thread(target=serve, args=(p,), daemon=True).start()

print("Tri-listener running. Press Ctrl+C to stop.")
threading.Event().wait()


def udp_6666():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", 6666))
    print("[UDP] Listening on 0.0.0.0:6666")
    while True:
        data, addr = s.recvfrom(8192)
        print(f"[UDP:6666] From {addr} {len(data)} bytes: {data.hex()}")

threading.Thread(target=udp_6666, daemon=True).start()