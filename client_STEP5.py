import socket

PORT = 5200
TIMEOUT = 2

DISCOVERY = b"\xAA\x55\x01\x00\x00\x00"
SERIAL_LEN = 20

def recv_once(sock):
    data, addr = sock.recvfrom(2048)
    return data, addr

def parse_discovery_response(data: bytes):
    # Packet: AA55 | cmd | len(2) | payload | crc
    if len(data) < 6:
        return "too short"

    header = data[:2]
    cmd = data[2]
    length = int.from_bytes(data[3:5], "big")
    payload = data[5:5+length]

    out = []
    out.append(f"header={header.hex()} cmd=0x{cmd:02X} len={length}")

    # Payload v1 (27)
    if len(payload) >= 27:
        model = payload[0:16].split(b"\x00", 1)[0].decode("ascii", errors="replace")
        fw = payload[16:24].split(b"\x00", 1)[0].decode("ascii", errors="replace")
        ports = payload[24]
        model_id = int.from_bytes(payload[25:27], "big")
        out.append(f"model={model} fw={fw} ports={ports} model_id=0x{model_id:04X}")

    # Payload extra v2: serial(16) + ip(4)
    if len(payload) >= 27 + SERIAL_LEN + 4:
        serial = payload[27:27+SERIAL_LEN].split(b"\x00", 1)[0].decode("ascii", errors="replace")
        ipb = payload[27+SERIAL_LEN:27+SERIAL_LEN+4]
        ip = ".".join(str(x) for x in ipb)
        out.append(f"serial={serial} ip={ip}")
    else:
        out.append("(v2 fields not present or too short)")

    return " | ".join(out)

def test_localhost():
    print("\n=== TEST 5A: localhost ===")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    dst = ("127.0.0.1", PORT)
    print(f">>> send DISCOVERY to {dst}: {DISCOVERY.hex()}")
    sock.sendto(DISCOVERY, dst)

    data, addr = recv_once(sock)
    print(f"<<< recv from {addr}: {data.hex()}")
    print("PARSE:", parse_discovery_response(data))

    sock.close()

def test_broadcast():
    print("\n=== TEST 5B: broadcast (può fallire su WiFi/loopback) ===")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Broadcast generico. Su Windows spesso richiede una interfaccia LAN attiva.
    dst = ("255.255.255.255", PORT)
    print(f">>> send DISCOVERY to {dst}: {DISCOVERY.hex()}")
    sock.sendto(DISCOVERY, dst)

    try:
        data, addr = recv_once(sock)
        print(f"<<< recv from {addr}: {data.hex()}")
        print("PARSE:", parse_discovery_response(data))
    except socket.timeout:
        print("!!! Nessuna risposta in broadcast (normale se non hai una LAN attiva o policy di rete).")

    sock.close()

if __name__ == "__main__":
    test_localhost()
    test_broadcast()
    print("\n>>> TEST STEP 5 COMPLETATO")
