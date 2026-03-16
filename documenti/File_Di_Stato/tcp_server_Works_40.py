# VERSION tcp_server.py: Works_40

import socket
import argparse
from collections import defaultdict

MAX_READ_PAYLOAD = 4096

IDENTITY_REGS = {0x00000002, 0x00000006, 0x00000016, 0x14000000}
KEY_SCREEN_REGS = {0x02000000, 0x02000100, 0x02020020, 0x08000000}

RCFG_REGS = {
    0x02100000,
    0x05000000,
    0x05065000,
    0x05066000,
}

VALIDATION_REGS = {
    0x0200000B,
    0x02000022,
    0x02000023,
    0x0200009D,
    0x02200117,
    0x03100109,
}

REGISTER_MAP = {
    (0x00000002, 2): b"\x01\x11",
    (0x00000006, 1): b"\x01",
    (0x00000016, 8): b"M660\x00\x01\x00\x00",
    (0x14000000, 0x58): bytes([0x4E, 0x53, 0x54, 0x52] + [i & 0xFF for i in range(4, 0x58)]),
}

MEM = {}
CTRL_BLOCKS = {}

COMMIT_SEEN = False
SCREEN_BLOCKS_READY = False

# Works_40: experiment on first two cabinets only
FIRST2_BUILDER_MODE = "baseline"  # baseline | mirror_minimal | zero_tail

ROUTING_WRITES = []
SCREEN_WRITES = []
CABINETS = []

RCFG_PRESENT = {}         # semantic "configured and coherent"
RCFG_SAVE_MARK = {}       # raw 0x05066000 save marker
RCFG_POSTSAVE_READS = {}  # debug counter
RCFG_ACCEPTED = {}        # sticky acceptance state (never regress within session)
SPECIAL_BRANCH_WRITES = []

CONNECTION_SEQ = 0
ACTIVE_CONN_ID = 0
SESSION_STATE = defaultdict(lambda: {
    "route_writes": 0,
    "commits": 0,
    "validation_reads": 0,
    "screen_reads": 0,
    "rcfg_reads": 0,
    "rcfg_writes": 0,
    "special_writes": 0,
    "first_route_regs": [],
    "first_validation": [],
    "first_screen_reads": [],
    "early_abort_suspected": False,
})


def session_state():
    return SESSION_STATE[ACTIVE_CONN_ID]


def session_note(kind: str, payload: str):
    st = session_state()
    bucket = None
    if kind == "route":
        bucket = st["first_route_regs"]
    elif kind == "validation":
        bucket = st["first_validation"]
    elif kind == "screen":
        bucket = st["first_screen_reads"]
    if bucket is not None and len(bucket) < 12:
        bucket.append(payload)


def dump_session_summary(conn_id: int, reason: str):
    st = SESSION_STATE.get(conn_id)
    if not st:
        return
    print(f"[EMU] ---- SESSION {conn_id} SUMMARY ({reason}) ----")
    print(f"[EMU] first2_builder={FIRST2_BUILDER_MODE}")
    print(
        f"[EMU] route_writes={st['route_writes']} commits={st['commits']} "
        f"validation_reads={st['validation_reads']} screen_reads={st['screen_reads']} "
        f"rcfg_reads={st['rcfg_reads']} rcfg_writes={st['rcfg_writes']} "
        f"special_writes={st['special_writes']} early_abort_suspected={1 if st['early_abort_suspected'] else 0}"
    )
    if st['first_route_regs']:
        print(f"[EMU] first_route_regs={' | '.join(st['first_route_regs'])}")
    if st['first_validation']:
        print(f"[EMU] first_validation={' | '.join(st['first_validation'])}")
    if st['first_screen_reads']:
        print(f"[EMU] first_screen_reads={' | '.join(st['first_screen_reads'])}")


def checksum_5555(frame_wo_checksum: bytes) -> int:
    return (sum(frame_wo_checksum[2:]) + 0x5555) & 0xFFFF


def parse_req(req: bytes):
    return {
        "serial": req[3],
        "src": req[4],
        "dst": req[5],
        "dev": req[6],
        "port": req[7],
        "rcvIndex": int.from_bytes(req[8:10], "little"),
        "code": req[10],
        "reserved": req[11],
        "reg": int.from_bytes(req[12:16], "little"),
        "n": int.from_bytes(req[16:18], "little"),
        "write_data": req[18:-2] if len(req) > 20 else b"",
    }


def feed_parser(buffer: bytearray):
    while True:
        if len(buffer) < 2:
            return

        if not (buffer[0] == 0x55 and buffer[1] == 0xAA):
            del buffer[0]
            continue

        if len(buffer) < 20:
            return

        code = buffer[10]
        n = int.from_bytes(buffer[16:18], "little")
        total = 20 + (n if code == 0x01 else 0)

        if len(buffer) < total:
            return

        frame = bytes(buffer[:total])
        del buffer[:total]
        yield frame


def mem_key(dev, port, rcvIndex, dst):
    return (dev, port, rcvIndex, dst)


def mem_write(dev, port, rcvIndex, dst, reg, data):
    key = mem_key(dev, port, rcvIndex, dst)
    d = MEM.setdefault(key, {})
    for i, b in enumerate(data):
        d[reg + i] = b


