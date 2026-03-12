import socket

PORT = 3800
REQ = b"rqProMI:"
RESP = b"rpProMI:App,0161"

# forza la rete "device"
IFACE_IP = "192.168.0.11"
BCAST_IP = "192.168.0.255"

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # IMPORTANTISSIMO: bind su interfaccia 192.168.0.11 (non 0.0.0.0)
    s.bind((IFACE_IP, PORT))
    print(f"[UDP:{PORT}] Listening on {IFACE_IP}:{PORT}")

    while True:
        data, addr = s.recvfrom(2048)

        # accetta solo richieste dalla rete 192.168.0.x
        if not addr[0].startswith("192.168.0."):
            continue
            
        # subito dopo recvfrom
        if addr[0] == "192.168.0.11":
            continue

        print(f"[UDP:{PORT}] RX from {addr} len={len(data)} hex={data.hex()} ascii={data!r}")

        if data == REQ:
            # rispondi in broadcast sulla subnet 192.168.0.0/24
            s.sendto(RESP, (BCAST_IP, PORT))
            print(f"[UDP:{PORT}] TX BROADCAST to {(BCAST_IP, PORT)} len={len(RESP)} hex={RESP.hex()} ascii={RESP!r}")
        else:
            print("[UDP:3800] Ignored (not rqProMI:)")

if __name__ == "__main__":
    main()