# 6. Notes and troubleshooting

## The USB link drops when the spindle switches

On the tested machine the CH340 USB adapter disconnects for a moment every time the spindle relay switches, at start or at stop. The host sees the serial device disappear and come back. It is electrical noise from the relay or the spindle motor, independent of the firmware: it happened with both the stock firmware and FluidNC.

What it means in practice:

- A command sent after the drop never arrives. During testing, an `M5` sent over USB was lost and the spindle kept running until power was cut.
- Do not run jobs over USB. Use Wi-Fi or the SD card.
- Never rely on software to stop the spindle. Keep a hardware stop within reach.
- For tests over USB, send start, dwell and stop in one write (`fluidnc_serial.py send --burst`).

Things that may help, none of them tested here: a ferrite on the USB cable, a shorter shielded cable, a USB isolator, a noise filter on the spindle supply.

Flashing is not affected as long as the spindle stays off.

## esptool fails or stops partway

Use `--no-stub --baud 115200`. With the default stub loader a 4 MB read failed at 86 % on this board. Without the stub, reads are slow (about 13 minutes) but reliable, and writes are verified by hash.

`erase-flash` is not available without the stub. That is why step 3 writes a blank image over the NVS partition instead.

## The serial port stops opening

Symptoms: `Invalid argument` or `Device not configured` when opening the port, usually after opening and closing it repeatedly, toggling DTR/RTS, or a spindle switch. Unplug the USB cable, wait a few seconds and plug it back in. On macOS the port name depends on the socket used.

Opening the port always reboots the controller. Plan each USB session as: open once, wait for the banner, do the work.

## SD card rejected, code 0x106

```text
[MSG:ERR: sdmmc_card_init failed code 0x106]
[MSG:ERR: filesystem error: SD card is inaccessible: ESP_ERR_NOT_SUPPORTED]
```

The card that came with the machine worked with the stock firmware and is refused by FluidNC, at 8 MHz and at 4 MHz alike. The card answers on the bus but rejects one of the initialisation commands of FluidNC's SD driver, which the stock firmware's driver did not use. The same error code is reported elsewhere on the command that enables CRC checking in SPI mode; which command fails here was not confirmed.

A different card was read at once, which confirms the reader and its pins. Use a recent card, 32 GB or less, formatted as **FAT32**.

The error shows up as soon as the web page opens, because the interface lists the card. Without a card it is harmless.

## Why `pulse_us` is 9 and not 10

The stock firmware used a 10 µs step pulse. FluidNC's RMT engine limits the step rate to `1000000 / (2 × pulse_us + dir_delay_us)`. X and Y at 4000 mm/min with 800 steps/mm need 53 333 steps/s. A 10 µs pulse allows 50 000 at best, and only 40 000 with the 5 µs direction delay tried first, so FluidNC rejects the configuration:

```text
[MSG:ERR: Axis X stepping rate 53333 steps/sec exceeds the maximum rate 40000]
```

With `pulse_us: 9` and `dir_delay_us: 0` the limit is 55 555. The pulse is 9 µs high and at least 9.75 µs low, against 10 / 8.75 on the stock firmware. If an axis loses steps at high speed, lower `max_rate_mm_per_min` and raise `pulse_us` again.

## The probe looked inverted on the stock firmware

The stock firmware reports `Pn:P` when GPIO 35 is high, which is the rest state, yet probing works. The vendor changed the probing cycle: it requires the input high at start and triggers when it goes low, and it ignores `$Probe/Invert`. Only the status display is wrong.

Electrically: idle high, contact low. Hence `pin: gpio.35:low` in FluidNC, where both the display and the probing are right.

## What you lose compared with the stock firmware

- Vendor additions: the `$BB` bounding-box command, the `$Motor/Lock` setting, the Wi-Fi reset commands.
- The ESP3D web UI with its preferences and macros.
- Work offsets and all settings, since the NVS is blanked.
- The stock firmware booted in `Idle`. This configuration boots in `Alarm` until homed; set `must_home: false` to change that.
- `M8`/`M9` did nothing on the stock firmware and still do nothing.

## The public XBoard E1.0 definition does not match

The stock firmware names its machine `XBoard E1.0`. That name comes from an open-hardware plotter controller, the [XBoard E series](https://oshwhub.com/Knight_Sin/esp32_grbl_3axis), whose firmware fork is [KnightSin/Grbl_Esp32](https://github.com/KnightSin/Grbl_Esp32). The Lunyee firmware clearly derives from that fork: it has the settings that only exist there (`Spindle/EM/*`, `Spindle/Servo/*`).

But Lunyee changed the pins and added closed code. Comparing the fork's `Machines/XBoard.h` with what the Lunyee binary does:

| Function | Public XBoard E1.0 | Lunyee 4040 Nova |
|---|---|---|
| X step / dir | 14 / 27 | 33 / 32 |
| Y step / dir | 26 / 25 | 26 / 25 |
| Z step / dir | 33 / 32 | 14 / 27 |
| Stepper disable | 12 | 13 |
| X / Y / Z limit | 36 / 39 / 34 | 34 / 39 / 36 |
| Spindle output | 17 | 4 (PWM) and 2 (relay) |

Using the public definition would swap X and Z and put enable, spindle and two limit inputs on the wrong pins.

Other findings from the binary:

- No Trinamic driver code is linked in. The `Current/Run`, `Microsteps` and `StallGuard` settings exist but do nothing; current and microstepping are set by the DIP switches only.
- Step and direction pins are driven as plain GPIOs. The I2S shift-register output is not used.
- A second UART (`Serial2`, default pins RX 16 / TX 17, 115200 baud) is opened, most likely for an offline controller.
- The SD card is initialised on the default SPI pins at 4 MHz.

## How the pinout was recovered

1. **Find the running application.** `flash_layout.py` reads the partition table and `otadata`. Here `otadata` is invalid and `app1` is empty, so `app0` runs; its checksum and SHA-256 are valid.
2. **Start from the boot messages.** The firmware prints lines such as `%s limit switch on pin %s`. `xtensa_xref.py strings` locates each string and the function that loads its address.
3. **Read the constants.** Those functions call `pinMode()` and `digitalWrite()`. `xtensa_xref.py callers` lists every call with the instructions just before it, which load the pin number. The limit pins sit in a small table read with `hex`; the motor pins are the arguments of four calls to the stepper constructor.
4. **Read the vendor additions.** The remaining `pinMode`/`digitalWrite` calls with constant arguments revealed the relay on GPIO 2 and the button on GPIO 22.
5. **Check on the machine.** Boot log, inputs pressed by hand, relay test, then under FluidNC: 5 mm moves and homing.

Addresses differ from one firmware build to another, so the tool gives you the method, not ready-made answers. Capstone does not decode two narrow Xtensa branches (`beqz.n`, `bnez.n`); the tool handles them itself.

One lesson worth passing on: the static analysis got the probe polarity wrong at first, because the status function and the probing cycle disagree in this firmware. The test on the machine caught it. Verify inputs by hand before trusting any reading of the code.
