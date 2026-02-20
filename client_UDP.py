import socket
import time

# --- CONFIGURAZIONE SERVER ---
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5200
server = (SERVER_IP, SERVER_PORT)

# --- CREAZIONE SOCKET UDP ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)  # timeout di 2 secondi per evitare blocchi

# --- FUNZIONE DI INVIO E RICEZIONE ---
def send_and_receive(name, packet):
    print(f"\n>>> INVIO {name}: {packet.hex()}")
    sock.sendto(packet, server)
    try:
        data, addr = sock.recvfrom(1024)
        print(f"<<< RISPOSTA {name}: {data.hex()} da {addr}")
    except socket.timeout:
        print(f"!!! Nessuna risposta per {name}")

# --- PACCHETTI MINIMI VALIDI ---
# DISCOVERY
discovery_packet = b"\xAA\x55\x01\x00\x00\x00"          # CMD 0x01, lunghezza 0

# HEARTBEAT
heartbeat_packet = b"\xAA\x55\x02\x00\x04\x00\x00\x00\x00"  # CMD 0x02, lunghezza=4, payload 4 byte zero

# STATUS
status_packet = b"\xAA\x55\x03\x00\x04\x00\x00\x00\x00"     # CMD 0x03, lunghezza=4, payload 4 byte zero

# --- INVIO PACCHETTI ---
send_and_receive("DISCOVERY", discovery_packet)
time.sleep(1)
send_and_receive("HEARTBEAT", heartbeat_packet)
time.sleep(1)
send_and_receive("STATUS", status_packet)

sock.close()
print("\n>>> TEST COMPLETATO")
