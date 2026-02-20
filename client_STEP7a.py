import socket
import time

SERVER = ("127.0.0.1", 5200)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

DISCOVERY = b"\xAA\x55\x01\x00\x00\x00"
HEARTBEAT = b"\xAA\x55\x02\x00\x00\x00"
STATUS    = b"\xAA\x55\x03\x00\x00\x00"

def send(name, pkt):
    print(f"\n>>> {name} TX: {pkt.hex()}")
    sock.sendto(pkt, SERVER)
    data, addr = sock.recvfrom(2048)
    print(f"<<< {name} RX: {data.hex()} from {addr}")
    return data

# Discovery (opzionale, ma utile)
send("DISCOVERY", DISCOVERY)

# Heartbeat + status ripetuti
for i in range(3):
    send("HEARTBEAT", HEARTBEAT)
    time.sleep(0.2)
    send("STATUS", STATUS)
    time.sleep(1.0)

sock.close()
print("\n>>> TEST 7A COMPLETATO")
