import socket

SERVER = ("127.0.0.1", 5200)

LEFT  = bytes.fromhex("55aa0085fe000104ffff010001000002010000e058")
RIGHT = bytes.fromhex("55aa0086fe000105ffff010001000002010000e258")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(SERVER)
print("Connected.")

print("Sending LEFT :", LEFT.hex())
s.sendall(LEFT)

print("Sending RIGHT:", RIGHT.hex())
s.sendall(RIGHT)

s.close()
print("Done.")
