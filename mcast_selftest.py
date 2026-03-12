import socket, struct, threading, time

MCAST_GRP = "224.224.125.119"
PORT = 3800
IFACE_IP = "192.168.0.11"   # IP device (alias)
TTL = 1

def rx():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))

    mreq = struct.pack("=4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(IFACE_IP))
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"[RX] joined {MCAST_GRP}:{PORT} on iface {IFACE_IP}")
    while True:
        data, addr = s.recvfrom(2048)
        print(f"[RX] from {addr} len={len(data)} hex={data.hex()} ascii={data!r}")

def tx():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(IFACE_IP))
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)  # fondamentale per self-test

    payload = b"SELFTEST"
    while True:
        s.sendto(payload, (MCAST_GRP, PORT))
        print(f"[TX] -> {MCAST_GRP}:{PORT} {payload!r}")
        time.sleep(1)

threading.Thread(target=rx, daemon=True).start()
time.sleep(0.2)
tx()