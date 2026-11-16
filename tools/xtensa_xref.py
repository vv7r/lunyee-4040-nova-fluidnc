#!/usr/bin/env python3
"""Small cross-reference helper for ESP32 (Xtensa) application images.

It was used to recover the GPIO assignments compiled into the Lunyee 4040 Nova
stock firmware. Input is an application image, as written by
`flash_layout.py dump.bin --extract-app app0.bin`.

    python3 xtensa_xref.py app0.bin segments
    python3 xtensa_xref.py app0.bin strings "limit switch on pin" "Probe on pin"
    python3 xtensa_xref.py app0.bin dis 0x400d4570 -n 80
    python3 xtensa_xref.py app0.bin callers 0x40081fb8
    python3 xtensa_xref.py app0.bin hex 0x3ffbec14 16

Requires capstone >= 6 (Xtensa support). Read-only.

How the pins were found, in short:
  1. `strings` on boot messages ("%s limit switch on pin %s", "Probe on pin %s")
     gives the functions that initialise each input.
  2. Those functions call pinMode(); `callers` on that address lists every
     pinMode call with the constants loaded just before it.
  3. Motor pins are the arguments of the four stepper constructor calls.
"""
import argparse
import struct
import sys

try:
    from capstone import Cs, CS_ARCH_XTENSA, CS_MODE_XTENSA_ESP32
except ImportError:
    sys.exit("capstone >= 6 is required: pip install 'capstone>=6'")


class Image:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        if self.d[0] != 0xE9:
            sys.exit("not an ESP32 application image (use flash_layout.py --extract-app)")
        self.segs = []
        o = 24
        for _ in range(self.d[1]):
            addr, ln = struct.unpack("<II", self.d[o:o + 8])
            self.segs.append((addr, ln, o + 8))
            o += 8 + ln
        self.code = [s for s in self.segs if s[0] >= 0x40000000]
        self.md = Cs(CS_ARCH_XTENSA, CS_MODE_XTENSA_ESP32)

    # --- address translation -------------------------------------------------
    def v2f(self, v):
        for a, ln, f in self.segs:
            if a <= v < a + ln:
                return f + (v - a)
        return None

    def f2v(self, fo):
        for a, ln, f in self.segs:
            if f <= fo < f + ln:
                return a + (fo - f)
        return None

    def read(self, v, n):
        f = self.v2f(v)
        return self.d[f:f + n] if f is not None else None

    def u32(self, v):
        b = self.read(v, 4)
        return struct.unpack("<I", b)[0] if b and len(b) == 4 else None

    def cstr(self, v, mx=200):
        f = self.v2f(v)
        if f is None:
            return None
        e = self.d.find(b"\0", f, f + mx)
        if e < 0:
            e = f + mx
        try:
            return self.d[f:e].decode("ascii")
        except UnicodeDecodeError:
            return None

    # --- cross references ----------------------------------------------------
    def literal_slots(self, value):
        """Aligned literal-pool slots holding `value`."""
        pat = struct.pack("<I", value)
        res = []
        for a, ln, f in self.segs:
            i = f
            while True:
                i = self.d.find(pat, i, f + ln)
                if i < 0:
                    break
                if (a + (i - f)) % 4 == 0:
                    res.append(a + (i - f))
                i += 1
        return res

    def l32r_sites(self, slot):
        """Addresses of l32r instructions loading from `slot` (brute force)."""
        res = []
        for a, ln, f in self.code:
            blob = self.d[f:f + ln]
            for i in range(0, ln - 3):
                if blob[i] & 0x0F == 1:
                    imm = blob[i + 1] | (blob[i + 2] << 8)
                    pc = a + i
                    if ((((pc + 3) & ~3) + ((imm | 0xFFFF0000) << 2)) & 0xFFFFFFFF) == slot:
                        res.append(pc)
        return res

    def xrefs(self, value):
        return [(site, slot) for slot in self.literal_slots(value) for site in self.l32r_sites(slot)]

    def callers(self, target):
        """Addresses of direct call instructions reaching `target` (brute force)."""
        res = []
        for a, ln, f in self.code:
            blob = self.d[f:f + ln]
            for i in range(0, ln - 3):
                if blob[i] & 0x0F == 5:
                    w = blob[i] | (blob[i + 1] << 8) | (blob[i + 2] << 16)
                    off = w >> 6
                    if off & 0x20000:
                        off -= 0x40000
                    pc = a + i
                    if (((pc & ~3) + (off << 2) + 4) & 0xFFFFFFFF) == target:
                        res.append(pc)
        return res

    def func_start(self, pc, maxback=4000):
        """Nearest preceding `entry a1, N` instruction."""
        f = self.v2f(pc)
        if f is None:
            return None
        for i in range(f, max(f - maxback, 0), -1):
            if self.d[i] == 0x36 and (self.d[i + 1] & 0x0F) == 1 and self.d[i + 2] < 0x20 \
                    and self.f2v(i) is not None and self.f2v(i) % 4 == 0:
                return self.f2v(i)
        return None

    # --- disassembly ---------------------------------------------------------
    def _call_target(self, addr):
        b = self.read(addr, 3)
        off = (b[0] | (b[1] << 8) | (b[2] << 16)) >> 6
        if off & 0x20000:
            off -= 0x40000
        return ((addr & ~3) + (off << 2) + 4) & 0xFFFFFFFF

    def _annotate(self, ins):
        s = f"{ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}"
        if ins.mnemonic == "l32r":
            b = self.read(ins.address, 3)
            slot = (((ins.address + 3) & ~3) + (((b[1] | (b[2] << 8)) | 0xFFFF0000) << 2)) & 0xFFFFFFFF
            val = self.u32(slot)
            s += f"   ; [{slot:08x}]=" + (f"{val:08x}" if val is not None else "?")
            if val is not None and 0x3F400000 <= val < 0x3F500000:
                text = self.cstr(val)
                if text and len(text) >= 2:
                    s += f'  "{text[:70]}"'
        elif ins.mnemonic in ("call0", "call4", "call8", "call12"):
            s += f"   ; -> {self._call_target(ins.address):08x}"
        return s

    def dis(self, start, count=120):
        out, pc = [], start
        for _ in range(count):
            f = self.v2f(pc)
            if f is None:
                break
            decoded = list(self.md.disasm(self.d[f:f + 3], pc, 1))
            if decoded:
                out.append(self._annotate(decoded[0]))
                pc += decoded[0].size
                continue
            # capstone does not decode the narrow branches beqz.n / bnez.n
            b0, b1 = self.d[f], self.d[f + 1]
            if (b0 & 0x0F) == 0x0C and (b0 & 0x80):
                imm = (((b0 >> 4) & 3) << 4) | (b1 >> 4)
                name = "bnez.n" if (b0 & 0x40) else "beqz.n"
                out.append(f"{pc:08x}: {name:8s} a{b1 & 0xF}, 0x{pc + 4 + imm:08x}")
                pc += 2
            else:
                out.append(f"{pc:08x}: .byte 0x{b0:02x}")
                pc += 1
        return out

    def context(self, site, window):
        """Instructions leading to `site`, disassembled from its function start."""
        fs = self.func_start(site)
        if fs is None:
            return [f"(no function start found before {site:08x})"]
        lines = self.dis(fs, 3000)
        idx = [i for i, t in enumerate(lines) if t.startswith(f"{site:08x}:")]
        if not idx:
            return [f"(site {site:08x} not reached linearly from {fs:08x})"]
        return [f"-- function {fs:08x}"] + lines[max(0, idx[0] - window):idx[0] + 1]


