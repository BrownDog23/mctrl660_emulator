def decode_fe_21(frame: bytes):
    # frame deve essere lungo 21
    if len(frame) != 21 or frame[0:2] != b"\x55\xAA":
        return None
    if frame[4] != 0xFE:
        return None

    addr = int.from_bytes(frame[2:4], "big")     # 0x0085 ecc
    param = int.from_bytes(frame[6:8], "big")    # 0x0104 / 0x0105
    value = frame[18]                            # valore 0..255
    crc = int.from_bytes(frame[19:21], "big")    # ultimi 2 byte

    side = "LEFT" if param == 0x0104 else ("RIGHT" if param == 0x0105 else f"PARAM_0x{param:04X}")

    return {
        "addr": addr,
        "param": param,
        "side": side,
        "value": value,
        "crc": crc
    }
