import socket
import time
from logger import log_packet, log_text
from protocol_55aa import try_extract_frame, Frame55AA
from novastar_fe_decoder import decode_fe_21
from fader_state import FaderState

# =========================
# CONFIG
# =========================
ACK_MODE = "mirror"   # "none" | "mirror"
LOG_STATE_CHANGES = True

# =========================
# GLOBAL STATE
# =========================
fader_state = FaderState()
_last_snapshot = None


def handle_tcp_stream(conn: socket.socket, addr):
    global _last_snapshot

    conn.settimeout(5.0)
    buf = bytearray()

    while True:
        data = conn.recv(4096)
        if not data:
            return

        log_packet(f"[TCP RX {addr}]", data)
        buf.extend(data)

        # Estrazione multipla frame
        while True:
            frame = try_extract_frame(buf)
            if frame is None:
                break

            log_packet(f"[TCP FRAME {addr}]", frame.raw)

            # =========================
            # ACK MIRROR (opzionale)
            # =========================
            if ACK_MODE == "mirror":
                try:
                    conn.sendall(frame.raw)
                except Exception as e:
                    log_text(f"[TCP] ACK send error: {e}")

            # =========================
            # DECODE FE
            # =========================
            info = decode_fe_21(frame.raw)
            if info:
                log_text(
                    f"[DECODE] addr=0x{info['addr']:04X} "
                    f"side={info['side']} "
                    f"value={info['value']} "
                    f"crc=0x{info['crc']:04X}"
                )

                # Update stato
                fader_state.update(
                    side=info["side"],
                    value=info["value"],
                    peer=addr
                )

                # =========================
                # LOG SOLO SE CAMBIA
                # =========================
                if LOG_STATE_CHANGES:
                    snapshot = fader_state.snapshot()
                    if (
                        _last_snapshot is None
                        or snapshot.left_value != _last_snapshot.left_value
                        or snapshot.right_value != _last_snapshot.right_value
                    ):
                        log_text(
                            f"[STATE] LEFT={snapshot.left_value} "
                            f"RIGHT={snapshot.right_value}"
                        )
                        _last_snapshot = snapshot