def mem_read_slice(dev, port, rcvIndex, dst, reg, n):
    key = mem_key(dev, port, rcvIndex, dst)
    d = MEM.get(key, {})
    return bytes(d.get(reg + i, 0) for i in range(n))


def mem_overlay(dev, port, rcvIndex, dst, reg, data):
    key = mem_key(dev, port, rcvIndex, dst)
    d = MEM.get(key)
    if not d:
        return data

    for i in range(len(data)):
        addr = reg + i
        if addr in d:
            data[i] = d[addr]

    return data


def ctrl_block_key(dev, port, reg):
    return (dev, port, reg)


def ctrl_block_write(dev, port, reg, data: bytes):
    CTRL_BLOCKS[ctrl_block_key(dev, port, reg)] = bytes(data)


def ctrl_block_read(dev, port, reg, n):
    data = CTRL_BLOCKS.get(ctrl_block_key(dev, port, reg))
    if data is None:
        return None
    if len(data) >= n:
        return data[:n]
    return data + (b"\x00" * (n - len(data)))


def hex_preview(data: bytes, max_len: int = 48) -> str:
    h = data.hex()
    if len(h) <= max_len * 2:
        return h
    return h[: max_len * 2] + "..."


def hex_full(data: bytes) -> str:
    return data.hex()


def dump_bytes_by8(label: str, data: bytes, limit: int = 64):
    chunked = []
    for i in range(0, min(len(data), limit), 8):
        chunk = data[i:i+8]
        chunked.append(f"{i:02X}:{chunk.hex()}")
    print(f"[EMU] {label} {' | '.join(chunked)}")


def first2_builder_active():
    return FIRST2_BUILDER_MODE != "baseline"


def is_sender_identity_reg(reg, n):
    return (
        (reg == 0x00000002 and n == 2) or
        (reg == 0x00000006 and n == 1) or
        (reg == 0x00000016 and n == 8) or
        (reg == 0x14000000 and n == 0x58)
    )


def read_default(dst, reg, n):
    if dst == 0x00:
        if reg == 0x00000002 and n == 2:
            return b"\x01\x11"
        if reg == 0x00000006 and n == 1:
            return b"\x01"
        if reg == 0x00000016 and n == 8:
            return b"M660\x00\x01\x00\x00"
        if reg == 0x14000000 and n == 0x58:
            return bytes([0x4E, 0x53, 0x54, 0x52] + [i & 0xFF for i in range(4, 0x58)])

        m = REGISTER_MAP.get((reg, n))
        if m is not None:
            return m

    return b"\x00" * n


def parse_route_record(raw: bytes):
    if len(raw) != 6:
        return None

    return {
        "raw": bytes(raw),
        "group": raw[0],
        "a": raw[1],
        "b": raw[2],
        "c": raw[3],
        "x": raw[4],
        "y": raw[5],
        "word": (raw[4] << 8) | raw[5],
    }


def save_marker_present(dev, port, rcvIndex, dst):
    return mem_key(dev, port, rcvIndex, dst) in RCFG_SAVE_MARK


def postsave_read_count(dev, port, rcvIndex, dst):
    return int(RCFG_POSTSAVE_READS.get(mem_key(dev, port, rcvIndex, dst), 0))


def bump_postsave_read(dev, port, rcvIndex, dst):
    key = mem_key(dev, port, rcvIndex, dst)
    RCFG_POSTSAVE_READS[key] = postsave_read_count(dev, port, rcvIndex, dst) + 1


def rcfg_accepted(dev, port, rcvIndex, dst):
    return bool(RCFG_ACCEPTED.get(mem_key(dev, port, rcvIndex, dst), False))


def mark_rcfg_accepted(dev, port, rcvIndex, dst, reason=""):
    key = mem_key(dev, port, rcvIndex, dst)
    if not RCFG_ACCEPTED.get(key, False):
        RCFG_ACCEPTED[key] = True
        extra = f" reason={reason}" if reason else ""
        print(
            f"[EMU] RCFG ACCEPTED dev={dev:02X} port={port:02X} "
            f"rcv={rcvIndex:04X} dst={dst:02X}{extra}"
        )


def protocol_branch_key(info):
    return info["dev"] == 0x01 and info["port"] == 0xFF and info["rcvIndex"] == 0xFFFF


def branch_seen_after_save(dst):
    for item in reversed(SPECIAL_BRANCH_WRITES):
        if item["dst"] in (dst, 0xFF):
            return True
    return False


def build_runtime_02100000(dev, port, rcvIndex, dst):
    count = len(CABINETS) & 0xFF
    return bytes([
        0x53, 0x53, 0x50, 0x45,   # SSPE
        0x01,                     # version
        dev & 0xFF,
        port & 0xFF,
        dst & 0xFF,
        rcvIndex & 0xFF,
        (rcvIndex >> 8) & 0xFF,
        count,
        0x01,                     # configured
        0x01 if COMMIT_SEEN else 0x00,
        0x00,
        0x01,
    ])


def build_summary_05065000(dev, port, rcvIndex, dst):
    count = len(CABINETS)
    return bytes([
        0x53,                     # S
        0x50,                     # P
        0x01,                     # version
        0x01,                     # configured
        dev & 0xFF,
        port & 0xFF,
        count & 0xFF,
        (count >> 8) & 0xFF,
        dst & 0xFF,
        0x01,
    ])


