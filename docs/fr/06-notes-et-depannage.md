# 6. Notes et dépannage

## La liaison USB décroche quand la broche commute

Sur la machine testée, l'adaptateur USB CH340 se déconnecte un instant chaque fois que le relais de broche commute, au démarrage comme à l'arrêt. L'ordinateur voit le périphérique série disparaître puis revenir. C'est un parasite électrique du relais ou du moteur de broche, indépendant du firmware : cela s'est produit avec le firmware d'origine comme avec FluidNC.

Ce que cela implique :

- Une commande envoyée après le décrochage n'arrive jamais. Pendant les essais, un `M5` envoyé par USB a été perdu et la broche a continué de tourner jusqu'à la coupure de l'alimentation.
- N'usinez pas par USB. Utilisez le Wi-Fi ou la carte SD.
- Ne comptez jamais sur le logiciel pour arrêter la broche. Gardez un arrêt matériel à portée de main.
- Pour les essais par USB, envoyez marche, pause et arrêt en une seule écriture (`fluidnc_serial.py send --burst`).

Pistes possibles, aucune n'a été testée ici : une ferrite sur le câble USB, un câble plus court et blindé, un isolateur USB, un filtre antiparasite sur l'alimentation de la broche.

Le flashage n'est pas concerné tant que la broche reste à l'arrêt.

## esptool échoue ou s'arrête en cours de route

Utilisez `--no-stub --baud 115200`. Avec le chargeur par défaut (stub), une lecture de 4 Mo a échoué à 86 % sur cette carte. Sans le stub, les lectures sont lentes (environ 13 minutes) mais fiables, et les écritures sont vérifiées par empreinte.

`erase-flash` n'est pas disponible sans le stub. C'est pourquoi l'étape 3 écrit une image vierge sur la partition NVS.

## Le port série ne s'ouvre plus

Symptômes : `Invalid argument` ou `Device not configured` à l'ouverture du port, en général après l'avoir ouvert et fermé plusieurs fois de suite, après avoir manipulé DTR/RTS, ou après une commutation de la broche. Débranchez le câble USB, attendez quelques secondes et rebranchez-le. Sous macOS le nom du port dépend de la prise utilisée.

Ouvrir le port redémarre toujours la carte. Organisez chaque session USB ainsi : une seule ouverture, attente de la bannière, puis le travail.

## Carte SD refusée, code 0x106

```text
[MSG:ERR: sdmmc_card_init failed code 0x106]
[MSG:ERR: filesystem error: SD card is inaccessible: ESP_ERR_NOT_SUPPORTED]
```

La carte livrée avec la machine fonctionnait avec le firmware d'origine et est refusée par FluidNC, à 8 MHz comme à 4 MHz. Elle répond sur le bus mais rejette l'une des commandes d'initialisation du pilote SD de FluidNC, que le pilote du firmware d'origine n'utilisait pas. Le même code d'erreur est signalé ailleurs sur la commande qui active le contrôle CRC en mode SPI ; la commande qui échoue ici n'a pas été confirmée.

Une autre carte a été lue immédiatement, ce qui confirme le lecteur et ses broches. Utilisez une carte récente, de 32 Go au plus, formatée en **FAT32**.

L'erreur apparaît dès l'ouverture de la page web, parce que l'interface liste le contenu de la carte. Sans carte, elle est sans conséquence.

## Pourquoi `pulse_us` vaut 9 et non 10

Le firmware d'origine utilisait une impulsion de pas de 10 µs. Le moteur de pas RMT de FluidNC limite la cadence à `1000000 / (2 × pulse_us + dir_delay_us)`. X et Y à 4000 mm/min avec 800 pas/mm demandent 53 333 pas/s. Une impulsion de 10 µs autorise 50 000 au mieux, et seulement 40 000 avec le délai de direction de 5 µs essayé au départ ; FluidNC refuse alors la configuration :

```text
[MSG:ERR: Axis X stepping rate 53333 steps/sec exceeds the maximum rate 40000]
```

Avec `pulse_us: 9` et `dir_delay_us: 0` la limite passe à 55 555. L'impulsion dure 9 µs à l'état haut et au moins 9,75 µs à l'état bas, contre 10 / 8,75 sur le firmware d'origine. Si un axe perd des pas à grande vitesse, baissez `max_rate_mm_per_min` et remontez `pulse_us`.

## Le palpeur semblait inversé sur le firmware d'origine

Le firmware d'origine affiche `Pn:P` quand GPIO 35 est à l'état haut, c'est-à-dire au repos, et pourtant le palpage fonctionne. Le constructeur a modifié le cycle de palpage : il exige l'entrée à l'état haut au départ et se déclenche quand elle passe à l'état bas, et il ignore `$Probe/Invert`. Seul l'affichage de l'état est faux.

