# 2. Sauvegarder le firmware d'origine, et le restaurer

À faire avant toute chose. La sauvegarde est le seul moyen de revenir au firmware d'origine : aucune image d'origine n'est distribuée ici ni, à notre connaissance, par le constructeur.

## 2.1 Ce qu'il vous faut

- Python 3 et [esptool](https://docs.espressif.com/projects/esptool/) : `pip install esptool`
- Le câble USB de la machine, branché directement sur l'ordinateur.
- La broche à l'arrêt pendant toute l'opération.

Les commandes ci-dessous utilisent la syntaxe d'esptool 5 (`read-flash`, `write-flash`). Les versions plus anciennes utilisent des tirets bas (`read_flash`, `write_flash`).

Repérez votre port : `/dev/cu.usbserial-XXXX` sous macOS, `/dev/ttyUSB0` sous Linux, `COMx` sous Windows. Il est noté `PORT` dans la suite.

## 2.2 Lire toute la flash, deux fois

Sur la carte testée, le mode par défaut d'esptool échouait en cours de lecture. Désactiver le stub et rester à 115200 bauds a fonctionné :

```bash
esptool --chip esp32 --port PORT --baud 115200 --no-stub \
  read-flash --flash-size 4MB 0x0 0x400000 stock_read1.bin

esptool --chip esp32 --port PORT --baud 115200 --no-stub \
  read-flash --flash-size 4MB 0x0 0x400000 stock_read2.bin
```

Chaque lecture prend environ 13 minutes. Chaque fichier doit faire exactement 4 194 304 octets.

## 2.3 Contrôler la sauvegarde

```bash
python3 tools/flash_layout.py stock_read1.bin --compare stock_read2.bin
```

Ce qu'il faut regarder :

- `bootloader` et `app0` : `checksum ... OK` et `sha256 OK`.
- Les deux lectures diffèrent de quelques octets, **tous dans la partition `nvs`**. C'est normal : la pile Wi-Fi y réécrit deux entrées à chaque démarrage. Une différence ailleurs signale une mauvaise lecture : recommencez.
- Sur la machine testée, `otadata` est entièrement à zéro et `app1` est vide, donc le bootloader démarre `app0`.

Pour comparer votre firmware à celui de la machine testée, extrayez l'application et calculez son empreinte :

```bash
python3 tools/flash_layout.py stock_read1.bin --extract-app app0.bin
shasum -a 256 app0.bin
```

La valeur de la machine testée est dans [CHECKSUMS.md](../../CHECKSUMS.md). Une empreinte différente signifie un firmware différent : reprenez l'[étape 1](01-identifier-sa-carte.md) et vérifiez les broches avec soin.

## 2.4 À conserver, et à ne pas diffuser

- Notez les empreintes : `shasum -a 256 stock_read*.bin > SHA256SUMS.txt`
- Copiez les fichiers ailleurs que sur cet ordinateur.
- **Ne publiez jamais un dump complet.** Il contient le nom et le mot de passe de votre Wi-Fi en clair. `tools/nvs_dump.py` montre ce qui y est enregistré, mots de passe masqués.

## 2.5 Restaurer le firmware d'origine

Réécrivez l'image complète. La machine revient exactement à l'état de la sauvegarde, réglages et Wi-Fi compris.

```bash
shasum -a 256 -c SHA256SUMS.txt

esptool --chip esp32 --port PORT --baud 115200 --no-stub \
  write-flash --flash-mode keep --flash-freq keep --flash-size 4MB \
  0x0 stock_read1.bin
```

- esptool doit terminer par `Hash of data verified`.
- Si l'écriture est interrompue, relancez la commande. Le chargeur série se trouve dans la ROM de la puce et ne peut pas être effacé par un mauvais flashage ; FluidNC ne touche pas aux eFuses.

> Cette commande de restauration a été préparée et contrôlée par rapport à la sauvegarde, mais elle n'a pas été exécutée sur la machine testée, la migration s'étant bien passée. La même méthode d'écriture a servi avec succès à installer FluidNC.

Suite : [flasher FluidNC](03-flasher-fluidnc.md).
