import time
import random

HEARTBEAT_TIMEOUT_SEC = 5
GRACE_PERIOD_SEC = 10
DISCOVERY_SERIAL_LEN = 20

class DeviceState:
    def __init__(self, *, serial="FAKE-MCTRL660-001", ip="192.168.0.100"):
        self.model = "MCTRL660"
        self.model_id = 0x660
        self.firmware = "V5.0.0"
        self.ports = 6
        self.serial = serial
        self.ip = ip

        self.last_heartbeat = None
        self.online = True
        self._prev_online = True
        self.discovery_seen_at = None

    def update_online_state(self):
        now = time.time()

        if self.in_grace_period():
            self.online = True
        elif self.last_heartbeat is not None and (now - self.last_heartbeat) <= HEARTBEAT_TIMEOUT_SEC:
            self.online = True
        else:
            self.online = False

        changed = (self.online != self._prev_online)
        old = self._prev_online
        new = self.online
        self._prev_online = self.online
        return changed, old, new



    def build_discovery_payload(self):
        payload = bytearray()
        payload += self.model.encode("ascii").ljust(16, b"\x00")
        payload += self.firmware.encode("ascii").ljust(8, b"\x00")
        payload += self.ports.to_bytes(1, "big")
        payload += self.model_id.to_bytes(2, "big")
        return bytes(payload)

    def build_heartbeat_payload(self):
        uptime = int(time.time()) & 0xFFFFFFFF
        return uptime.to_bytes(4, "big")

    def build_status_payload(self):
        temperature = random.randint(35, 55)
        ports_mask = (1 << self.ports) - 1
        online_flag = 1 if self.online else 0

        payload = bytearray()
        payload += temperature.to_bytes(1, "big")
        payload += self.ports.to_bytes(1, "big")
        payload += ports_mask.to_bytes(1, "big")
        payload += online_flag.to_bytes(1, "big")
        return bytes(payload)
        
    def mark_discovery_seen(self):
        self.discovery_seen_at = time.time()

    def in_grace_period(self):
        if self.discovery_seen_at is None:
            return False
        return (time.time() - self.discovery_seen_at) <= GRACE_PERIOD_SEC
        
    def mark_heartbeat_seen(self):
        self.last_heartbeat = time.time()
        
    def build_discovery_payload_v2(self):
        payload = bytearray(self.build_discovery_payload())  # 27 byte invariati

        # seriale a lunghezza fissa (tronca + pad)
        serial_bytes = self.serial.encode("ascii")[:DISCOVERY_SERIAL_LEN].ljust(DISCOVERY_SERIAL_LEN, b"\x00")
        payload += serial_bytes

        # IP in 4 byte
        ip_parts = [int(x) for x in self.ip.split(".")]
        payload += bytes(ip_parts)

        return bytes(payload)


