import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

packet = b"\xAA\x55\x01\x00\x00\x00"
sock.sendto(packet, ("127.0.0.1", 5200))

data, addr = sock.recvfrom(1024)
print("RISPOSTA:", data.hex(), addr)

sock.close()
