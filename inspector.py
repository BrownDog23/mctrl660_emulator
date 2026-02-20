def inspect_packet(hex_string):
    data = bytes.fromhex(hex_string)
    print("LEN:", len(data))
    for i, b in enumerate(data):
        print(f"{i:02d}: {b:02X}")
