#!/usr/bin/env python3
"""Inspect an ESP32 flash dump: bootloader, partition table, otadata, app images.

Typical use on a full 4 MB dump read with esptool:

    python3 flash_layout.py dump.bin
    python3 flash_layout.py dump.bin --compare second_read.bin
    python3 flash_layout.py dump.bin --extract-app app0.bin

Standard library only. Nothing is written unless --extract-app is given.
"""
import argparse
import binascii
import hashlib
import struct
import sys

BOOTLOADER_OFFSET = 0x1000
PARTITION_TABLE_OFFSET = 0x8000
IMAGE_MAGIC = 0xE9


def parse_image(d, off, name):
    """Print an ESP32 image header and return (segments, total_length) or None."""
    magic, nseg, spi_mode, spi_sf, entry = struct.unpack("<BBBBI", d[off:off + 8])
    print(f"\n== {name} @0x{off:06X}: magic=0x{magic:02X} segments={nseg} "
          f"spi_mode={spi_mode} size/freq=0x{spi_sf:02X} entry=0x{entry:08X}")
    if magic != IMAGE_MAGIC:
        print("   not an ESP32 image (empty slot?)")
        return None
    hash_appended = d[off + 23]
    o = off + 24
    segs = []
    checksum = 0xEF
    for i in range(nseg):
        addr, ln = struct.unpack("<II", d[o:o + 8])
        for b in d[o + 8:o + 8 + ln]:
            checksum ^= b
        segs.append((addr, ln, o + 8))
        print(f"   seg{i}: vaddr=0x{addr:08X} len=0x{ln:06X} fileoff=0x{o + 8:06X}")
        o += 8 + ln
    end = o + (16 - (o % 16))
    stored = d[end - 1]
    print(f"   checksum 0x{checksum:02X} (stored 0x{stored:02X}) "
          f"{'OK' if checksum == stored else 'BAD'}")
    if hash_appended:
        calc = hashlib.sha256(d[off:end]).hexdigest()
        ok = calc == d[end:end + 32].hex()
        print(f"   sha256 {'OK' if ok else 'BAD'} {calc}")
        end += 32
    print(f"   image length 0x{end - off:06X} ({end - off} bytes)")
    return segs, end - off


def parse_partitions(d):
    parts = []
    print(f"\n== partition table @0x{PARTITION_TABLE_OFFSET:04X}")
    for i in range(0, 0xC00, 32):
        e = d[PARTITION_TABLE_OFFSET + i:PARTITION_TABLE_OFFSET + i + 32]
        if e[:2] == b"\xAA\x50":
            ptype, subtype, off, size = struct.unpack("<BBII", e[2:12])
            label = e[12:28].split(b"\0")[0].decode()
            parts.append((label, ptype, subtype, off, size))
            print(f"   {label:10s} type={ptype} subtype=0x{subtype:02X} "
                  f"offset=0x{off:06X} size=0x{size:06X}")
        else:
            break
    return parts


def parse_otadata(d, parts):
    ota = [p for p in parts if p[1] == 1 and p[2] == 0x00]
    apps = [p for p in parts if p[1] == 0]
    if not ota:
        return apps[0] if apps else None
    off = ota[0][3]
    print("\n== otadata")
    valid = []
    for k in range(2):
        e = d[off + k * 0x1000:off + k * 0x1000 + 32]
        seq, = struct.unpack("<I", e[:4])
        crc, = struct.unpack("<I", e[28:32])
        calc = binascii.crc32(e[:4], 0xFFFFFFFF) & 0xFFFFFFFF
        ok = seq not in (0, 0xFFFFFFFF) and crc == calc
        print(f"   entry{k}: seq=0x{seq:08X} crc {'OK' if ok else 'invalid'}")
        if ok:
            valid.append(seq)
    ota_apps = [p for p in apps if 0x10 <= p[2] < 0x20]
    if not ota_apps:
        return apps[0] if apps else None
    if not valid:
        print(f"   no valid entry: bootloader starts the first app slot ({ota_apps[0][0]})")
        return ota_apps[0]
    active = ota_apps[(max(valid) - 1) % len(ota_apps)]
    print(f"   active slot: {active[0]}")
    return active


def region_map(d):
    def kind(b):
        if b.count(0xFF) == len(b):
            return "erased (FF)"
        if b.count(0) == len(b):
            return "zeros"
        return "data"
    print("\n== region map (4 KiB blocks)")
    prev, start = None, 0
    for off in range(0, len(d) + 1, 0x1000):
        k = kind(d[off:off + 0x1000]) if off < len(d) else None
        if k != prev:
            if prev is not None:
                print(f"   0x{start:06X}-0x{off:06X} {prev} ({(off - start) // 1024} KiB)")
            prev, start = k, off


def compare(a, b, parts):
    diffs = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    print(f"\n== compare: {len(diffs)} differing bytes")
    if not diffs:
        return
    print(f"   first 0x{diffs[0]:06X}, last 0x{diffs[-1]:06X}")
    for label, _, _, off, size in parts:
        n = sum(1 for i in diffs if off <= i < off + size)
        if n:
            print(f"   {n} in partition '{label}'")
    print("   Differences limited to 'nvs' are normal: the Wi-Fi stack rewrites it at boot.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump", help="full flash dump (read with esptool read-flash 0x0 ...)")
    ap.add_argument("--compare", metavar="OTHER", help="second dump to compare byte by byte")
    ap.add_argument("--extract-app", metavar="OUT",
                    help="write the active application image to OUT")
    args = ap.parse_args()

    d = open(args.dump, "rb").read()
    print(f"{args.dump}: {len(d)} bytes")
    parse_image(d, BOOTLOADER_OFFSET, "bootloader")
    parts = parse_partitions(d)
    active = parse_otadata(d, parts)
    images = {}
    for label, ptype, _, off, size in parts:
        if ptype == 0:
            images[label] = parse_image(d, off, label)
    region_map(d)
    if args.compare:
        compare(d, open(args.compare, "rb").read(), parts)
    if args.extract_app:
        if not active or not images.get(active[0]):
            sys.exit("no valid active application image found")
        off, length = active[3], images[active[0]][1]
        with open(args.extract_app, "wb") as f:
            f.write(d[off:off + length])
        print(f"\nwrote {length} bytes of '{active[0]}' to {args.extract_app}")


if __name__ == "__main__":
    main()
