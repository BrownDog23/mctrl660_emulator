from device_state import DeviceState
from settings import EMULATOR_IP


class DeviceRegistry:
    def __init__(self):
        self.devices = [
            DeviceState(serial="FAKE-MCTRL660-001", ip=EMULATOR_IP),
        ]

    def all(self):
        return self.devices

    def get_by_index(self, idx: int) -> DeviceState:
        if idx < 0 or idx >= len(self.devices):
            return self.devices[0]
        return self.devices[idx]

    def get_free_device_index(self):
        for idx, dev in enumerate(self.devices):
            if not hasattr(dev, "assigned"):
                dev.assigned = False
            if not dev.assigned:
                return idx
        return None

    def assign(self, idx):
        self.devices[idx].assigned = True