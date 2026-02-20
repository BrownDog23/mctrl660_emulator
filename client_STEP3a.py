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

discovery_packet  = b"\xAA\x55\x01\x00\x00\x00"
heartbeat_packet  = b"\xAA\x55\x02\x00\x04\x00\x00\x00\x00"
status_packet     = b"\xAA\x55\x03\x00\x04\x00\x00\x00\x00"

# 1) Online iniziale (heartbeat)
send_and_receive("DISCOVERY", discovery_packet)
send_and_receive("HEARTBEAT", heartbeat_packet)

# 2) Aspetta oltre timeout per andare offline
print("\n--- Attendo 7s per forzare OFFLINE ---")
time.sleep(7)

# 3) Chiedi status -> deve risultare OFFLINE (ultimo byte payload = 00)
send_and_receive("STATUS (atteso OFFLINE)", status_packet)

# 4) Invia heartbeat -> deve tornare ONLINE e loggare OFFLINE -> ONLINE sul server
send_and_receive("HEARTBEAT (atteso ONLINE)", heartbeat_packet)

# 5) Chiedi status -> deve risultare ONLINE (ultimo byte payload = 01)
send_and_receive("STATUS (atteso ONLINE)", status_packet)

sock.close()
print("\n>>> TEST STEP 3A COMPLETATO")
