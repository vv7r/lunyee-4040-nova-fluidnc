# 4. Mise en service

Faites ces vérifications dans l'ordre, la première fois que FluidNC tourne sur votre machine et après tout changement de configuration. Gardez la main sur l'interrupteur d'alimentation ou l'arrêt d'urgence pendant toute la séquence.

Vous pouvez envoyer les commandes depuis le terminal de l'interface web, ou par USB avec `tools/fluidnc_serial.py send '<commande>'`. Rappel : ouvrir le port USB redémarre la carte, ce qui la remet en `Alarm`.

## 4.1 Les entrées, moteurs à l'arrêt

```bash
python3 tools/fluidnc_serial.py watch 120
```

Appuyez sur un interrupteur X, un Y, un Z, puis mettez la pince du palpeur en contact avec la plaque.

Attendu : rien d'actif au repos ; `Pn:X`, `Pn:Y`, `Pn:Z` pendant l'appui ; `Pn:P` **au contact** (FluidNC affiche le palpeur dans le bon sens, contrairement au firmware d'origine).

Si le palpeur montre `P` au repos, retirez `:low` de `pin: gpio.35:low`.

## 4.2 Enable et sens des axes

La machine doit se trouver là où une prise d'origine l'a laissée, à 2 mm de ses interrupteurs. Vérifiez qu'il y a au moins 5 mm de libre sous l'outil.

Envoyez, une ligne à la fois, en regardant la machine :

```text
$X
$J=G91 G21 X5 F300
$J=G91 G21 Y5 F300
$J=G91 G21 Z-5 F300
```

Résultat correct : chaque axe se déplace d'environ 5 mm ; X et Y **s'éloignent** du coin de prise d'origine ; Z **descend**.

- **Un axe part dans le mauvais sens :** il va vers son interrupteur, à 2 mm, et la machine s'arrête d'elle-même en alarme. Ajoutez ou retirez `:low` sur le `direction_pin` de cet axe.
- **Rien ne bouge du tout :** le signal enable est inversé. Ajoutez `:low` à `shared_stepper_disable_pin`.

## 4.3 Prise d'origine

```text
$X
$HZ
$H
```

`$HZ` fait la prise d'origine de Z seul : il monte jusqu'à son interrupteur, se dégage de 2 mm, puis revient lentement (25 mm/min, comme sur le firmware d'origine). `$H` fait ensuite Z, puis X et Y ensemble. Attendez `[MSG:Homed:Z]` et `[MSG:Homed:XY]`, environ une minute en tout.

Si un interrupteur n'est pas vu, l'axe continue jusqu'à la butée mécanique. Surveillez les premières secondes de chaque phase.

Après la prise d'origine, FluidNC affiche la position machine 0 à la position dégagée. Le firmware d'origine y affichait probablement ±2 mm, donc les coordonnées machine peuvent être décalées de 2 mm : revoyez toute macro qui utilise `G53`.

## 4.4 Broche

Retirez l'outil. Comme la liaison USB peut décrocher quand le relais commute, envoyez toute la séquence d'un coup, pour que la carte détienne déjà la commande d'arrêt quand la broche démarre :

```text
$X
M3 S1000
G4 P3
M5
```

Par USB, l'option `--burst` envoie toutes les lignes en une seule écriture :

```bash
python3 tools/fluidnc_serial.py send --burst --wait 8 '$X' 'M3 S1000' 'G4 P3' 'M5'
```

Sur la machine testée la liaison a bien été perdue au moment où le relais s'est ouvert, et la broche s'est arrêtée d'elle-même comme prévu. Par Wi-Fi, depuis l'interface web, le problème ne se pose pas de la même façon.

Attendu : le relais colle, la broche tourne trois secondes, le relais relâche. Si elle ne s'arrête pas dans les cinq secondes, coupez l'alimentation.

## 4.5 Non couvert

Ces points n'ont pas été testés sur la machine de référence. Considérez-les comme inconnus :

- l'axe A (step 12, dir 15), dont le driver n'était raccordé à rien ;
- le second port série sur GPIO 16/17, laissé en commentaire dans `config.yaml` ;
- une sortie d'arrosage ou d'aspiration : le firmware d'origine n'en commande aucune.

Suite : [installer FigUI](05-figui.md).