def rcfg_blocks_nonzero(dev, port, rcvIndex, dst):
    a = mem_read_slice(dev, port, rcvIndex, dst, 0x05000000, 4)
    b = mem_read_slice(dev, port, rcvIndex, dst, 0x02100000, 15)
    c = mem_read_slice(dev, port, rcvIndex, dst, 0x05065000, 10)
    return any(a) and any(b) and any(c)


def topology_ready(dev, port, rcvIndex, dst):
    return len(CABINETS) > 0 and COMMIT_SEEN


def rcfg_configured(dev, port, rcvIndex, dst):
    """
    Works_40 rule:
    configured only if:
      - semantic present flag exists
      - save marker exists
      - topology exists and has been committed
      - derived config blocks are non-zero
    """
    key = mem_key(dev, port, rcvIndex, dst)
    semantic = bool(RCFG_PRESENT.get(key, False))
    return semantic and save_marker_present(dev, port, rcvIndex, dst) and topology_ready(dev, port, rcvIndex, dst) and rcfg_blocks_nonzero(dev, port, rcvIndex, dst)


def rcfg_acceptance_ready(dev, port, rcvIndex, dst):
    if rcfg_accepted(dev, port, rcvIndex, dst):
        return True
    if not rcfg_configured(dev, port, rcvIndex, dst):
        return False
    if postsave_read_count(dev, port, rcvIndex, dst) >= 1:
        return True
    if branch_seen_after_save(dst):
        return True
    return False


def refresh_rcfg_semantic_state():
    """
    Re-evaluate semantic configured flag after topology changes.
    """
    for key in list(RCFG_PRESENT.keys()):
        dev, port, rcv, dst = key
        RCFG_PRESENT[key] = save_marker_present(dev, port, rcv, dst) and topology_ready(dev, port, rcv, dst) and rcfg_blocks_nonzero(dev, port, rcv, dst)


def seed_rcfg_blocks(dev, port, rcvIndex, dst, save_blob=None):
    """
    Seed coherent blocks, but do NOT automatically expose configured=1
    until topology + save marker + blocks all align.
    """
    mem_write(dev, port, rcvIndex, dst, 0x05000000, b"\x01\x00\x00\x00")
    mem_write(dev, port, rcvIndex, dst, 0x02100000, build_runtime_02100000(dev, port, rcvIndex, dst))
    mem_write(dev, port, rcvIndex, dst, 0x05065000, build_summary_05065000(dev, port, rcvIndex, dst))
    if save_blob is not None:
        mem_write(dev, port, rcvIndex, dst, 0x05066000, save_blob)


def mark_rcfg_saved(dev, port, rcvIndex, dst, save_blob):
    key = mem_key(dev, port, rcvIndex, dst)
    RCFG_SAVE_MARK[key] = bytes(save_blob)
    RCFG_POSTSAVE_READS[key] = 0

    seed_rcfg_blocks(dev, port, rcvIndex, dst, save_blob=save_blob)

    # semantic exposure delayed until coherence rule passes
    RCFG_PRESENT[key] = save_marker_present(dev, port, rcvIndex, dst) and topology_ready(dev, port, rcvIndex, dst) and rcfg_blocks_nonzero(dev, port, rcvIndex, dst)


def validation_read(dev, port, rcvIndex, dst, reg, n):
    route_count = len(CABINETS)
    configured = rcfg_configured(dev, port, rcvIndex, dst)
    accepted = rcfg_acceptance_ready(dev, port, rcvIndex, dst)

    if accepted:
        mark_rcfg_accepted(dev, port, rcvIndex, dst, reason="validation")

    print(
        f"[EMU] VALIDATION STATE reg=0x{reg:08X} dst={dst:02X} route_count={route_count} "
        f"commit={1 if COMMIT_SEEN else 0} configured={1 if configured else 0} "
        f"accepted={1 if accepted else 0} save={1 if save_marker_present(dev, port, rcvIndex, dst) else 0} "
        f"postreads={postsave_read_count(dev, port, rcvIndex, dst)}"
    )

    if reg == 0x0200000B and n == 1:
        return bytes([0x01 if route_count > 0 else 0x00])

    if reg == 0x02000022 and n == 1:
        return bytes([route_count & 0xFF])

    if reg == 0x02000023 and n == 1:
        return bytes([(route_count >> 8) & 0xFF])

    if reg == 0x0200009D and n == 1:
        return bytes([0x01 if (COMMIT_SEEN or configured or accepted or rcfg_accepted(dev, port, rcvIndex, dst)) else 0x00])

    if reg == 0x02200117 and n == 1:
        return bytes([0x01 if accepted else 0x00])

    if reg == 0x03100109 and n == 1:
        return b"\x01"

    return None


def read_data(dev, port, rcvIndex, dst, reg, n):
    if reg in KEY_SCREEN_REGS:
        data = ctrl_block_read(dev, port, reg, n)
        if data is not None:
            return data
        return b"\x00" * n

    if reg in VALIDATION_REGS:
        data = validation_read(dev, port, rcvIndex, dst, reg, n)
        if data is not None:
            return data

    key = mem_key(dev, port, rcvIndex, dst)
    if key in MEM:
        direct = mem_read_slice(dev, port, rcvIndex, dst, reg, n)
        if any(b != 0 for b in direct):
            return direct

    base = bytearray(read_default(dst, reg, n))
    base = mem_overlay(dev, port, rcvIndex, dst, reg, base)
    return bytes(base)


