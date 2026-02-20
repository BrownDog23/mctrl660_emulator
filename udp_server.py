import socket
from logger import log_text
from udp_handler import handle_udp

UDP_PORT = 5200  # confermeremo con sniffing

def start_udp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", UDP_PORT))

    log_text(f"UDP server in ascolto su 0.0.0.0:{UDP_PORT}")

    while True:
        data, addr = sock.recvfrom(2048)

        try:
            response = handle_udp(data, addr)
        except Exception as e:
            import traceback
            log_text(f"ERROR in handle_udp: {e}")
            traceback.print_exc()
            continue

        if not response:
            continue

        if isinstance(response, list):
            for r in response:
                sock.sendto(r, addr)
        else:
            sock.sendto(response, addr)

if __name__ == "__main__":
    start_udp()
