import socket
import threading

HOST = "192.168.0.11"
PORTS = [5200, 6666, 6000, 7000, 8000, 9000, 10000]

def serve(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port))
        s.listen(50)
        print(f"[TCP] Listening on {HOST}:{port}")
        while True:
            conn, addr = s.accept()
            print(f"[TCP:{port}] Connection from {addr}")
            try:
                conn.settimeout(2)
                data = conn.recv(4096)
                print(f"[TCP:{port}] RX {len(data)} bytes: {data.hex()}")
            except socket.timeout:
                print(f"[TCP:{port}] RX timeout")
            except Exception as e:
                print(f"[TCP:{port}] RX error: {e}")
            finally:
                try:
                    conn.close()
                except:
                    pass

for p in PORTS:
    threading.Thread(target=serve, args=(p,), daemon=True).start()

print("Multi TCP probe running. Ctrl+C to stop.")
#threading.Event().wait()
import time
while True:
    time.sleep(3600)