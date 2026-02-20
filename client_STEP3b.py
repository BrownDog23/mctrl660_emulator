import socket
import time

SERVER = ("127.0.0.1", 5200)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

def send_and_receive(name, packet):
    print(f"\n>>> INVIO {name}: {packet.hex()}")
    sock.sendto(packet, SERVER)
    try:
        data, addr = sock.recvfrom(1024)
        print(f"<<< RISPOSTA {name}: {data.hex()} da {addr}")
        return data
    except socket.timeout:
        print(f"!!! Nessuna risposta per {name}")
        return None

# Pacchetti
discovery_packet = b"\xAA\x55\x01\x00\x00\x00"
status_packet    = b"\xAA\x55\x03\x00\x04\x00\x00\x00\x00"

# --- TEST 1: grace period attivo (ONLINE atteso) ---
send_and_receive("DISCOVERY", discovery_packet)
time.sleep(1)
send_and_receive("STATUS (atteso ONLINE - grace attivo)", status_packet)

# --- TEST 2: grace period scaduto (OFFLINE atteso) ---
print("\n--- Attendo 12s per far scadere il grace period (senza heartbeat) ---")
time.sleep(12)
send_and_receive("STATUS (atteso OFFLINE - grace scaduto)", status_packet)

sock.close()
print("\n>>> TEST STEP 3B COMPLETATO")