def hexint(x):
    return int(x, 16)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", help="ESP32 application image")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("segments", help="list image segments")
    p = sub.add_parser("strings", help="find strings and the code that references them")
    p.add_argument("text", nargs="+")
    p = sub.add_parser("xval", help="find code loading a 32-bit value (hex)")
    p.add_argument("value", nargs="+", type=hexint)
    p = sub.add_parser("dis", help="disassemble from an address (hex)")
    p.add_argument("address", type=hexint)
    p.add_argument("-n", type=int, default=120, help="instruction count")
    p = sub.add_parser("callers", help="list calls to an address (hex) with preceding code")
    p.add_argument("address", type=hexint)
    p.add_argument("-w", type=int, default=8, help="instructions of context")
    p = sub.add_parser("hex", help="hex dump at a virtual address (hex)")
    p.add_argument("address", type=hexint)
    p.add_argument("length", type=int)
    args = ap.parse_args()

    im = Image(args.image)
    if args.cmd == "segments":
        for a, ln, f in im.segs:
            print(f"vaddr 0x{a:08x} len 0x{ln:06x} fileoff 0x{f:06x}")
    elif args.cmd == "strings":
        for needle in args.text:
            i = -1
            while True:
                i = im.d.find(needle.encode(), i + 1)
                if i < 0:
                    break
                v = im.f2v(i)
                if v is None:
                    continue
                print(f'"{needle}" at file 0x{i:x}, vaddr 0x{v:08x}')
                # The code references the start of the C string, which may be a few
                # bytes before the match: try every start back to the previous NUL.
                first = max(im.d.rfind(b"\0", max(0, i - 120), i) + 1, i - 120)
                for start in range(i, first - 1, -1):
                    sv = im.f2v(start)
                    if sv is None:
                        break
                    text = im.cstr(sv)
                    if text is None or needle not in text:
                        continue
                    for site, slot in im.xrefs(sv):
                        fs = im.func_start(site) or 0
                        print(f'   "{text[:60]}" loaded at 0x{site:08x} '
                              f"(literal 0x{slot:08x}), function 0x{fs:08x}")
    elif args.cmd == "xval":
        for v in args.value:
            for site, slot in im.xrefs(v):
                fs = im.func_start(site) or 0
                print(f"0x{v:08x}: loaded at 0x{site:08x} (literal 0x{slot:08x}), function 0x{fs:08x}")
    elif args.cmd == "dis":
        print("\n".join(im.dis(args.address, args.n)))
    elif args.cmd == "callers":
        sites = im.callers(args.address)
        print(f"{len(sites)} call(s) to 0x{args.address:08x}\n")
        for site in sites:
            print("\n".join(im.context(site, args.w)))
            print()
    elif args.cmd == "hex":
        b = im.read(args.address, args.length)
        if b is None:
            sys.exit("address not in image")
        for i in range(0, len(b), 16):
            row = b[i:i + 16]
            text = "".join(chr(c) if 32 <= c < 127 else "." for c in row)
            print(f"{args.address + i:08x}: {row.hex(' '):47s}  {text}")


if __name__ == "__main__":
    main()
