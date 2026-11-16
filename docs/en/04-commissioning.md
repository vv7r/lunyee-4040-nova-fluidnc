# 4. Commissioning

Go through these checks in order, the first time FluidNC runs on your machine and after any configuration change. Keep a hand on the power switch or emergency stop the whole time.

You can send the commands from the web UI terminal or over USB with `tools/fluidnc_serial.py send '<command>'`. Remember that opening the USB port reboots the controller, which puts it back in `Alarm`.

## 4.1 Inputs, motors idle

```bash
python3 tools/fluidnc_serial.py watch 120
```

Press one X switch, one Y switch, one Z switch, then touch the probe clip to the plate.

Expected: nothing active at rest; `Pn:X`, `Pn:Y`, `Pn:Z` while pressed; `Pn:P` **on contact** (FluidNC shows the probe the right way round, unlike the stock firmware).

If the probe shows `P` at rest, remove `:low` from `pin: gpio.35:low`.

## 4.2 Enable and directions

The machine must be where a homing cycle left it, 2 mm away from its switches. Check there is at least 5 mm of free space below the tool.

Send, one at a time, watching the machine:

```text
$X
$J=G91 G21 X5 F300
$J=G91 G21 Y5 F300
$J=G91 G21 Z-5 F300
```

Correct result: each axis moves about 5 mm; X and Y move **away** from the corner they home to; Z moves **down**.

- **An axis moves the wrong way:** it travels toward its switch, 2 mm away, and the machine stops itself in alarm. Add or remove `:low` on that axis' `direction_pin`.
- **Nothing moves at all:** the enable signal is inverted. Add `:low` to `shared_stepper_disable_pin`.

## 4.3 Homing

```text
$X
$HZ
$H
```

`$HZ` homes Z alone: it rises to its switch, pulls off 2 mm, then approaches again slowly (25 mm/min, as on the stock firmware). `$H` then homes Z, followed by X and Y together. Expect `[MSG:Homed:Z]` and `[MSG:Homed:XY]`, about one minute in total.

If a switch is not seen, the axis keeps going until the mechanical stop. Watch the first seconds of each phase.

After homing FluidNC reports machine position 0 at the pulled-off position. The stock firmware probably reported ±2 mm there, so machine coordinates may be shifted by 2 mm: review any macro that uses `G53`.

## 4.4 Spindle

Remove the tool. Because the USB link can drop when the relay switches, send the whole sequence at once, so the controller already holds the stop command when the spindle starts:

```text
$X
M3 S1000
G4 P3
M5
```

Over USB, the `--burst` option sends all the lines in a single write:

```bash
python3 tools/fluidnc_serial.py send --burst --wait 8 '$X' 'M3 S1000' 'G4 P3' 'M5'
```

On the tested machine the link was indeed lost at the moment the relay opened, and the spindle stopped by itself as intended. Over Wi-Fi, from the web UI, the problem does not arise in the same way.

Expected: the relay closes, the spindle runs three seconds, the relay opens. If it does not stop within five seconds, cut the power.

## 4.5 Not covered

These were not tested on the reference machine. Treat them as unknown:

- the A axis (step 12, dir 15), with nothing connected to its driver;
- the second serial port on GPIO 16/17, left commented out in `config.yaml`;
- a coolant or dust-extraction output: the stock firmware drives none.

Next: [install FigUI](05-figui.md).
