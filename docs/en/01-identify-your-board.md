# 1. Identify your board

The configuration in this repository is only valid if your controller is wired like the tested one. Lunyee may ship different boards or firmware builds under the same product name, so check before you flash. Nothing in this step changes the machine.

## 1.1 Firmware version

Connect over USB at 115200 baud (or use the Wi-Fi web UI terminal) and send `$I`.

Tested machine:

```text
[VER:1.3a.20231030:]
[OPT:PHSW]
```

## 1.2 Boot log: the firmware prints its own pins

This is the most useful check. Open the serial port and reset the controller; the stock firmware lists five pins while it starts. With the tools of this repository:

```bash
pip install pyserial
python3 tools/fluidnc_serial.py log
```

Opening the port reboots the board, so the log appears by itself. You should see exactly these GPIO numbers:

```text
[MSG:Laser spindle on Pin:GPIO(4), Enbl:None, Freq:10000Hz, Res:12bits Laser mode:Off]
[MSG:Flood coolant on pin None]
[MSG:X  Axis limit switch on pin GPIO(34)]
[MSG:Y  Axis limit switch on pin GPIO(39)]
[MSG:Z  Axis limit switch on pin GPIO(36)]
[MSG:Probe on pin GPIO(35)]
```

The vendor removed the motor messages, so step/dir pins are not printed. They are confirmed later, during commissioning, with 5 mm moves that are safe even if a direction is wrong.

**If any number differs, stop.** Your board is not the same; this `config.yaml` would be wrong for it. You can still use the method in [section 1.5](#15-if-your-board-differs) to find your own pinout.

## 1.3 Inputs, by hand

Still on the stock firmware, watch the inputs while you press each switch by hand. No motor moves.

```bash
python3 tools/fluidnc_serial.py watch 90
```

Wait about ten seconds after launching it, then press one X switch, one Y switch, one Z switch, and touch the probe clip to the plate.

Expected on the stock firmware:

- `Pn:X`, `Pn:Y`, `Pn:Z` appear while the matching switch is pressed. The first press raises `ALARM:1`; that is normal.
- **The probe display is inverted on this firmware**: it shows `Pn:P` at rest and the `P` disappears on contact. Probing itself works correctly.

## 1.4 Spindle relay and Home button

- Remove the tool. Send `M3 S0`, then `M5`. On the tested machine the relay closes on `M3 S0`, which shows it is driven by GPIO 2 and not by the PWM output. **Read the USB warning in the [notes](06-notes-and-troubleshooting.md#the-usb-link-drops-when-the-spindle-switches) first**: the `M5` may never arrive, be ready to cut power.
- Press the button on the control box. On the tested machine it starts a homing cycle (the firmware prints `Homing`).

## 1.5 If your board differs

The flash dump tells you everything the firmware does. After making a backup ([step 2](02-backup-and-restore.md)):

```bash
python3 tools/flash_layout.py dump.bin --extract-app app0.bin
pip install 'capstone>=6'
python3 tools/xtensa_xref.py app0.bin strings "limit switch on pin" "Probe on pin"
```

`xtensa_xref.py --help` summarises the method, and the [notes](06-notes-and-troubleshooting.md#how-the-pinout-was-recovered) describe it in more detail. Please open an issue with what you find, so this guide can cover more machines.

## Stock settings of the tested machine

For reference, in case you lose yours. Only `Z/MaxRate` was stored as a changed value; everything else is the firmware default.

| Setting | X | Y | Z | A |
|---|---:|---:|---:|---:|
| Steps/mm (`$100`–`$103`) | 800 | 800 | 800 | 800 |
| Max rate mm/min (`$110`–`$113`) | 4000 | 4000 | 800 | 2000 |
| Acceleration mm/s² (`$120`–`$123`) | 50 | 50 | 50 | 50 |
| Travel mm (`$130`–`$133`) | 400 | 400 | 130 | 400 |

```text
$0=10    step pulse, µs            $22=1    homing enabled
$1=25    step idle delay, ms       $23=3    homing direction invert: X, Y
$3=5     direction invert: X, Z    $24=25   homing feed, mm/min
$4=0     enable invert: off        $25=1000 homing seek, mm/min
$5=1     limit pins invert: on     $26=250  homing debounce, ms
$6=0     probe invert: off         $27=2    homing pull-off, mm
$20=0    soft limits: off          $30=1000 max spindle speed
$21=1    hard limits: on           $32=0    laser mode: off
Homing cycle 0: Z, cycle 1: XY     Spindle type: LASER, PWM 10000 Hz
```

Next: [back up the stock firmware](02-backup-and-restore.md).
