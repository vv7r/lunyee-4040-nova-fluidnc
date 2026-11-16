#!/usr/bin/env python3
"""Talk to the controller over USB serial, for both the stock firmware and FluidNC.

    python3 fluidnc_serial.py log                 # boot messages (shows the pins)
    python3 fluidnc_serial.py status              # three "?" status reports
    python3 fluidnc_serial.py watch 90            # print input changes while you press switches
    python3 fluidnc_serial.py send '$SS' '$SD/List'
    python3 fluidnc_serial.py send --burst --wait 8 '$X' 'M3 S1000' 'G4 P3' 'M5'
    python3 fluidnc_serial.py upload config.yaml config.yaml --restart
    python3 fluidnc_serial.py upload index.html.gz index.html.gz --delete-first

Requires pyserial, plus xmodem for `upload` (FluidNC only).

Things worth knowing about this board (CH340 USB adapter):
  * Opening the port reboots the controller. Each command below opens it once,
    waits for the banner, then does its work.
  * Do not toggle DTR/RTS or open/close in a loop: the macOS driver can lock up
    until the cable is unplugged.
  * The USB link drops when the spindle relay switches. Never rely on it to
    stop the spindle: keep a hardware stop within reach.
"""
import argparse
import glob
import os
import re
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial is required: pip install pyserial")

BANNER = r"for help\]"          # matches Grbl_ESP32 and FluidNC banners
DONE = r"(^|\n)(ok|error:[0-9]+)\s"


def find_port():
    for pattern in ("/dev/cu.usbserial-*", "/dev/cu.wchusbserial*", "/dev/ttyUSB*"):
        ports = sorted(glob.glob(pattern))
        if ports:
            return ports[0]
    sys.exit("no USB serial port found; use --port")


class Link:
    def __init__(self, port, baud):
        self.s = serial.Serial()
        self.s.port = port or find_port()
        self.s.baudrate = baud
        self.s.timeout = 0.05
        self.s.dtr = False
        self.s.rts = False
        self.s.open()
        self.t0 = time.time()

    def now(self):
        return time.time() - self.t0

    def read(self, secs, until=None):
        end = time.time() + secs
        buf = ""
        while time.time() < end:
            buf += self.s.read(4096).decode("latin1")
            if until and re.search(until, buf):
                break
        return buf.replace("\r", "")

    def wait_banner(self, timeout=25):
        text = self.read(timeout, BANNER)
        ready = re.search(BANNER, text) is not None
        text += self.read(1.5)
        return ready, text

    def command(self, line, wait=6.0):
        self.s.write(b"?" if line == "?" else (line + "\n").encode())
        return self.read(1.0 if line == "?" else wait, None if line == "?" else DONE)

    def close(self):
        self.s.close()


def show(text):
    for line in text.split("\n"):
        if line.strip():
            print("   ", line)


def cmd_log(link, args):
    ready, text = link.wait_banner()
    show(text)
    if not ready:
        print("(no firmware banner seen)")


def cmd_status(link, args):
    ready, _ = link.wait_banner()
    if not ready:
        sys.exit("firmware not ready")
    for _ in range(3):
        show(link.command("?"))
        time.sleep(0.5)


def cmd_send(link, args):
    ready, _ = link.wait_banner()
    if not ready:
        sys.exit("firmware not ready, nothing sent")
    if args.burst:
        # One write: the controller holds every line before it runs the first,
        # so a stop command still executes if the USB link drops meanwhile.
        print(f"[{link.now():5.1f}s] >>> " + " / ".join(args.line))
        link.s.write(("\n".join(args.line) + "\n").encode())
        link.s.flush()
        try:
            show(link.read(args.wait))
        except (OSError, serial.SerialException) as e:
            print(f"[{link.now():5.1f}s] USB link lost ({e}). Check the machine by eye.")
        return
    for line in args.line:
        print(f"[{link.now():5.1f}s] >>> {line}")
        show(link.command(line, args.wait))


