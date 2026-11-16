# 3. Flasher FluidNC et envoyer la configuration

Prérequis : votre carte correspond ([étape 1](01-identifier-sa-carte.md)) et vous avez une sauvegarde contrôlée ([étape 2](02-sauvegarde-et-restauration.md)). Gardez la broche à l'arrêt pendant toute cette étape.

Ce guide a été validé avec **FluidNC v4.1.1**. Une version plus récente peut modifier des clés de configuration : lisez ses notes de version, et refaites les vérifications de mise en service après toute mise à jour.

## 3.1 Récupérer FluidNC

Téléchargez `fluidnc-v4.1.1-posix.zip` (macOS, Linux) ou le zip `win64` depuis les [versions de FluidNC](https://github.com/bdring/FluidNC/releases/tag/v4.1.1) et décompressez-le. Les empreintes sont dans [CHECKSUMS.md](../../CHECKSUMS.md).

La table de partitions de la version 4 Mo de FluidNC est identique à celle d'origine, et `firmware.bin` (1,83 Mo) tient dans l'emplacement applicatif de 1,92 Mo.

Les scripts d'installation du paquet utilisent le stub d'esptool à 230400 bauds, peu fiable sur cette carte. Utilisez plutôt les commandes manuelles ci-dessous.

## 3.2 Contrôler les fusibles de sécurité

L'installeur de FluidNC refuse de flasher une puce dont le démarrage sécurisé ou le chiffrement de la flash est activé. Faites le même contrôle :

```bash
esptool --chip esp32 --port PORT --baud 115200 --no-stub read-mem 0x3ff5a018
```

Attendu : `0x00000004` (machine testée) ou `0x00000000`. Toute autre valeur : arrêtez-vous et consultez le wiki de FluidNC.

## 3.3 Écrire le firmware

Depuis le dossier FluidNC décompressé. La première commande crée une image NVS vierge, car l'effacement complet de la puce n'est pas disponible sans le stub.

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

Comptez environ quatre minutes. Chacun des six blocs doit se terminer par `Hash of data verified`.

À ce stade FluidNC tourne avec sa machine par défaut « test drive » : aucune broche n'est affectée, donc rien ne peut bouger.

## 3.4 Envoyer `config.yaml`

Par USB, avec l'outil de ce dépôt :

```bash
pip install pyserial xmodem
python3 tools/fluidnc_serial.py upload config.yaml config.yaml --restart
```

Ou par Wi-Fi : rejoignez le réseau `FluidNC` (mot de passe `12345678`), ouvrez `http://192.168.0.1`, téléversez `config.yaml` dans le **système de fichiers local** (pas la carte SD) et redémarrez.

## 3.5 Lire le journal de démarrage

L'option `--restart` l'affiche ; sinon envoyez `$SS`. Il ne doit y avoir **aucune ligne commençant par `[MSG:ERR`**, et vous devez reconnaître le brochage :

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

La machine démarre en `Alarm` et réclame une prise d'origine. C'est le réglage `must_home: true` ; le firmware d'origine démarrait en `Idle`.

Une erreur `sdmmc_card_init failed` à l'ouverture de la page web ne concerne que la carte SD : voir les [notes](06-notes-et-depannage.md#carte-sd-refusée-code-0x106).

## 3.6 Wi-Fi

Dans les réglages de l'interface web, ou par le port série : `$Sta/SSID=<votre-reseau>`, `$Sta/Password=<votre-mot-de-passe>`, puis redémarrez. La carte ne gère que les réseaux 2,4 GHz. Elle est ensuite joignable à `http://fluidnc.local`.

Vos réglages d'origine, vos décalages d'origine pièce (G54...) et vos identifiants Wi-Fi ont disparu, puisque la NVS a été remise à zéro. Refaites votre zéro pièce avant le premier usinage.

Suite : [mise en service](04-mise-en-service.md).
