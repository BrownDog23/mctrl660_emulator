import socket
import time

PORT = 5200
DISCOVERY = b"\xAA\x55\x01\x00\x00\x00"

def parse(data: bytes):
    length = int.from_bytes(data[3:5], "big")
    payload = data[5:5+length]
    model = payload[0:16].split(b"\x00",1)[0].decode()
    fw = payload[16:24].split(b"\x00",1)[0].decode()
    ports = payload[24]
    model_id = int.from_bytes(payload[25:27],"big")

    # v2 fields
    serial_len = 20
    serial = payload[27:27+serial_len].split(b"\x00",1)[0].decode()
    ipb = payload[27+serial_len:27+serial_len+4]
    ip = ".".join(str(x) for x in ipb)

    return f"{serial} | {ip} | {model} {fw} ports={ports} id=0x{model_id:04X}"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.2)

sock.sendto(DISCOVERY, ("127.0.0.1", PORT))
print("DISCOVERY inviato, attendo risposte...")

seen = []
end = time.time() + 1.0
while time.time() < end:
    try:
        data, addr = sock.recvfrom(2048)
        s = parse(data)
        if s not in seen:
            seen.append(s)
            print(" -", s, "from", addr)
    except socket.timeout:
        pass

print("\nTrovati", len(seen), "device.")
sock.close()
