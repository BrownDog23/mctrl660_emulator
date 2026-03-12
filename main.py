import socket

HOST = "0.0.0.0"
PORT = 5200

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print("Listening on 5200...")

    conn, addr = s.accept()
    print("Connection from", addr)

    while True:
        data = conn.recv(4096)
        if not data:
            print("Client closed")
            break
        print("RX:", data.hex())