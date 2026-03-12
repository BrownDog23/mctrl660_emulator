import socket
import struct

MCAST_GRP = "224.224.125.119"
PORTS = [6666, 5200, 3800, 6000, 7000, 8000, 10000]  # candidate
BIND_IP = "0.0.0.0"

def listen(port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((BIND_IP, port))

    mreq = struct.pack("=4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"[MCAST] Listening {MCAST_GRP}:{port}")
    while True:
        data, addr = s.recvfrom(8192)
        print(f"[MCAST:{port}] RX from {addr} len={len(data)} hex={data.hex()}")

if __name__ == "__main__":
    # parte dal porto più probabile: 6666 e 5200 sono spesso usati in ecosistemi NovaStar
    for p in PORTS:
        try:
            listen(p)
        except OSError as e:
            print(f"[MCAST:{p}] bind/join error: {e}")