def make_ack_base(req, info, ack_code):
    ack = bytearray()
    ack += b"\xAA\x55"
    ack.append(ack_code)
    ack.append(info["serial"])
    ack.append(info["dst"])
    ack.append(info["src"])
    ack.append(info["dev"])
    ack.append(info["port"])
    ack += info["rcvIndex"].to_bytes(2, "little")
    ack.append(info["code"])
    ack.append(0x00)
    ack += info["reg"].to_bytes(4, "little")
    ack += info["n"].to_bytes(2, "little")
    return ack


def finalize_ack(ack):
    cs = checksum_5555(bytes(ack))
    ack += cs.to_bytes(2, "little")
    return bytes(ack)


def rebuild_screen_writes_from_routing():
    global SCREEN_WRITES

    out = []
    for item in ROUTING_WRITES[-128:]:
        parsed = parse_route_record(item["data"])
        if not parsed:
            continue

        out.append({
            "dev": item["dev"],
            "port": item["port"],
            "rcvIndex": item["rcvIndex"],
            "dst": item["dst"],
            **parsed,
        })

    out.sort(key=lambda e: (e["dev"], e["port"], e["rcvIndex"], e["word"], e["raw"]))
    SCREEN_WRITES = out


def rebuild_cabinets_from_screen_writes():
    global CABINETS

    by_port = defaultdict(list)
    for item in SCREEN_WRITES:
        by_port[item["port"]].append(item)

    cabinets = []

    for port in sorted(by_port.keys()):
        port_items = list(by_port[port])

        cascade_items = sorted(port_items, key=lambda e: (e["word"], e["raw"]))
        layout_items = sorted(port_items, key=lambda e: (e["y"], e["x"], e["word"]))

        cascade_pos = {id(item): idx for idx, item in enumerate(cascade_items)}
        layout_pos = {id(item): idx for idx, item in enumerate(layout_items)}

        unique_x = sorted({item["x"] for item in port_items})
        unique_y = sorted({item["y"] for item in port_items})
        x_rank = {v: i for i, v in enumerate(unique_x)}
        y_rank = {v: i for i, v in enumerate(unique_y)}

        for item in port_items:
            cabinets.append({
                "tile_index": layout_pos[id(item)] & 0xFF,
                "sender_port": port & 0xFF,
                "chain_index": item["rcvIndex"] & 0xFF,
                "cascade_order": cascade_pos[id(item)] & 0xFF,
                "layout_x": x_rank[item["x"]] & 0xFF,
                "layout_y": y_rank[item["y"]] & 0xFF,
                "raw_x": item["x"] & 0xFF,
                "raw_y": item["y"] & 0xFF,
                "group": item["group"] & 0xFF,
                "c": item["c"] & 0xFF,
                "route_word": item["word"] & 0xFFFF,
                "dev": item["dev"] & 0xFF,
                "port": item["port"] & 0xFF,
            })

    cabinets.sort(key=lambda c: (c["sender_port"], c["tile_index"], c["cascade_order"], c["route_word"]))
    CABINETS = cabinets


def pack_layout_entry(entry):
    return bytes([
        entry["layout_x"] & 0xFF,
        entry["layout_y"] & 0xFF,
        entry["sender_port"] & 0xFF,
        entry["cascade_order"] & 0xFF,
        entry["tile_index"] & 0xFF,
        entry["group"] & 0xFF,
        entry["c"] & 0xFF,
        0x00,
    ])


def pack_cascade_entry(entry):
    return bytes([
        entry["sender_port"] & 0xFF,
        entry["cascade_order"] & 0xFF,
        entry["chain_index"] & 0xFF,
        entry["tile_index"] & 0xFF,
        entry["raw_x"] & 0xFF,
        entry["raw_y"] & 0xFF,
        (entry["route_word"] >> 8) & 0xFF,
        entry["route_word"] & 0xFF,
    ])


def pack_summary_entry(entry):
    return bytes([
        (entry["route_word"] >> 8) & 0xFF,
        entry["route_word"] & 0xFF,
        entry["cascade_order"] & 0xFF,
        0x01,
    ])


def dump_routing_writes():
    print("[EMU] ---- ROUTING_WRITES ----")
    if not ROUTING_WRITES:
        print("[EMU] (none)")
        return
    for idx, item in enumerate(ROUTING_WRITES):
        print(
            f"[EMU] RAW[{idx:02d}] dev={item['dev']:02X} port={item['port']:02X} "
            f"rcv={item['rcvIndex']:04X} dst={item['dst']:02X} data={item['data'].hex()}"
        )


def dump_screen_writes():
    print("[EMU] ---- SCREEN_WRITES ----")
    if not SCREEN_WRITES:
        print("[EMU] (none)")
        return
    for idx, item in enumerate(SCREEN_WRITES):
        print(
            f"[EMU] ROUTE[{idx:02d}] dev={item['dev']:02X} port={item['port']:02X} "
            f"rcv={item['rcvIndex']:04X} dst={item['dst']:02X} "
            f"group={item['group']:02X} a={item['a']:02X} b={item['b']:02X} c={item['c']:02X} "
            f"x={item['x']:02X} y={item['y']:02X} word=0x{item['word']:04X} raw={item['raw'].hex()}"
        )


