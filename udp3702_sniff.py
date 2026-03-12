import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", 3702))
print("[UDP:3702] Listening on 0.0.0.0:3702")

while True:
    data, addr = s.recvfrom(65535)
    print(f"[UDP:3702] From {addr} {len(data)} bytes")
    # stampa i primi byte per capire se è SOAP/XML
    print(data[:200])