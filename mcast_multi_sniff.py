import socket, struct, threading, time

MCAST_GRP = "224.224.125.119"
BIND_IP = "0.0.0.0"
PORTS = [3800, 5200, 6666, 6000, 7000, 8000, 9000, 10000, 1947]  # lascia pure 1947: se fallisce lo vediamo

def listen(port: int):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Su Windows, SO_REUSEPORT spesso non esiste / non serve. Non lo usiamo.

        s.bind((BIND_IP, port))

        mreq = struct.pack("=4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(f"[MCAST] Listening {MCAST_GRP}:{port}")

        while True:
            data, addr = s.recvfrom(8192)
            print(f"[MCAST:{port}] RX from {addr} len={len(data)} hex={data.hex()}")

    except PermissionError as e:
        print(f"[MCAST:{port}] PermissionError (WinError 10013) -> porta occupata o riservata. {e}")
    except OSError as e:
        print(f"[MCAST:{port}] OSError -> {e}")

if __name__ == "__main__":
    for p in PORTS:
        threading.Thread(target=listen, args=(p,), daemon=True).start()

    print("MCAST multi sniffer running. Ctrl+C to stop.")
    while True:
        time.sleep(3600)