def dump_cabinets():
    print("[EMU] ---- CABINETS ----")
    if not CABINETS:
        print("[EMU] (none)")
        return
    for idx, c in enumerate(CABINETS):
        print(
            f"[EMU] CAB[{idx:02d}] tile={c['tile_index']:02X} port={c['sender_port']:02X} "
            f"chain={c['chain_index']:02X} cascade={c['cascade_order']:02X} "
            f"lx={c['layout_x']:02X} ly={c['layout_y']:02X} "
            f"group={c['group']:02X} c={c['c']:02X} route=0x{c['route_word']:04X}"
        )


def dump_topology_model():
    print("[EMU] ---- TOPOLOGY_MODEL ----")
    if not CABINETS:
        print("[EMU] (none)")
        return

    for idx, c in enumerate(CABINETS):
        print(
            f"[EMU] MODEL[{idx:02d}] "
            f"port={c['sender_port']:02X} tile={c['tile_index']:02X} "
            f"cascade={c['cascade_order']:02X} chain={c['chain_index']:02X} "
            f"layout=({c['layout_x']:02X},{c['layout_y']:02X}) "
            f"raw=({c['raw_x']:02X},{c['raw_y']:02X}) "
            f"route=0x{c['route_word']:04X}"
        )


def dump_rcfg_summary():
    print("[EMU] ---- RCFG_STATE ----")
    found = False
    for key in sorted(set(list(MEM.keys()) + list(RCFG_PRESENT.keys()) + list(RCFG_SAVE_MARK.keys()))):
        dev, port, rcv, dst = key
        present = rcfg_configured(dev, port, rcv, dst)
        save = 1 if save_marker_present(dev, port, rcv, dst) else 0
        if not present and not save and not rcfg_blocks_nonzero(dev, port, rcv, dst):
            continue
        found = True
        print(
            f"[EMU] RCFG dev={dev:02X} port={port:02X} rcv={rcv:04X} dst={dst:02X} "
            f"present={1 if present else 0} save={save} "
            f"02100000={hex_preview(mem_read_slice(dev, port, rcv, dst, 0x02100000, 15))} "
            f"05000000={hex_preview(mem_read_slice(dev, port, rcv, dst, 0x05000000, 4))} "
            f"05065000={hex_preview(mem_read_slice(dev, port, rcv, dst, 0x05065000, 10))} "
            f"reads={postsave_read_count(dev, port, rcv, dst)}"
        )
    if not found:
        print("[EMU] (none)")


