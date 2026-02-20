import socket
import threading
from logger import log_packet, log_text
from tcp_handler import handle_tcp_stream

TCP_PORT = 5200
BIND_IP = "0.0.0.0"  # ascolta su tutte le interfacce

def client_thread(conn: socket.socket, addr):
    log_text(f"[TCP] Client connected: {addr}")
    try:
        handle_tcp_stream(conn, addr)
    except Exception as e:
        log_text(f"[TCP] ERROR for {addr}: {e}")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
        log_text(f"[TCP] Client disconnected: {addr}")

def start_tcp():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((BIND_IP, TCP_PORT))
    srv.listen(5)
    log_text(f"TCP server in ascolto su {BIND_IP}:{TCP_PORT}")

    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    start_tcp()