Électriquement : repos à l'état haut, contact à l'état bas. D'où `pin: gpio.35:low` sous FluidNC, où l'affichage comme le palpage sont corrects.

## Ce que l'on perd par rapport au firmware d'origine

- Les ajouts du constructeur : la commande de cadrage `$BB`, le réglage `$Motor/Lock`, les commandes de réinitialisation du Wi-Fi.
- L'interface ESP3D, avec ses préférences et ses macros.
- Les décalages d'origine pièce et tous les réglages, puisque la NVS est remise à zéro.
- Le firmware d'origine démarrait en `Idle`. Cette configuration démarre en `Alarm` tant que la prise d'origine n'est pas faite ; mettez `must_home: false` pour changer cela.
- `M8`/`M9` ne faisaient rien sur le firmware d'origine et ne font toujours rien.

## La définition publique XBoard E1.0 ne correspond pas

Le firmware d'origine nomme sa machine `XBoard E1.0`. Ce nom vient d'un contrôleur de traceur en matériel libre, la [série XBoard E](https://oshwhub.com/Knight_Sin/esp32_grbl_3axis), dont le fork du firmware est [KnightSin/Grbl_Esp32](https://github.com/KnightSin/Grbl_Esp32). Le firmware Lunyee dérive clairement de ce fork : on y trouve des réglages qui n'existent que là (`Spindle/EM/*`, `Spindle/Servo/*`).

Mais Lunyee a changé les broches et ajouté du code fermé. Comparaison entre le fichier `Machines/XBoard.h` du fork et ce que fait le binaire Lunyee :

| Fonction | XBoard E1.0 public | Lunyee 4040 Nova |
|---|---|---|
| X step / dir | 14 / 27 | 33 / 32 |
| Y step / dir | 26 / 25 | 26 / 25 |
| Z step / dir | 33 / 32 | 14 / 27 |
| Désactivation des moteurs | 12 | 13 |
| Fins de course X / Y / Z | 36 / 39 / 34 | 34 / 39 / 36 |
| Sortie broche | 17 | 4 (PWM) et 2 (relais) |

Reprendre la définition publique permuterait X et Z et placerait l'enable, la broche et deux entrées de fin de course sur de mauvaises broches.

Autres constats tirés du binaire :

- Aucun code de driver Trinamic n'est présent. Les réglages `Current/Run`, `Microsteps` et `StallGuard` existent mais ne font rien ; courant et micropas se règlent uniquement par les DIP switches.
- Les broches step et direction sont pilotées en GPIO directs. La sortie par registre à décalage I2S n'est pas utilisée.
- Un second port série (`Serial2`, broches par défaut RX 16 / TX 17, 115200 bauds) est ouvert, très probablement pour une télécommande hors ligne.
- La carte SD est initialisée sur les broches SPI par défaut, à 4 MHz.

## Comment le brochage a été retrouvé

1. **Trouver l'application active.** `flash_layout.py` lit la table de partitions et `otadata`. Ici `otadata` est invalide et `app1` est vide, donc c'est `app0` qui tourne ; son checksum et son SHA-256 sont valides.
2. **Partir des messages de démarrage.** Le firmware affiche des lignes comme `%s limit switch on pin %s`. `xtensa_xref.py strings` localise chaque chaîne et la fonction qui charge son adresse.
3. **Lire les constantes.** Ces fonctions appellent `pinMode()` et `digitalWrite()`. `xtensa_xref.py callers` liste chaque appel avec les instructions qui le précèdent, lesquelles chargent le numéro de broche. Les broches de fin de course sont dans une petite table lue avec `hex` ; celles des moteurs sont les arguments de quatre appels au constructeur du moteur pas à pas.
4. **Lire les ajouts du constructeur.** Les appels restants à `pinMode`/`digitalWrite` avec des arguments constants ont révélé le relais sur GPIO 2 et le bouton sur GPIO 22.
5. **Vérifier sur la machine.** Journal de démarrage, entrées actionnées à la main, test du relais, puis sous FluidNC : déplacements de 5 mm et prise d'origine.

Les adresses changent d'un firmware à l'autre : l'outil vous donne la méthode, pas des réponses toutes faites. Capstone ne décode pas deux branchements courts de l'Xtensa (`beqz.n`, `bnez.n`) ; l'outil les traite lui-même.

Une leçon à retenir : l'analyse statique s'est d'abord trompée sur la polarité du palpeur, parce que la fonction d'état et le cycle de palpage ne sont pas cohérents dans ce firmware. C'est l'essai sur la machine qui l'a révélé. Vérifiez les entrées à la main avant de vous fier à une lecture du code.