def build_controller_blocks():
    global SCREEN_BLOCKS_READY

    rebuild_screen_writes_from_routing()
    rebuild_cabinets_from_screen_writes()
    refresh_rcfg_semantic_state()

    print(f"[EMU] Rebuilding controller screen blocks from {len(CABINETS)} cabinet entries")
    print(f"[EMU] FIRST4_BUILDER_MODE={FIRST2_BUILDER_MODE}")
    dump_routing_writes()
    dump_screen_writes()
    dump_cabinets()
    dump_topology_model()
    dump_rcfg_summary()

    groups = {}
    if CABINETS:
        for item in CABINETS:
            key = (item["dev"], item["port"])
            groups.setdefault(key, []).append(item)
    else:
        groups[(0x00, 0x00)] = []

    for (dev, port), items in groups.items():
        blk_02000000 = bytearray(256)
        blk_02000100 = bytearray(256)
        blk_02020020 = bytearray(64)
        blk_08000000 = bytearray(256)

        count = len(items)

        # Shared single source of truth: the topology model in `items`.
        port_count = len({it["sender_port"] for it in items}) if items else 1
        max_tile = max((it["tile_index"] for it in items), default=0)
        max_cascade = max((it["cascade_order"] for it in items), default=0)
        max_lx = max((it["layout_x"] for it in items), default=0)
        max_ly = max((it["layout_y"] for it in items), default=0)

        # 0x02000000 : layout view
        blk_02000000[0] = 0x01
        blk_02000000[1] = 0x01
        blk_02000000[2] = dev & 0xFF
        blk_02000000[3] = port & 0xFF
        blk_02000000[4] = count & 0xFF
        blk_02000000[5] = 0x20
        blk_02000000[6] = (max_lx + 1) & 0xFF if items else 0x01
        blk_02000000[7] = (max_ly + 1) & 0xFF if items else 0x01

        # 0x02000100 : cascade / chain view
        blk_02000100[0] = 0x01
        blk_02000100[1] = 0xA5
        blk_02000100[2] = dev & 0xFF
        blk_02000100[3] = port & 0xFF
        blk_02000100[4] = count & 0xFF
        blk_02000100[5] = port_count & 0xFF
        blk_02000100[6] = (max_cascade + 1) & 0xFF if items else 0x01
        blk_02000100[7] = 0x01

        # 0x02020020 : compact summary view
        blk_02020020[0] = 0x01
        blk_02020020[1] = dev & 0xFF
        blk_02020020[2] = port & 0xFF
        blk_02020020[3] = count & 0xFF
        blk_02020020[4] = port_count & 0xFF
        blk_02020020[5] = (max_tile + 1) & 0xFF if items else 0x00
        blk_02020020[6] = (max_cascade + 1) & 0xFF if items else 0x00
        blk_02020020[7] = 0x01 if count > 0 else 0x00

        # 0x08000000 : presence/descriptor view
        blk_08000000[0] = count & 0xFF
        blk_08000000[1] = port_count & 0xFF
        blk_08000000[2] = (max_tile + 1) & 0xFF if items else 0x00
        blk_08000000[3] = (max_cascade + 1) & 0xFF if items else 0x00

        # Works_40: preserve route arrival order to keep chain semantics stable
        layout_items = list(items)
        cascade_items = list(items)

        off0 = 16
        for idx, item in enumerate(layout_items):
            packed = pack_layout_entry(item)
            if FIRST2_BUILDER_MODE == "mirror_minimal" and idx < 4:
                packed = bytes([
                    item["sender_port"] & 0xFF,
                    item["tile_index"] & 0xFF,
                    item["tile_index"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    item["layout_x"] & 0xFF,
                    item["layout_y"] & 0xFF,
                    0x01,
                    item["chain_index"] & 0xFF,
                ])
            elif FIRST2_BUILDER_MODE == "zero_tail" and idx < 4:
                packed = bytes([
                    item["layout_x"] & 0xFF,
                    item["layout_y"] & 0xFF,
                    item["sender_port"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    0x00, 0x00, 0x00, 0x00,
                ])
            if off0 + 8 <= 256:
                blk_02000000[off0:off0 + 8] = packed
            off0 += 8

        off1 = 16
        for idx, item in enumerate(cascade_items):
            packed = pack_cascade_entry(item)
            if FIRST2_BUILDER_MODE == "mirror_minimal" and idx < 4:
                packed = bytes([
                    item["sender_port"] & 0xFF,
                    item["tile_index"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    item["chain_index"] & 0xFF,
                    item["raw_x"] & 0xFF,
                    item["raw_y"] & 0xFF,
                    item["layout_x"] & 0xFF,
                    item["layout_y"] & 0xFF,
                ])
            elif FIRST2_BUILDER_MODE == "zero_tail" and idx < 4:
                packed = bytes([
                    item["sender_port"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    item["chain_index"] & 0xFF,
                    item["tile_index"] & 0xFF,
                    0x00, 0x00, 0x00, 0x00,
                ])
            if off1 + 8 <= 256:
                blk_02000100[off1:off1 + 8] = packed
            off1 += 8

        off2 = 8
        for idx, item in enumerate(cascade_items):
            packed = pack_summary_entry(item)
            if FIRST2_BUILDER_MODE == "mirror_minimal" and idx < 4:
                packed = bytes([
                    item["sender_port"] & 0xFF,
                    item["tile_index"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    item["chain_index"] & 0xFF,
                ])
            elif FIRST2_BUILDER_MODE == "zero_tail" and idx < 4:
                packed = bytes([
                    item["sender_port"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    0x00,
                    0x01,
                ])
            if off2 + 4 <= 64:
                blk_02020020[off2:off2 + 4] = packed
            off2 += 4

        for idx, item in enumerate(cascade_items):
            base = idx * 4
            if base + 4 > 256:
                break
            if FIRST2_BUILDER_MODE == "baseline":
                blk_08000000[base:base+4] = bytes([
                    item["sender_port"] & 0xFF,
                    item["tile_index"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    0x01,
                ])
            elif FIRST2_BUILDER_MODE == "mirror_minimal":
                blk_08000000[base:base+4] = bytes([
                    item["sender_port"] & 0xFF,
                    item["tile_index"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    item["chain_index"] & 0xFF,
                ])
            elif FIRST2_BUILDER_MODE == "zero_tail":
                blk_08000000[base:base+4] = bytes([
                    item["sender_port"] & 0xFF,
                    item["cascade_order"] & 0xFF,
                    0x00,
                    0x01,
                ])

        ctrl_block_write(dev, port, 0x02000000, bytes(blk_02000000))
        ctrl_block_write(dev, port, 0x02000100, bytes(blk_02000100))
        ctrl_block_write(dev, port, 0x02020020, bytes(blk_02020020))
        ctrl_block_write(dev, port, 0x08000000, bytes(blk_08000000))

        print(f"[EMU] Screen blocks rebuilt for dev={dev:02X} port={port:02X} entries={count}")
        print(f"[EMU] FIRST4 active_mode={FIRST2_BUILDER_MODE} shaped_entries={min(count, 4)}")
        print(f"[EMU] 0x02000000 head={hex_preview(bytes(blk_02000000))}")
        print(f"[EMU] 0x02000100 head={hex_preview(bytes(blk_02000100))}")
        print(f"[EMU] 0x02020020 head={hex_preview(bytes(blk_02020020))}")
        print(f"[EMU] 0x08000000 head={hex_preview(bytes(blk_08000000))}")

        if count <= 16:
            print(f"[EMU_FULL] 0x02000000={hex_full(bytes(blk_02000000))}")
            print(f"[EMU_FULL] 0x02000100={hex_full(bytes(blk_02000100))}")
            print(f"[EMU_FULL] 0x02020020={hex_full(bytes(blk_02020020))}")
            print(f"[EMU_FULL] 0x08000000={hex_full(bytes(blk_08000000))}")

        if count <= 4:
            print("[EMU] ---- FIRST4 STRUCTURED DUMP ----")
            dump_bytes_by8("02000000", bytes(blk_02000000), limit=48)
            dump_bytes_by8("02000100", bytes(blk_02000100), limit=48)
            dump_bytes_by8("02020020", bytes(blk_02020020), limit=32)
            dump_bytes_by8("08000000", bytes(blk_08000000), limit=32)

    SCREEN_BLOCKS_READY = True

def ensure_screen_blocks_ready():
    if not SCREEN_BLOCKS_READY:
        build_controller_blocks()


def is_sspe_marker(blob: bytes) -> bool:
    return len(blob) >= 8 and blob[:4] == b"SSPE" and blob[4:8] == b"\xEA\x03\x00\x00"


def store_special_branch(info):
    st = session_state()
    st["special_writes"] += 1
    SPECIAL_BRANCH_WRITES.append({
        "serial": info["serial"],
        "dst": info["dst"],
        "reg": info["reg"],
        "n": info["n"],
        "data": bytes(info["write_data"]),
    })
    SPECIAL_BRANCH_WRITES[:] = SPECIAL_BRANCH_WRITES[-128:]
    print(
        f"[EMU] SPECIAL BRANCH WRITE dst={info['dst']:02X} reg=0x{info['reg']:08X} "
        f"len={info['n']} data={hex_preview(info['write_data'])}"
    )

    # Conservative rule: once NovaLCT enters this branch after save, keep the main
    # controller validation state sticky instead of regressing to 0 mid-session.
    for key in list(RCFG_SAVE_MARK.keys()):
        dev, port, rcv, dst = key
        if dst in (0x00, 0x01):
            mark_rcfg_accepted(dev, port, rcv, dst, reason="special-branch")


def store_rcfg(info):
    reg = info["reg"]
    wd = info["write_data"]
    dev = info["dev"]
    port = info["port"]
    rcv = info["rcvIndex"]
    dst = info["dst"]

    st = session_state()
    st["rcfg_writes"] += 1
    mem_write(dev, port, rcv, dst, reg, wd)

    if dst == 0xFF:
        for d in (0x00, 0x01):
            mem_write(dev, port, rcv, d, reg, wd)

    print(
        f"[EMU] RCFG WRITE reg=0x{reg:08X} dst={dst:02X} "
        f"dev={dev:02X} port={port:02X} rcv={rcv:04X} len={len(wd)}"
    )
    print(f"[EMU_FULL] RCFG_0x{reg:08X}={wd.hex()}")

    if reg == 0x05066000 and is_sspe_marker(wd):
        if dst == 0xFF:
            for d in (0x00, 0x01):
                mark_rcfg_saved(dev, port, rcv, d, save_blob=wd)
        else:
            mark_rcfg_saved(dev, port, rcv, dst, save_blob=wd)

        print(
            f"[EMU] RCFG SAVE MARKER ACCEPTED reg=0x{reg:08X} "
            f"dev={dev:02X} port={port:02X} rcv={rcv:04X} dst={dst:02X}"
        )


def handle_command_register_write(info):
    global COMMIT_SEEN
    global SCREEN_BLOCKS_READY

    reg = info["reg"]
    wd = info["write_data"]

    if reg == 0x02000011:
        st = session_state()
        st["route_writes"] += 1
        session_note("route", f"0x{info['reg']:08X}@p{info['port']:02X}/r{info['rcvIndex']:04X}:{wd.hex()}")
        ROUTING_WRITES.append({
            "dev": info["dev"],
            "port": info["port"],
            "rcvIndex": info["rcvIndex"],
            "dst": info["dst"],
            "data": bytes(wd),
        })
        ROUTING_WRITES[:] = ROUTING_WRITES[-512:]
        SCREEN_BLOCKS_READY = False

        print(
            f"[EMU] ROUTE CMD reg=0x{reg:08X} dst={info['dst']:02X} "
            f"dev={info['dev']:02X} port={info['port']:02X} "
            f"rcv={info['rcvIndex']:04X} data={wd.hex()}"
        )

        build_controller_blocks()
        return True

    if reg == 0x02000018:
        st = session_state()
        st["commits"] += 1
        COMMIT_SEEN = True
        SCREEN_BLOCKS_READY = False

        print(
            f"[EMU] COMMIT CMD reg=0x{reg:08X} dst={info['dst']:02X} "
            f"dev={info['dev']:02X} port={info['port']:02X} "
            f"rcv={info['rcvIndex']:04X} data={wd.hex()}"
        )

        build_controller_blocks()
        return True

    return False


def build_ack(req, allowed_dst):
    info = parse_req(req)

    if info["dst"] not in allowed_dst:
        ack = make_ack_base(req, info, 0x01)
        return finalize_ack(ack)

    # only one valid sender identity
    if info["code"] == 0x00 and is_sender_identity_reg(info["reg"], info["n"]):
        if info["dst"] == 0x00:
            ack = make_ack_base(req, info, 0x00)
            ack += read_data(
                info["dev"], info["port"], info["rcvIndex"],
                info["dst"], info["reg"], info["n"]
            )
            return finalize_ack(ack)

        ack = make_ack_base(req, info, 0x01)
        return finalize_ack(ack)

    ack = make_ack_base(req, info, 0x00)

    if info["code"] == 0x01:
        n = info["n"]
        wd = info["write_data"]

        if n == len(wd) and n > 0:
            if handle_command_register_write(info):
                return finalize_ack(ack)

            if protocol_branch_key(info):
                store_special_branch(info)
                return finalize_ack(ack)

            if info["reg"] in RCFG_REGS:
                store_rcfg(info)
                return finalize_ack(ack)

            mem_write(
                info["dev"], info["port"], info["rcvIndex"],
                info["dst"], info["reg"], wd
            )

            if info["dst"] == 0xFF:
                for d in allowed_dst:
                    if d != 0xFF:
                        mem_write(
                            info["dev"], info["port"], info["rcvIndex"],
                            d, info["reg"], wd
                        )

        return finalize_ack(ack)

    if info["code"] == 0x00 and info["n"] > 0:
        n = info["n"]

        if info["reg"] in KEY_SCREEN_REGS:
            ensure_screen_blocks_ready()

        if n > MAX_READ_PAYLOAD:
            ack[2] = 0x04
            return finalize_ack(ack)

        data = read_data(
            info["dev"], info["port"], info["rcvIndex"],
            info["dst"], info["reg"], n
        )

        if save_marker_present(info["dev"], info["port"], info["rcvIndex"], info["dst"]) and (
            info["reg"] in VALIDATION_REGS or info["reg"] in RCFG_REGS
        ):
            bump_postsave_read(info["dev"], info["port"], info["rcvIndex"], info["dst"])
            print(
                f"[EMU] POSTSAVE READ#{postsave_read_count(info['dev'], info['port'], info['rcvIndex'], info['dst'])} "
                f"reg=0x{info['reg']:08X} dst={info['dst']:02X} data={hex_preview(data)}"
            )
            if info["reg"] in (0x05000000, 0x05065000, 0x02100000, 0x0200009D):
                if rcfg_configured(info["dev"], info["port"], info["rcvIndex"], info["dst"]):
                    mark_rcfg_accepted(info["dev"], info["port"], info["rcvIndex"], info["dst"], reason=f"postsave-reg-0x{info['reg']:08X}")

        if info["reg"] in KEY_SCREEN_REGS:
            st = session_state()
            st["screen_reads"] += 1
            session_note("screen", f"0x{info['reg']:08X}/n={info['n']}")
            print(
                f"[EMU] READBACK reg=0x{info['reg']:08X} "
                f"dev={info['dev']:02X} port={info['port']:02X} "
                f"rcv={info['rcvIndex']:04X} dst={info['dst']:02X} "
                f"data={hex_preview(data)}"
            )

        if info["reg"] in VALIDATION_REGS:
            st = session_state()
            st["validation_reads"] += 1
            session_note("validation", f"0x{info['reg']:08X}={data.hex()}")
            if st["route_writes"] <= 2 and st["commits"] >= 1 and len(CABINETS) <= 2:
                st["early_abort_suspected"] = True
            print(
                f"[EMU] VALIDATION READ reg=0x{info['reg']:08X} "
                f"dev={info['dev']:02X} port={info['port']:02X} "
                f"rcv={info['rcvIndex']:04X} dst={info['dst']:02X} "
                f"data={data.hex()}"
            )

        if info["reg"] in RCFG_REGS:
            st = session_state()
            st["rcfg_reads"] += 1
            print(
                f"[EMU] RCFG READ reg=0x{info['reg']:08X} "
                f"dev={info['dev']:02X} port={info['port']:02X} "
                f"rcv={info['rcvIndex']:04X} dst={info['dst']:02X} "
                f"data={hex_preview(data)}"
            )

        ack += data

    return finalize_ack(ack)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=5200)
    ap.add_argument("--allowed-dst", default="00,01,FF")
    ap.add_argument("--first2-builder", default="baseline", choices=["baseline", "mirror_minimal", "zero_tail"])
    args = ap.parse_args()

    global FIRST2_BUILDER_MODE
    FIRST2_BUILDER_MODE = args.first2_builder

    allowed_dst = set(int(x.strip(), 16) for x in args.allowed_dst.split(","))

    print(f"[TCP] Listening on {args.host}:{args.port} allowed_dst={sorted(allowed_dst)}")
    print(f"[EMU] FIRST4_BUILDER_MODE={FIRST2_BUILDER_MODE}")

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((args.host, args.port))
    s.listen(10)

    global CONNECTION_SEQ, ACTIVE_CONN_ID

    while True:
        c, a = s.accept()
        CONNECTION_SEQ += 1
        ACTIVE_CONN_ID = CONNECTION_SEQ
        SESSION_STATE[ACTIVE_CONN_ID]  # ensure created
        print(f"[TCP] Conn#{ACTIVE_CONN_ID} from {a}")
        buf = bytearray()

        try:
            while True:
                data = c.recv(4096)
                if not data:
                    break

                buf += data

                for req in feed_parser(buf):
                    info = parse_req(req)

                    print(
                        f"[TCP] RX serial={info['serial']:02X} src={info['src']:02X} "
                        f"dst={info['dst']:02X} dev={info['dev']:02X} "
                        f"port={info['port']:02X} rcv={info['rcvIndex']:04X} "
                        f"code={info['code']:02X} reg=0x{info['reg']:08X} len={info['n']}"
                    )

                    reply = build_ack(req, allowed_dst)
                    c.sendall(reply)

                    print(f"[TCP] TX ack={reply[2]:02X} bytes={len(reply)}")

        except Exception as e:
            print("[TCP] ERROR:", e)
            dump_session_summary(ACTIVE_CONN_ID, reason=f"exception:{e}")

        finally:
            dump_session_summary(ACTIVE_CONN_ID, reason="close")
            c.close()


if __name__ == "__main__":
    main()