# FluidNC + FigUI on the Lunyee 4040 Nova

*[Version française](README.fr.md)*

How to replace the stock Grbl_ESP32 firmware of a Lunyee 4040 Nova CNC router with [FluidNC](https://github.com/bdring/FluidNC) and the [FigUI](https://github.com/figamore/FigUI) web interface, **keeping the original controller board**.

The pinout of that board is not documented anywhere. It was recovered by disassembling the stock firmware, then every signal that could be exercised was checked on a real machine.

> **Read this first**
>
> - This is an unofficial community guide. It is not affiliated with Lunyee, FluidNC or FigUI.
> - Everything here was tested on **one machine**. Boards and firmware builds can differ between batches. Check that yours matches before flashing ([step 1](docs/en/01-identify-your-board.md)).
> - A wrong pin or polarity can drive an axis into its end stop or start the spindle. You do this at your own risk.
> - The firmware has no emergency-stop input. Make sure you have a hardware stop that cuts power, and keep a hand on it during every first test.
> - Make a full flash backup before anything else ([step 2](docs/en/02-backup-and-restore.md)). It is your only way back.

## Is this your machine?

| Item | Value on the tested machine |
|---|---|
| Controller MCU | ESP32-D0WD-V3, 4 MB flash, CH340 USB adapter |
| Stock firmware | Grbl_ESP32 `1.3a`, build `20231030` (`$I` answers `[VER:1.3a.20231030:]`) |
| Stock web UI | ESP3D WebUI 2.1b68 |
| Strings in the flash | `XBoard E1.0`, `VGRBL-4axis-4040-6.0-V1.0` |
| Drivers | four external step/dir drivers set by DIP switches |
| Spindle | on/off relay, manual speed |

The stock firmware prints five of its pins at boot. If your boot log shows the same GPIO numbers, you have the same pinout: see [step 1](docs/en/01-identify-your-board.md).

## Pinout

| Function | GPIO | Notes |
|---|---|---|
| X step / dir | 33 / 32 | direction inverted |
| Y step / dir | 26 / 25 | |
| Z step / dir | 14 / 27 | direction inverted |
| A step / dir | 12 / 15 | 4th driver, **untested** |
| Stepper enable (shared) | 13 | high = disabled |
| X / Y / Z limit | 34 / 39 / 36 | active low, both switches of an axis on one input |
| Probe | 35 | idle high, contact low |
| Spindle relay | 2 | high = on |
| Spindle PWM | 4 | 10 kHz, nothing known wired to it |
| Home button | 22 | active low, internal pull-up |
| SD card SCK / MISO / MOSI / CS | 18 / 19 / 23 / 5 | |
| Second UART RX / TX | 16 / 17 | pendant port, **untested** |
| Coolant (M8/M9) | none | the stock firmware drives no output |

This is **not** the pinout of the public `XBoard E1.0` machine definition, even though the firmware reports that name. See the [notes](docs/en/06-notes-and-troubleshooting.md#the-public-xboard-e10-definition-does-not-match).

## What was verified

| Feature | Result under FluidNC v4.1.1 |
|---|---|
| Limit switches, probe, Home button | verified |
| Stepper enable and direction of X, Y, Z | verified |
| Homing (`$HZ`, `$H`) | verified |
| Spindle relay on/off | verified |
| SD card reader | verified, but the card shipped with the machine was rejected |
| Wi-Fi | verified |
| FigUI v1.4.3 | verified |
| A axis, second UART, coolant output | not tested |

## Steps

1. [Identify your board](docs/en/01-identify-your-board.md)
2. [Back up the stock firmware, and how to restore it](docs/en/02-backup-and-restore.md)
3. [Flash FluidNC and upload the configuration](docs/en/03-flash-fluidnc.md)
4. [Commissioning: inputs, axes, homing, spindle](docs/en/04-commissioning.md)
5. [Install FigUI](docs/en/05-figui.md)
6. [Notes and troubleshooting](docs/en/06-notes-and-troubleshooting.md)

## Known issues

- **The USB link drops when the spindle relay switches.** The CH340 adapter disconnects for a moment at spindle start or stop. Do not run jobs over USB, and never count on USB to stop the spindle. Use Wi-Fi or the SD card.
- **esptool only works with `--no-stub --baud 115200`** on this board.
- **Opening the serial port reboots the controller.**
- **The SD card shipped with the machine is rejected by FluidNC** (`sdmmc_card_init failed code 0x106`). A recent FAT32 card works.
- The step pulse is 9 µs instead of the stock 10 µs, to keep the stock top speed.

Details and workarounds are in the [notes](docs/en/06-notes-and-troubleshooting.md).

## Repository contents

| Path | What it is |
|---|---|
| [`config.yaml`](config.yaml) | FluidNC configuration validated on the machine |
| [`docs/`](docs/) | the guide, in English and French |
| [`tools/flash_layout.py`](tools/flash_layout.py) | inspect a flash dump: partitions, active app, compare two reads, extract the app |
| [`tools/nvs_dump.py`](tools/nvs_dump.py) | list the settings stored in a dump, passwords masked |
| [`tools/xtensa_xref.py`](tools/xtensa_xref.py) | the disassembly helper used to find the pins |
| [`tools/fluidnc_serial.py`](tools/fluidnc_serial.py) | boot log, status, input watcher, file upload over USB |
| [`CHECKSUMS.md`](CHECKSUMS.md) | SHA-256 of the files used |

No firmware binary is distributed here. Flash dumps contain Wi-Fi passwords: never publish yours.

## Credits

- [FluidNC](https://github.com/bdring/FluidNC) by Bart Dring, Mitch Bradley and contributors.
- [FigUI](https://github.com/figamore/FigUI) by figamore.
- The stock firmware derives from [KnightSin/Grbl_Esp32](https://github.com/KnightSin/Grbl_Esp32), itself a fork of [bdring/Grbl_Esp32](https://github.com/bdring/Grbl_Esp32).

## License

[MIT](LICENSE). Corrections and reports from other machines are welcome: open an issue with your `$I` output and boot log.
