# Checksums / Empreintes

SHA-256 of the files used on the tested machine. No binary is distributed in this repository; download them from the official sources and compare.

Empreintes SHA-256 des fichiers utilisés sur la machine testée. Aucun binaire n'est distribué dans ce dépôt ; téléchargez-les depuis les sources officielles et comparez.

## Stock firmware / Firmware d'origine

Application image of the tested machine (Grbl_ESP32 1.3a, build 20231030), as extracted with `tools/flash_layout.py --extract-app`. A different value means a different firmware build.

| Item | SHA-256 |
|---|---|
| extracted `app0` image, 1 074 560 bytes | `d4656d752f662031bb7c40cf37869517af384e2cd8f539a9e7be7397071d6bff` |
| hash embedded at the end of the image | `c2c17a66005188b0e990561d9629191bb464e3365dfbcd08b60b96621e9b5d13` |

Full 4 MB dumps always differ between machines, and between two reads of the same machine, because of the settings partition. They also contain Wi-Fi credentials: do not share them.

## FluidNC v4.1.1

From <https://github.com/bdring/FluidNC/releases/tag/v4.1.1>

| File | SHA-256 |
|---|---|
| `fluidnc-v4.1.1-posix.zip` | `9012318d5c9f46319a92648b68ad7c2da4d11645280e9d5c4b290740111a31b0` |
| `wifi/bootloader.bin` | `5b1b0cd6bcbfd6de6d388652a46e9b6e341f36adb9127d1e654d21dadeae74bd` |
| `wifi/partitions.bin` | `1ae446228d79cf83a4b83de41c33d1e01dc21a3557149d7da90fbcbfc303311d` |
| `common/boot_app0.bin` | `f94c5d786a7a8fab06ac5d10e33bf37711a6697636dc037559ea19cc410a17f0` |
| `wifi/firmware.bin` | `5f7e2a397a856f66a7015402f2af46adf27180048d8e7ae30b962178d7f22c5d` |
| `wifi/littlefs.bin` | `e14799ebda7ac15c4751326281d93dc5af3d9b701eba9feb42f30c14b516a65d` |

## FigUI v1.4.3

From <https://github.com/figamore/FigUI/releases/tag/v1.4.3>

| File | SHA-256 |
|---|---|
| `index.html.gz`, 152 129 bytes | `5f8a81dd67f2b8c13c0694d88a3b815529f4cad591c903ca7ccbda1a12c7d5e8` |
