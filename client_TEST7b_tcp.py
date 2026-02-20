import socket

SERVER = ("127.0.0.1", 5200)

# frame finto: 55 AA + len(2) + payload(len) + crc(2)
payload = b"\x01\x02\x03\x04\x05"
length = len(payload).to_bytes(2, "big")
crc = b"\x00\x00"

frame = b"\x55\xAA" + length + payload + crc

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(SERVER)
print("Connected, sending:", frame.hex())
s.sendall(frame)
s.close()
print("Done.")
