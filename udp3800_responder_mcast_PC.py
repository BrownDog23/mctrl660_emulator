import socket
import struct

BIND_IP = "192.168.0.11"
PORT = 3800

MCAST_GRP = "224.224.125.119"
MCAST_TTL = 1

REQ  = b"rqProMI:"
RESP = b"rpProMI:App,0161"

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind sul "device IP" e porta 3800 => source port = 3800 (fondamentale)
    s.bind((BIND_IP, PORT))
    print(f"[UDP:{PORT}] Listening on {BIND_IP}:{PORT}")

    # forza l'interfaccia multicast sull'alias (device IP)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(BIND_IP))
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MCAST_TTL)

    # (opzionale) evita che il tuo stesso host si riascolti la sua multicast
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

    while True:
        data, addr = s.recvfrom(2048)

        # ignora eventuale echo locale
        if addr[0] == BIND_IP:
            continue

        print(f"[UDP:{PORT}] RX from {addr} len={len(data)} hex={data.hex()} ascii={data!r}")

        if data != REQ:
            print("[UDP:3800] Ignored (not rqProMI:)")
            continue

        # 1) broadcast subnet
        bcast = ("192.168.0.255", PORT)
        s.sendto(RESP, bcast)
        print(f"[UDP:{PORT}] TX BROADCAST -> {bcast} {RESP!r}")

        # 2) multicast group (stessa source ip/port del socket bindato)
        mcast = (MCAST_GRP, PORT)
        s.sendto(RESP, mcast)
        print(f"[UDP:{PORT}] TX MCAST -> {mcast} {RESP!r}")

if __name__ == "__main__":
    main()