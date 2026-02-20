import socket
import time

SERVER = ("127.0.0.1", 5200)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

def send_and_receive(name, packet):
    print(f"\n>>> INVIO {name}: {packet.hex()}")
    sock.sendto(packet, SERVER)
    data, addr = sock.recvfrom(1024)
    print(f"<<< RISPOSTA {name}: {data.hex()} da {addr}")
    return data

discovery_packet = b"\xAA\x55\x01\x00\x00\x00"
heartbeat_packet = b"\xAA\x55\x02\x00\x04\x00\x00\x00\x00"
status_packet    = b"\xAA\x55\x03\x00\x04\x00\x00\x00\x00"

# 1) Discovery (inizia grace)
send_and_receive("DISCOVERY", discovery_packet)

# 2) Heartbeat durante grace (dovrebbe restare online, nessuna transizione)
time.sleep(2)
send_and_receive("HEARTBEAT (durante grace)", heartbeat_packet)

# 3) Aspetta oltre la scadenza grace (es. 12s) MA entro timeout heartbeat (mandiamo un altro heartbeat prima)
print("\n--- Attendo 9s (grace sta per scadere) ---")
time.sleep(9)

# heartbeat per restare online anche dopo grace
send_and_receive("HEARTBEAT (prima che scada grace)", heartbeat_packet)

print("\n--- Attendo 4s (grace scaduto, ma heartbeat recente) ---")
time.sleep(4)

# 4) Status deve risultare ONLINE
send_and_receive("STATUS (atteso ONLINE)", status_packet)

sock.close()
print("\n>>> TEST STEP 4 COMPLETATO")
