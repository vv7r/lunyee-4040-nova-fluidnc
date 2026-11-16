# 5. Install FigUI

FluidNC ships with WebUI 2, a functional but dated interface. [FigUI](https://github.com/figamore/FigUI) is a modern replacement: a single `index.html.gz` file on the controller's internal filesystem. Swapping it is quick and reversible.

Validated here: **FigUI v1.4.3 on FluidNC v4.1.1**. FigUI documents no minimum FluidNC version; its release notes refer to FluidNC 4.0.3 and later. You can try it without a machine with its [live demo](https://figamore.github.io/FigUI/).

## 5.1 Mind the space

The internal filesystem of this 4 MB board is only 192 KB.

| File | Size |
|---|---|
| WebUI 2 `index.html.gz` (shipped with FluidNC 4.1.1) | 112 KB |
| FigUI v1.4.3 `index.html.gz` | 152 KB |
| `config.yaml` + `favicon.ico` | 8 KB |

So the old interface must be deleted before the new one is sent, and about **20 KB remain free** afterwards. That is enough for the configuration and macros. Keep G-code files on the SD card.

## 5.2 Install

Download `index.html.gz` from the [FigUI v1.4.3 release](https://github.com/figamore/FigUI/releases/tag/v1.4.3) and check its hash against [CHECKSUMS.md](../../CHECKSUMS.md).

Keep a copy of the current interface first: it is `wifi/index.html.gz` in the FluidNC package you downloaded in step 3.

Over USB:

```bash
python3 tools/fluidnc_serial.py upload index.html.gz index.html.gz --delete-first
```

The transfer takes about 35 seconds and must end with `Received 152129 bytes`. No restart is needed.

Or from the web UI: delete `index.html.gz` in the internal files, then upload the new one. If something goes wrong in between you have no web page, so the USB method is the safer one.

Reload the page with the cache bypassed (Cmd+Shift+R or Ctrl+F5).

## 5.3 Going back

Send the saved WebUI 2 file the same way:

```bash
python3 tools/fluidnc_serial.py upload path/to/wifi/index.html.gz index.html.gz --delete-first
```

## 5.4 Good to know

- **English only.** FigUI has no translations or language selector at the time of writing. WebUI 3 ([michmela44/ESP3D-WEBUI](https://github.com/michmela44/ESP3D-WEBUI)) is the alternative if you need another language: it has language packs, and its 108 KB file fits as well. It was not installed on the tested machine.
- **Plugins live on the SD card** (`/sd/plugins/`), not in the internal filesystem, so they do not eat into the 20 KB. You need a working SD card to use them.
- **FigUI can update FluidNC over the air** from its settings panel. Do not upgrade blindly: this configuration was validated on v4.1.1, and a failed over-the-air update means reflashing over USB.

Next: [notes and troubleshooting](06-notes-and-troubleshooting.md).
