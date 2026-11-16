# 1. Identifier sa carte

La configuration de ce dépôt n'est valable que si votre carte est câblée comme celle qui a été testée. Lunyee peut livrer des cartes ou des firmwares différents sous le même nom de produit : vérifiez avant de flasher. Rien dans cette étape ne modifie la machine.

## 1.1 Version du firmware

Connectez-vous par USB à 115200 bauds (ou par le terminal de l'interface web) et envoyez `$I`.

Machine testée :

```text
[VER:1.3a.20231030:]
[OPT:PHSW]
```

## 1.2 Journal de démarrage : le firmware affiche lui-même ses broches

C'est la vérification la plus utile. Ouvrez le port série et redémarrez la carte ; le firmware d'origine liste cinq broches pendant son démarrage. Avec les outils de ce dépôt :

```bash
pip install pyserial
python3 tools/fluidnc_serial.py log
```

Ouvrir le port redémarre la carte, donc le journal s'affiche tout seul. Vous devez voir exactement ces numéros de GPIO :

```text
[MSG:Laser spindle on Pin:GPIO(4), Enbl:None, Freq:10000Hz, Res:12bits Laser mode:Off]
[MSG:Flood coolant on pin None]
[MSG:X  Axis limit switch on pin GPIO(34)]
[MSG:Y  Axis limit switch on pin GPIO(39)]
[MSG:Z  Axis limit switch on pin GPIO(36)]
[MSG:Probe on pin GPIO(35)]
```

Le constructeur a retiré les messages des moteurs, donc les broches step/dir n'y figurent pas. Elles sont confirmées plus tard, à la mise en service, par des déplacements de 5 mm sans danger même si un sens est faux.

**Si un seul numéro diffère, arrêtez-vous.** Votre carte n'est pas la même ; ce `config.yaml` serait faux pour elle. Vous pouvez tout de même utiliser la méthode de la [section 1.5](#15-si-votre-carte-diffère) pour trouver votre propre brochage.

## 1.3 Les entrées, à la main

Toujours sur le firmware d'origine, surveillez les entrées en appuyant à la main sur chaque interrupteur. Aucun moteur ne bouge.

```bash
python3 tools/fluidnc_serial.py watch 90
```

Attendez une dizaine de secondes après le lancement, puis appuyez sur un interrupteur X, un Y, un Z, et mettez la pince du palpeur en contact avec la plaque.

Résultat attendu sur le firmware d'origine :

- `Pn:X`, `Pn:Y`, `Pn:Z` apparaissent tant que l'interrupteur correspondant est enfoncé. Le premier appui déclenche `ALARM:1` ; c'est normal.
- **L'affichage du palpeur est inversé sur ce firmware** : il montre `Pn:P` au repos, et le `P` disparaît au contact. Le palpage lui-même fonctionne correctement.

## 1.4 Relais de broche et bouton Home

- Retirez l'outil. Envoyez `M3 S0`, puis `M5`. Sur la machine testée le relais colle sur `M3 S0`, ce qui montre qu'il est commandé par GPIO 2 et non par la sortie PWM. **Lisez d'abord l'avertissement USB dans les [notes](06-notes-et-depannage.md#la-liaison-usb-décroche-quand-la-broche-commute)** : le `M5` peut ne jamais arriver, soyez prêt à couper l'alimentation.
- Appuyez sur le bouton du boîtier de commande. Sur la machine testée il lance une prise d'origine (le firmware affiche `Homing`).

## 1.5 Si votre carte diffère

Le dump de la flash contient tout ce que fait le firmware. Après avoir fait une sauvegarde ([étape 2](02-sauvegarde-et-restauration.md)) :

```bash
python3 tools/flash_layout.py dump.bin --extract-app app0.bin
pip install 'capstone>=6'
python3 tools/xtensa_xref.py app0.bin strings "limit switch on pin" "Probe on pin"
```

`xtensa_xref.py --help` résume la méthode, et les [notes](06-notes-et-depannage.md#comment-le-brochage-a-été-retrouvé) la détaillent. Ouvrez une issue avec ce que vous trouvez, pour que ce guide couvre davantage de machines.

## Réglages d'origine de la machine testée

Pour référence, au cas où vous perdriez les vôtres. Seul `Z/MaxRate` était enregistré comme valeur modifiée ; tout le reste est la valeur par défaut du firmware.

| Réglage | X | Y | Z | A |
|---|---:|---:|---:|---:|
| Pas/mm (`$100`–`$103`) | 800 | 800 | 800 | 800 |
| Vitesse maxi mm/min (`$110`–`$113`) | 4000 | 4000 | 800 | 2000 |
| Accélération mm/s² (`$120`–`$123`) | 50 | 50 | 50 | 50 |
| Course mm (`$130`–`$133`) | 400 | 400 | 130 | 400 |

```text
$0=10    impulsion de pas, µs         $22=1    prise d'origine activée
$1=25    délai de repos, ms           $23=3    sens de prise d'origine inversé : X, Y
$3=5     direction inversée : X, Z    $24=25   avance de prise d'origine, mm/min
$4=0     enable inversé : non         $25=1000 recherche de prise d'origine, mm/min
$5=1     fins de course inversés : oui  $26=250  anti-rebond, ms
$6=0     palpeur inversé : non        $27=2    dégagement, mm
$20=0    limites logicielles : non    $30=1000 vitesse de broche maxi
$21=1    limites matérielles : oui    $32=0    mode laser : non
Cycle de prise d'origine 0 : Z, cycle 1 : XY     Type de broche : LASER, PWM 10000 Hz
```

Suite : [sauvegarder le firmware d'origine](02-sauvegarde-et-restauration.md).
