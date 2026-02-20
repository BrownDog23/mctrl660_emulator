class NovaPacket:
    HEADER = b"\xAA\x55"

    DISCOVERY_CMD = 0x01
    HEARTBEAT_CMD = 0x02
    STATUS_CMD    = 0x03

    def __init__(self, raw: bytes):
        self.raw = raw
        self.valid = False

        if len(raw) < 6:
            return

        self.header = raw[0:2]
        self.cmd = raw[2]
        self.length = int.from_bytes(raw[3:5], "big")
        self.payload = raw[5:5 + self.length]
        self.crc = raw[5 + self.length] if len(raw) > 5 + self.length else None

        if self.header != self.HEADER:
            return

        if len(self.payload) != self.length:
            return

        self.valid = True

    def is_discovery(self):
        return self.valid and self.cmd == self.DISCOVERY_CMD

    def is_heartbeat(self):
        return self.valid and self.cmd == self.HEARTBEAT_CMD

    def is_status(self):
        return self.valid and self.cmd == self.STATUS_CMD

    def __str__(self):
        return (
            f"Header={self.header.hex()} "
            f"CMD={self.cmd:02X} "
            f"LEN={self.length} "
            f"PAYLOAD_LEN={len(self.payload)}"
        )
