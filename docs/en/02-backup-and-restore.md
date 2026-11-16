# 2. Back up the stock firmware, and how to restore it

Do this before anything else. The backup is the only way to return to the stock firmware: no stock image is distributed here or, as far as we know, by the vendor.

## 2.1 What you need

- Python 3 and [esptool](https://docs.espressif.com/projects/esptool/): `pip install esptool`
- The USB cable of the machine, plugged directly into the computer.
- The spindle switched off for the whole operation.

The commands below use the esptool 5 syntax (`read-flash`, `write-flash`). Older versions use underscores (`read_flash`, `write_flash`).

Find your port: `/dev/cu.usbserial-XXXX` on macOS, `/dev/ttyUSB0` on Linux, `COMx` on Windows. It is called `PORT` below.

## 2.2 Read the whole flash, twice

On the tested board esptool's default mode failed partway through. Disabling the stub and staying at 115200 baud worked:

```bash
esptool --chip esp32 --port PORT --baud 115200 --no-stub \
  read-flash --flash-size 4MB 0x0 0x400000 stock_read1.bin

esptool --chip esp32 --port PORT --baud 115200 --no-stub \
  read-flash --flash-size 4MB 0x0 0x400000 stock_read2.bin
```

Each read takes about 13 minutes. Each file must be exactly 4 194 304 bytes.

## 2.3 Check the backup

```bash
python3 tools/flash_layout.py stock_read1.bin --compare stock_read2.bin
```

What to look for:

- `bootloader` and `app0`: `checksum ... OK` and `sha256 OK`.
- The two reads differ by a small number of bytes, **all inside the `nvs` partition**. That is normal: the Wi-Fi stack rewrites two entries at every boot. Any difference elsewhere means a bad read: read again.
- On the tested machine, `otadata` is all zeros and `app1` is empty, so the bootloader starts `app0`.

If you want to compare your firmware with the tested one, extract the application and hash it:

```bash
python3 tools/flash_layout.py stock_read1.bin --extract-app app0.bin
shasum -a 256 app0.bin
```

The value for the tested machine is in [CHECKSUMS.md](../../CHECKSUMS.md). A different hash means a different firmware build: go back to [step 1](01-identify-your-board.md) and check the pins carefully.

## 2.4 Keep it safe, keep it private

- Record the hashes: `shasum -a 256 stock_read*.bin > SHA256SUMS.txt`
- Copy the files somewhere other than this computer.
- **Never publish a full dump.** It contains your Wi-Fi name and password in clear text. `tools/nvs_dump.py` shows what is stored, with passwords masked.

## 2.5 Restore the stock firmware

Write the full image back. This returns the machine to exactly the state of the backup, settings and Wi-Fi included.

```bash
shasum -a 256 -c SHA256SUMS.txt

esptool --chip esp32 --port PORT --baud 115200 --no-stub \
  write-flash --flash-mode keep --flash-freq keep --flash-size 4MB \
  0x0 stock_read1.bin
```

- esptool must end with `Hash of data verified`.
- If the write is interrupted, run the command again. The serial bootloader lives in the chip's ROM and cannot be erased by a bad flash; FluidNC does not touch the eFuses.

> This restore command was prepared and checked against the backup, but it was not actually run on the tested machine, because the migration went well. The same write method was used successfully to install FluidNC.

Next: [flash FluidNC](03-flash-fluidnc.md).
