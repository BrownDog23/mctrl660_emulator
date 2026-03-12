# tcp_handler.py
# LISTEN-FIRST diagnostic handler:
# - Dopo handshake TLS, non invia nulla.
# - Ascolta per 1.5s in finestre da 200ms per catturare eventuali primi byte da NovaLCT.
# - Logga i primi byte in hex (max 128 bytes).
# - Poi chiude (return).

import socket
import time

try:
    # Se esiste nel tuo progetto, meglio usare logger comune
    from logger import log_text, log_packet
except Exception:
    # Fallback (non dovrebbe servire)
    def log_text(msg: str):
        print(msg)

    def log_packet(prefix: str, data: bytes):
        print(prefix, data.hex())


LISTEN_FIRST_WINDOW_SEC = 5.0
RECV_TIMEOUT_SEC = 1.2
MAX_DUMP_BYTES = 128


def handle_tcp_stream(conn: socket.socket, addr):
    """
    Handler TCP/TLS stream.
    In questa versione diagnostica:
    - ascolta solamente (server "listen-first")
    - NON manda alcun frame
    - logga se riceve dati
    """
    # timeout corto per poll non-bloccante
    conn.settimeout(RECV_TIMEOUT_SEC)

    deadline = time.time() + LISTEN_FIRST_WINDOW_SEC
    got_any = False
    total_bytes = 0

    log_text(f"[TCP] Listen-first window started ({LISTEN_FIRST_WINDOW_SEC}s) for {addr}")

    while time.time() < deadline:
        try:
            data = conn.recv(4096)
        except socket.timeout:
            # nessun dato in questo slot -> riprova
            continue
        except ConnectionResetError:
            log_text(f"[TCP] Peer reset (10054) {addr}")
            return
        except Exception as e:
            log_text(f"[TCP] recv error {addr}: {e}")
            return

        if not data:
            # chiusura pulita dal client
            log_text(f"[TCP] Peer closed connection {addr}")
            return

        got_any = True
        total_bytes += len(data)

        # Log corto (prime N bytes)
        head = data[:MAX_DUMP_BYTES]
        log_text(f"[TCP] RX {len(data)} bytes (total {total_bytes}) from {addr}: {head.hex()}...")
        # Log “packet” completo del chunk ricevuto (se vuoi più dettaglio)
        log_packet(f"[TCP RX CHUNK {addr}]", data)

        # continuiamo a leggere finché siamo nella finestra

    if not got_any:
        log_text(f"[TCP] Listen-first window ended: NO DATA from {addr}")
    else:
        log_text(f"[TCP] Listen-first window ended: GOT DATA (total {total_bytes} bytes) from {addr}")

    # Fine test diagnostico
    return