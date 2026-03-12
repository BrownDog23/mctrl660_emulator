#!/usr/bin/env python3
import socket
import sys
import time

LISTEN_PORT = 3800
MCAST_GRP = "224.224.125.119"      # gruppo visto in IGMP
BCAST_SUBNET = "192.168.0.255"     # broadcast di subnet
BCAST_GLOBAL = "255.255.255.255"   # broadcast globale (quello che sta usando NovaLCT)
REPLY = b"rpProMI:App,0161"

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Consigliato su Linux per poter riavviare senza "Address already in use"
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Necessario per poter trasmettere broadcast
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # IMPORTANTE: ricezione broadcast -> bind su 0.0.0.0
    s.bind(("0.0.0.0", LISTEN_PORT))

    print(f"[UDP:{LISTEN_PORT}] Listening on 0.0.0.0:{LISTEN_PORT}")
    sys.stdout.flush()

    while True:
        data, addr = s.recvfrom(2048)

        # NovaLCT manda: b"rqProMI:" (8 bytes)
        if data != b"rqProMI:":
            # per debug minimale:
            # print(f"[UDP:{LISTEN_PORT}] Ignored from {addr} len={len(data)}")
            continue

        print(f"[UDP:{LISTEN_PORT}] RX rqProMI from {addr} -> replying")
        sys.stdout.flush()

        # 1) UNICAST diretto al sender (spesso il più efficace)
        try:
            s.sendto(REPLY, (addr[0], LISTEN_PORT))
            print(f"[UDP:{LISTEN_PORT}] TX UNICAST -> {(addr[0], LISTEN_PORT)} {REPLY!r}")
        except Exception as e:
            print(f"[UDP:{LISTEN_PORT}] TX UNICAST error: {e}")

        # 2) Broadcast subnet
        try:
            s.sendto(REPLY, (BCAST_SUBNET, LISTEN_PORT))
            print(f"[UDP:{LISTEN_PORT}] TX BCAST(subnet) -> {(BCAST_SUBNET, LISTEN_PORT)} {REPLY!r}")
        except Exception as e:
            print(f"[UDP:{LISTEN_PORT}] TX BCAST(subnet) error: {e}")

        # 3) Broadcast globale (per simmetria col dst di NovaLCT)
        try:
            s.sendto(REPLY, (BCAST_GLOBAL, LISTEN_PORT))
            print(f"[UDP:{LISTEN_PORT}] TX BCAST(global) -> {(BCAST_GLOBAL, LISTEN_PORT)} {REPLY!r}")
        except Exception as e:
            print(f"[UDP:{LISTEN_PORT}] TX BCAST(global) error: {e}")

        # 4) Multicast (non costa nulla tenerlo)
        try:
            s.sendto(REPLY, (MCAST_GRP, LISTEN_PORT))
            print(f"[UDP:{LISTEN_PORT}] TX MCAST -> {(MCAST_GRP, LISTEN_PORT)} {REPLY!r}")
        except Exception as e:
            print(f"[UDP:{LISTEN_PORT}] TX MCAST error: {e}")

        sys.stdout.flush()
        time.sleep(0.05)

if __name__ == "__main__":
    main()