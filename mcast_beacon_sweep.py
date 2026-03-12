import socket, time

MCAST_GRP = "224.224.125.119"
IFACE_IP = "192.168.0.11"   # tua IP “device”
TTL = 1

PORTS = [3800, 5200, 6666, 6000, 7000, 8000, 9000, 10000, 1947]

# payload “neutro” (poi lo cambiamo se serve)
PAYLOAD = bytes.fromhex("aa55") + b"HELLO_MCTRL660"

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Forza uscita su interfaccia 192.168.0.11
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(IFACE_IP))
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)

    print(f"[TX] Multicast beacon to {MCAST_GRP} from iface {IFACE_IP}")

    while True:
        for p in PORTS:
            s.sendto(PAYLOAD, (MCAST_GRP, p))
            print(f"[TX] -> {MCAST_GRP}:{p} len={len(PAYLOAD)} hex={PAYLOAD.hex()}")
            time.sleep(0.05)
        time.sleep(0.5)

if __name__ == "__main__":
    main()