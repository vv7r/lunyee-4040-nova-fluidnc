#!/usr/bin/env python3
"""Decode the NVS partition of an ESP32 flash dump and list its entries.

    python3 nvs_dump.py dump.bin
    python3 nvs_dump.py dump.bin --compare second_read.bin

Passwords are masked in the output. Standard library only, read-only.

A full flash dump contains your Wi-Fi password in clear text inside this
partition: never publish or share a raw dump.
"""
import argparse
import binascii
import struct

PAGE = 0x1000
SECRET_HINTS = ("pass", "pwd", "pswd", "pmk")


def crc32(b):
    return binascii.crc32(b, 0xFFFFFFFF) & 0xFFFFFFFF


def parse(path, offset, size):
    d = open(path, "rb").read()[offset:offset + size]
    entries, namespaces, pages, bad = {}, {}, [], 0
    for p in range(0, len(d), PAGE):
        pg = d[p:p + PAGE]
        state, seq = struct.unpack("<II", pg[:8])
        header_ok = crc32(pg[4:28]) == struct.unpack("<I", pg[28:32])[0]
        pages.append((offset + p, state, seq, header_ok))
        if state not in (0xFFFFFFFE, 0xFFFFFFFC):  # active or full
            continue
        bitmap = pg[32:64]
        i = 0
        while i < 126:
            if (bitmap[i // 4] >> ((i % 4) * 2)) & 3 != 2:  # 2 = written
                i += 1
                continue
            e = pg[64 + i * 32:96 + i * 32]
            ns, typ, span = e[0], e[1], e[2]
            if crc32(e[0:4] + e[8:32]) != struct.unpack("<I", e[4:8])[0]:
                bad += 1
            key = e[8:24].split(b"\0")[0].decode("latin1")
            data = e[24:32]
            if ns == 0:
                namespaces[data[0]] = key
                value = data[0]
            elif typ in (0x21, 0x41, 0x42):  # string / blob
                ln = struct.unpack("<H", data[:2])[0]
                raw = pg[64 + (i + 1) * 32:64 + (i + 1) * 32 + ln]
                value = raw.rstrip(b"\0").decode("latin1") if typ == 0x21 else f"<blob {ln} bytes>"
            elif typ == 0x48:
                value = "<blob index>"
            else:
                n = typ & 0x0F
                value = int.from_bytes(data[:n], "little", signed=bool(typ & 0x10))
            entries[(ns, key)] = (value, offset + p + 64 + i * 32)
            i += max(span, 1)
    return pages, namespaces, entries, bad


def shown(key, value):
    if any(h in key.lower() for h in SECRET_HINTS):
        return "<masked>"
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump")
    ap.add_argument("--offset", type=lambda x: int(x, 0), default=0x9000,
                    help="NVS partition offset (default 0x9000)")
    ap.add_argument("--size", type=lambda x: int(x, 0), default=0x5000,
                    help="NVS partition size (default 0x5000)")
    ap.add_argument("--compare", metavar="OTHER", help="second dump to compare entries with")
    args = ap.parse_args()

    pages, namespaces, entries, bad = parse(args.dump, args.offset, args.size)
    print("pages:")
    for off, state, seq, ok in pages:
        print(f"   0x{off:06X} state=0x{state:08X} seq={seq} header {'OK' if ok else 'unused/invalid'}")
    print(f"{len(entries)} entries, {bad} with a bad CRC")
    for (ns, key) in sorted(entries):
        value = entries[(ns, key)][0]
        print(f"   {namespaces.get(ns, ns)!s:14s} {key:16s} = {shown(key, value)}")

    if args.compare:
        _, _, other, _ = parse(args.compare, args.offset, args.size)
        print("\ndifferences:")
        found = False
        for k in sorted(set(entries) | set(other)):
            a, b = entries.get(k), other.get(k)
            if a != b:
                found = True
                what = "value differs" if (a and b and a[0] != b[0]) else "moved or rewritten"
                print(f"   {namespaces.get(k[0], k[0])}/{k[1]}: {what}")
        if not found:
            print("   none")


if __name__ == "__main__":
    main()