def cmd_watch(link, args):
    ready, _ = link.wait_banner()
    if not ready:
        sys.exit("firmware not ready")
    print(f"[{link.now():5.1f}s] watching inputs for {args.seconds:.0f} s")
    end = time.time() + args.seconds
    last, buf, next_poll = None, "", 0
    while time.time() < end:
        if time.time() >= next_poll:
            link.s.write(b"?")
            next_poll = time.time() + 0.1
        buf += link.s.read(4096).decode("latin1").replace("\r", "")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line or line == "ok":
                continue
            m = re.match(r"<([^|>]*)\|", line)
            if m:
                pn = re.search(r"\|Pn:([A-Z]*)", line)
                key = (m.group(1), pn.group(1) if pn else "-")
                if key != last:
                    print(f"[{link.now():5.1f}s] state={key[0]:8s} Pn={key[1]}")
                    last = key
            else:
                print(f"[{link.now():5.1f}s] {line}")


def cmd_upload(link, args):
    try:
        from xmodem import XMODEM
    except ImportError:
        sys.exit("xmodem is required for upload: pip install xmodem")
    ready, _ = link.wait_banner()
    if not ready:
        sys.exit("FluidNC not ready, nothing changed")
    if args.delete_first:
        print(f">>> $LocalFS/Delete={args.remote}")
        show(link.command(f"$LocalFS/Delete={args.remote}"))
    size = os.path.getsize(args.local)
    print(f"[{link.now():5.1f}s] sending {args.local} ({size} bytes) as {args.remote}")
    link.s.write(f"$Xmodem/Receive={args.remote}\n".encode())
    time.sleep(0.5)
    link.s.reset_input_buffer()

    def getc(n, timeout=1):
        link.s.timeout = timeout
        return link.s.read(n) or None

    def putc(data, timeout=1):
        return link.s.write(data)

    with open(args.local, "rb") as f:
        ok = XMODEM(getc, putc, mode="xmodem").send(f, retry=30)
    link.s.timeout = 0.05
    print(f"[{link.now():5.1f}s] transfer {'OK' if ok else 'FAILED'}")
    show(link.read(4.0))
    show(link.command("$LocalFS/List"))
    if not ok:
        sys.exit(1)
    if args.restart:
        print(">>> $Bye (restart)")
        link.s.write(b"$Bye\n")
        _, text = link.wait_banner()
        show(text)
        print("Check the lines above for [MSG:ERR ...] before trusting the configuration.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", help="serial port (default: first USB serial port found)")
    ap.add_argument("--baud", type=int, default=115200)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("log", help="print the boot messages").set_defaults(fn=cmd_log)
    sub.add_parser("status", help="print three status reports").set_defaults(fn=cmd_status)
    p = sub.add_parser("send", help="send command lines and print the replies")
    p.add_argument("line", nargs="+")
    p.add_argument("--wait", type=float, default=6.0, help="seconds to wait per command")
    p.add_argument("--burst", action="store_true",
                   help="send all lines in a single write (use it for spindle tests)")
    p.set_defaults(fn=cmd_send)
    p = sub.add_parser("watch", help="print state and input (Pn:) changes")
    p.add_argument("seconds", type=float)
    p.set_defaults(fn=cmd_watch)
    p = sub.add_parser("upload", help="send a file to FluidNC's local filesystem (XModem)")
    p.add_argument("local")
    p.add_argument("remote")
    p.add_argument("--delete-first", action="store_true",
                   help="delete the remote file first (needed to free space for a web UI)")
    p.add_argument("--restart", action="store_true", help="restart FluidNC afterwards")
    p.set_defaults(fn=cmd_upload)
    args = ap.parse_args()

    link = Link(args.port, args.baud)
    try:
        args.fn(link, args)
    finally:
        link.close()


if __name__ == "__main__":
    main()
