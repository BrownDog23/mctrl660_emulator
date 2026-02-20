from device_state import DeviceState

class DeviceRegistry:
    def __init__(self):
        # Crea qui quanti device vuoi
        self.devices = [
        #   DeviceState(serial="FAKE-MCTRL660-001", ip="192.168.0.100"),
        #   DeviceState(serial="FAKE-MCTRL660-002", ip="192.168.0.101"),
        #   DeviceState(serial="FAKE-MCTRL660-003", ip="192.168.0.102"),
            DeviceState(serial="FAKE-MCTRL660-001", ip="192.168.56.1"),
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

    def get_by_index(self, idx):
        return self.devices[idx]
