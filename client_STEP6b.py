import socket
import time

PORT = 5200
SERVER = ("127.0.0.1", PORT)

TIMEOUT = 0.3
DISCOVERY_WAIT_SEC = 1.0

# Timeout heartbeat del server (metti qui lo stesso valore del server + un margine)
OFFLINE_WAIT_SEC = 13.0

# Helper: costruzione pacchetti
def pkt_discovery():
    return b"\xAA\x55\x01\x00\x00\x00"

def pkt_heartbeat(idx: int):
    # CMD=02, LEN=1, PAYLOAD=idx, CRC=0x00
    return b"\xAA\x55" + bytes([0x02]) + b"\x00\x01" + bytes([idx & 0xFF]) + b"\x00"

def pkt_status(idx: int):
    # CMD=03, LEN=1, PAYLOAD=idx, CRC=0x00
    return b"\xAA\x55" + bytes([0x03]) + b"\x00\x01" + bytes([idx & 0xFF]) + b"\x00"

def parse_discovery_response(data: bytes):
    # AA55 | cmd | len(2) | payload | crc
    if len(data) < 6:
        return None

    cmd = data[2]
    length = int.from_bytes(data[3:5], "big")
    payload = data[5:5+length]

    # V1: 27 byte
    if len(payload) < 27:
        return None

    model = payload[0:16].split(b"\x00", 1)[0].decode("ascii", errors="replace")
    fw = payload[16:24].split(b"\x00", 1)[0].decode("ascii", errors="replace")
    ports = payload[24]
    model_id = int.from_bytes(payload[25:27], "big")

    # V2: serial(20) + ip(4)
    serial = None
    ip = None
    SERIAL_LEN = 20
    if len(payload) >= 27 + SERIAL_LEN + 4:
        serial = payload[27:27+SERIAL_LEN].split(b"\x00", 1)[0].decode("ascii", errors="replace")
        ipb = payload[27+SERIAL_LEN:27+SERIAL_LEN+4]
        ip = ".".join(str(x) for x in ipb)

    return {
        "cmd": cmd,
        "model": model,
        "fw": fw,
        "ports": ports,
        "model_id": model_id,
        "serial": serial,
        "ip": ip,
        "raw": data.hex(),
    }

def parse_status_response(data: bytes):
    if len(data) < 6:
        return None
    cmd = data[2]
    length = int.from_bytes(data[3:5], "big")
    payload = data[5:5+length]

    if cmd != 0x83 or len(payload) < 4:
        return {"cmd": cmd, "length": length, "payload_hex": payload.hex()}

    temp = payload[0]
    ports = payload[1]
    mask = payload[2]
    online = payload[3]
    return {
        "cmd": cmd,
        "temp_c": temp,
        "ports": ports,
        "mask": mask,
        "online": online,
        "payload_hex": payload.hex(),
    }

def send_and_recv(sock, name, packet):
    print(f"\n>>> {name} TX: {packet.hex()}")
    sock.sendto(packet, SERVER)
    data, addr = sock.recvfrom(2048)
    print(f"<<< {name} RX: {data.hex()} from {addr}")
    return data

def discover_devices(sock):
    print("\n=== DISCOVERY MULTI-DEVICE ===")
    sock.sendto(pkt_discovery(), SERVER)

    end = time.time() + DISCOVERY_WAIT_SEC
    devices = []
    seen_raw = set()

    while time.time() < end:
        try:
            data, addr = sock.recvfrom(2048)
            h = data.hex()
            if h in seen_raw:
                continue
            seen_raw.add(h)

            info = parse_discovery_response(data)
            if info:
                devices.append(info)
                print(f" - Found: serial={info['serial']} ip={info['ip']} model={info['model']} fw={info['fw']} ports={info['ports']} id=0x{info['model_id']:04X}")
            else:
                print(" - Received non-parseable discovery response:", h)
        except socket.timeout:
            pass

    print(f"\nTrovati {len(devices)} device via discovery.\n")
    return devices

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    devices = discover_devices(sock)
    if not devices:
        print("!!! Nessun device trovato. Controlla server/handler multi-device.")
        sock.close()
        return

    # Test ONLINE: heartbeat + status per ogni indice
    print("=== TEST ONLINE (HEARTBEAT + STATUS) ===")
    for idx, dev in enumerate(devices):
        send_and_recv(sock, f"HEARTBEAT idx={idx}", pkt_heartbeat(idx))
        data = send_and_recv(sock, f"STATUS idx={idx} (atteso ONLINE)", pkt_status(idx))
        st = parse_status_response(data)
        print(f"    STATUS idx={idx}: online={st.get('online')} temp={st.get('temp_c')} ports={st.get('ports')} mask=0x{st.get('mask',0):02X}")

    # Attesa per andare OFFLINE (nessun heartbeat)
    print(f"\n--- Attendo {OFFLINE_WAIT_SEC}s per forzare OFFLINE (senza heartbeat) ---")
    time.sleep(OFFLINE_WAIT_SEC)

    print("\n=== TEST OFFLINE (STATUS senza heartbeat) ===")
    for idx, dev in enumerate(devices):
        data = send_and_recv(sock, f"STATUS idx={idx} (atteso OFFLINE)", pkt_status(idx))
        st = parse_status_response(data)
        print(f"    STATUS idx={idx}: online={st.get('online')} temp={st.get('temp_c')} ports={st.get('ports')} mask=0x{st.get('mask',0):02X}")

    sock.close()
    print("\n>>> TEST 6B COMPLETATO")

if __name__ == "__main__":
    main()
