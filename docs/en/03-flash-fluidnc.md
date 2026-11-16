# 3. Flash FluidNC and upload the configuration

Prerequisites: your board matches ([step 1](01-identify-your-board.md)) and you have a verified backup ([step 2](02-backup-and-restore.md)). Keep the spindle off during the whole step.

This guide was validated with **FluidNC v4.1.1**. A newer release may change configuration keys: read its release notes, and repeat the commissioning checks after any upgrade.

## 3.1 Get FluidNC

Download `fluidnc-v4.1.1-posix.zip` (macOS, Linux) or the `win64` zip from the [FluidNC releases](https://github.com/bdring/FluidNC/releases/tag/v4.1.1) and unpack it. Hashes are in [CHECKSUMS.md](../../CHECKSUMS.md).

The partition layout of FluidNC's 4 MB build is identical to the stock one, and `firmware.bin` (1.83 MB) fits in the 1.92 MB application slot.

The install scripts in the package use esptool's stub at 230400 baud, which was unreliable on this board. Use the manual commands below instead.

## 3.2 Check the security fuses

FluidNC's own installer refuses to flash a chip with secure boot or flash encryption enabled. Do the same check:

```bash
esptool --chip esp32 --port PORT --baud 115200 --no-stub read-mem 0x3ff5a018
```

Expected: `0x00000004` (tested machine) or `0x00000000`. Anything else: stop and read the FluidNC wiki.

## 3.3 Write the firmware

From the unpacked FluidNC folder. The first command creates a blank NVS image, because a full chip erase is not available without the stub.

```bash
dd if=/dev/zero bs=4096 count=5 | LC_ALL=C tr '\000' '\377' > nvs_blank.bin

esptool --chip esp32 --port PORT --baud 115200 --no-stub \
  write-flash --flash-mode dio --flash-freq 80m --flash-size 4MB \
  0x1000   wifi/bootloader.bin \
  0x8000   wifi/partitions.bin \
  0x9000   nvs_blank.bin \
  0xe000   common/boot_app0.bin \
  0x10000  wifi/firmware.bin \
  0x3d0000 wifi/littlefs.bin
```

It takes about four minutes. Each of the six blocks must end with `Hash of data verified`.

At this point FluidNC runs with its default "test drive" machine: no pins are assigned, so nothing can move.

## 3.4 Upload `config.yaml`

Over USB, with the tool from this repository:

```bash
pip install pyserial xmodem
python3 tools/fluidnc_serial.py upload config.yaml config.yaml --restart
```

Or over Wi-Fi: join the `FluidNC` network (password `12345678`), open `http://192.168.0.1`, upload `config.yaml` to the **local filesystem** (not the SD card) and restart.

## 3.5 Read the boot log

The `--restart` option prints it; otherwise send `$SS`. There must be **no line starting with `[MSG:ERR`**, and you should recognise the pinout:

```text
[MSG:INFO: Machine Lunyee 4040 Nova]
[MSG:INFO: SD Card cs_pin:gpio.5 detect:NO_PIN freq:4000000]
[MSG:INFO: Stepping:RMT Pulse:9us Dsbl Delay:0us Dir Delay:0us Idle Delay:25ms]
[MSG:INFO: Axis count 4]
[MSG:INFO: Shared stepper disable gpio.13]
[MSG:INFO:     standard_stepper Step:gpio.33 Dir:gpio.32:low Disable:NO_PIN]
[MSG:INFO:  X All Limit gpio.34:low]
...
[MSG:INFO: homing_button_pin gpio.22:low:pu]
[MSG:INFO: PWM Spindle Ena:gpio.2 Out:gpio.4 Dir:NO_PIN Freq:10000Hz Period:4095]
[MSG:INFO: Probe gpio.35:low]
[MSG:INFO: ALARM: Unhomed]
```

The machine starts in `Alarm` and asks for homing. That is the `must_home: true` setting; the stock firmware started in `Idle`.

An `sdmmc_card_init failed` error when the web page opens only concerns the SD card: see the [notes](06-notes-and-troubleshooting.md#sd-card-rejected-code-0x106).

## 3.6 Wi-Fi

In the web UI settings, or over serial: `$Sta/SSID=<your-ssid>`, `$Sta/Password=<your-password>`, then restart. The board only supports 2.4 GHz networks. It is then reachable at `http://fluidnc.local`.

Your stock settings, work offsets (G54...) and Wi-Fi credentials are gone, since the NVS was blanked. Set your work zero again before the first job.

Next: [commissioning](04-commissioning.md).
