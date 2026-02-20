from dataclasses import dataclass
from typing import Optional

HEADER = b"\x55\xAA"

# Frame fissi visti nello sniff (questa famiglia specifica)
FIXED_FRAME_LEN = 21

@dataclass
class Frame55AA:
    raw: bytes

def try_extract_frame(buffer: bytearray) -> Optional[Frame55AA]:
    # trova header
    idx = buffer.find(HEADER)
    if idx < 0:
        if len(buffer) > 4096:
            del buffer[:-2]
        return None

    if idx > 0:
        del buffer[:idx]

    # --- MODE 1: euristica len(2) BE dopo header ---
    if len(buffer) >= 6:
        length = int.from_bytes(buffer[2:4], "big")
        total = 2 + 2 + length + 2
        # sanity
        if 0 <= length <= 8192 and len(buffer) >= total:
            raw = bytes(buffer[:total])
            del buffer[:total]
            return Frame55AA(raw=raw)

    # --- MODE 2: frame fisso 21 byte (famiglia 55aa 00xx fe .... crc2) ---
    if len(buffer) >= FIXED_FRAME_LEN:
        # firma: 55 aa | 00 ?? | fe ...
        # (byte 2 spesso 0x00, byte 4 spesso 0xFE negli esempi)
        if buffer[2] == 0x00 and buffer[4] == 0xFE:
            raw = bytes(buffer[:FIXED_FRAME_LEN])
            del buffer[:FIXED_FRAME_LEN]
            return Frame55AA(raw=raw)

    return None
