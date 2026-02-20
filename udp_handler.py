import time
from protocol import NovaPacket
from logger import log_packet, log_text
from device_registry import DeviceRegistry

HEADER = b"\xAA\x55"

registry = DeviceRegistry()
client_map = {}  # (ip,port) -> device_index


def build_response(cmd: int, payload: bytes) -> bytes:
    pkt = bytearray()
    pkt += HEADER
    pkt += cmd.to_bytes(1, "big")
    pkt += len(payload).to_bytes(2, "big")
    pkt += payload
    pkt += b"\x00"  # CRC placeholder
    return bytes(pkt)


def _get_device_for_client(addr):
    # addr è una tupla (ip,port)
    if addr in client_map:
        return registry.get_by_index(client_map[addr])

    free_idx = registry.get_free_device_index()
    if free_idx is None:
        free_idx = 0  # fallback

    registry.assign(free_idx)
    client_map[addr] = free_idx

    dev = registry.get_by_index(free_idx)
    log_text(f"Client {addr} assigned to device idx={free_idx} [{dev.serial}]")
    return dev


def handle_udp(data: bytes, addr):
    log_packet(f"RX from {addr}", data)

    pkt = NovaPacket(data)
    if not pkt.valid:
        log_text("Invalid packet -> ignored")
        return None

    print(pkt)  # stampa Header/CMD/LEN ecc.

    # DISCOVERY -> risponde con TUTTI i device
    if pkt.is_discovery():
        responses = []
        for dev in registry.all():
            dev.mark_discovery_seen()
            dev.update_online_state()
            payload = dev.build_discovery_payload_v2()
            resp = build_response(0x81, payload)
            responses.append(resp)

        log_text(f"TX DISCOVERY: {len(responses)} devices")
        return responses

    # HEARTBEAT -> device assegnato a quel client
    if pkt.is_heartbeat():
        dev = _get_device_for_client(addr)

        dev.mark_heartbeat_seen()
        changed, old, new = dev.update_online_state()
        if changed:
            log_text(f"[{dev.serial}] Device state changed: {'ONLINE' if old else 'OFFLINE'} -> {'ONLINE' if new else 'OFFLINE'}")

        payload = dev.build_heartbeat_payload()
        resp = build_response(0x82, payload)
        log_packet(f"TX HEARTBEAT [{dev.serial}]", resp)
        return resp

    # STATUS -> device assegnato a quel client
    if pkt.is_status():
        dev = _get_device_for_client(addr)

        changed, old, new = dev.update_online_state()
        if changed:
            log_text(f"[{dev.serial}] Device state changed: {'ONLINE' if old else 'OFFLINE'} -> {'ONLINE' if new else 'OFFLINE'}")

        payload = dev.build_status_payload()
        resp = build_response(0x83, payload)
        log_packet(f"TX STATUS [{dev.serial}]", resp)
        return resp

    # CMD sconosciuto
    log_text(f"Unknown CMD=0x{pkt.cmd:02X}")
    return build_response(0xFF, b"\x00")
