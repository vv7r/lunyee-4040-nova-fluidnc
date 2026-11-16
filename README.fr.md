# FluidNC + FigUI sur la Lunyee 4040 Nova

*[English version](README.md)*

Comment remplacer le firmware Grbl_ESP32 d'origine d'une fraiseuse CNC Lunyee 4040 Nova par [FluidNC](https://github.com/bdring/FluidNC) et l'interface web [FigUI](https://github.com/figamore/FigUI), **en gardant la carte de commande d'origine**.

Le brochage de cette carte n'est documenté nulle part. Il a été retrouvé en désassemblant le firmware d'origine, puis chaque signal qui pouvait être testé l'a été sur une vraie machine.

> **À lire avant tout**
>
> - Ce guide est un travail communautaire non officiel, sans lien avec Lunyee, FluidNC ni FigUI.
> - Tout a été testé sur **une seule machine**. Les cartes et les firmwares peuvent varier d'un lot à l'autre. Vérifiez que la vôtre correspond avant de flasher ([étape 1](docs/fr/01-identifier-sa-carte.md)).
> - Une broche ou une polarité fausse peut envoyer un axe en butée ou démarrer la broche. Vous agissez à vos risques.
> - Le firmware n'a aucune entrée d'arrêt d'urgence. Assurez-vous d'avoir un arrêt matériel qui coupe l'alimentation, et gardez la main dessus à chaque premier essai.
> - Faites une sauvegarde complète de la flash avant toute chose ([étape 2](docs/fr/02-sauvegarde-et-restauration.md)). C'est votre seule voie de retour.

## Est-ce bien votre machine ?

| Élément | Valeur sur la machine testée |
|---|---|
| Microcontrôleur | ESP32-D0WD-V3, flash de 4 Mo, adaptateur USB CH340 |
| Firmware d'origine | Grbl_ESP32 `1.3a`, build `20231030` (`$I` répond `[VER:1.3a.20231030:]`) |
| Interface d'origine | ESP3D WebUI 2.1b68 |
| Chaînes présentes dans la flash | `XBoard E1.0`, `VGRBL-4axis-4040-6.0-V1.0` |
| Drivers | quatre drivers externes step/dir réglés par DIP switches |
| Broche | relais marche/arrêt, vitesse manuelle |

Le firmware d'origine affiche cinq de ses broches au démarrage. Si votre journal de démarrage montre les mêmes numéros de GPIO, vous avez le même brochage : voir l'[étape 1](docs/fr/01-identifier-sa-carte.md).

## Brochage

| Fonction | GPIO | Remarques |
|---|---|---|
| X step / dir | 33 / 32 | direction inversée |
| Y step / dir | 26 / 25 | |
| Z step / dir | 14 / 27 | direction inversée |
| A step / dir | 12 / 15 | 4e driver, **non testé** |
| Enable des moteurs (commun) | 13 | niveau haut = désactivé |
| Fins de course X / Y / Z | 34 / 39 / 36 | actifs à l'état bas, les deux interrupteurs d'un axe sur la même entrée |
| Palpeur | 35 | repos à l'état haut, contact à l'état bas |
| Relais de broche | 2 | niveau haut = marche |
| PWM de broche | 4 | 10 kHz, rien de connu n'y est branché |
| Bouton Home | 22 | actif à l'état bas, pull-up interne |
| Carte SD SCK / MISO / MOSI / CS | 18 / 19 / 23 / 5 | |
| Second port série RX / TX | 16 / 17 | port de télécommande, **non testé** |
| Arrosage (M8/M9) | aucune | le firmware d'origine ne commande aucune sortie |

Ce n'est **pas** le brochage de la définition publique `XBoard E1.0`, bien que le firmware annonce ce nom. Voir les [notes](docs/fr/06-notes-et-depannage.md#la-définition-publique-xboard-e10-ne-correspond-pas).

## Ce qui a été vérifié

| Fonction | Résultat sous FluidNC v4.1.1 |
|---|---|
| Fins de course, palpeur, bouton Home | vérifié |
| Enable et sens des axes X, Y, Z | vérifié |
| Prise d'origine (`$HZ`, `$H`) | vérifié |
| Relais de broche marche/arrêt | vérifié |
| Lecteur de carte SD | vérifié, mais la carte livrée avec la machine a été refusée |
| Wi-Fi | vérifié |
| FigUI v1.4.3 | vérifié |
| Axe A, second port série, sortie d'arrosage | non testé |

## Étapes

1. [Identifier sa carte](docs/fr/01-identifier-sa-carte.md)
2. [Sauvegarder le firmware d'origine, et le restaurer](docs/fr/02-sauvegarde-et-restauration.md)
3. [Flasher FluidNC et envoyer la configuration](docs/fr/03-flasher-fluidnc.md)
4. [Mise en service : entrées, axes, prise d'origine, broche](docs/fr/04-mise-en-service.md)
5. [Installer FigUI](docs/fr/05-figui.md)
6. [Notes et dépannage](docs/fr/06-notes-et-depannage.md)

## Problèmes connus

- **La liaison USB décroche quand le relais de broche commute.** L'adaptateur CH340 se déconnecte un instant au démarrage ou à l'arrêt de la broche. N'usinez pas par USB, et ne comptez jamais sur l'USB pour arrêter la broche. Utilisez le Wi-Fi ou la carte SD.
- **esptool ne fonctionne qu'avec `--no-stub --baud 115200`** sur cette carte.
- **Ouvrir le port série redémarre la carte.**
- **La carte SD livrée avec la machine est refusée par FluidNC** (`sdmmc_card_init failed code 0x106`). Une carte récente en FAT32 fonctionne.
- L'impulsion de pas est de 9 µs au lieu des 10 µs d'origine, pour conserver la vitesse maximale d'origine.

Détails et contournements dans les [notes](docs/fr/06-notes-et-depannage.md).

## Contenu du dépôt

| Chemin | Rôle |
|---|---|
| [`config.yaml`](config.yaml) | configuration FluidNC validée sur la machine (commentaires en anglais) |
| [`docs/`](docs/) | le guide, en anglais et en français |
| [`tools/flash_layout.py`](tools/flash_layout.py) | examiner un dump : partitions, application active, comparaison de deux lectures, extraction de l'application |
| [`tools/nvs_dump.py`](tools/nvs_dump.py) | lister les réglages contenus dans un dump, mots de passe masqués |
| [`tools/xtensa_xref.py`](tools/xtensa_xref.py) | l'outil de désassemblage qui a servi à trouver les broches |
| [`tools/fluidnc_serial.py`](tools/fluidnc_serial.py) | journal de démarrage, état, surveillance des entrées, envoi de fichier par USB |
| [`CHECKSUMS.md`](CHECKSUMS.md) | empreintes SHA-256 des fichiers utilisés |

Aucun firmware n'est distribué ici. Un dump de flash contient le mot de passe de votre Wi-Fi : ne publiez jamais le vôtre.

## Crédits

- [FluidNC](https://github.com/bdring/FluidNC), par Bart Dring, Mitch Bradley et les contributeurs.
- [FigUI](https://github.com/figamore/FigUI), par figamore.
- Le firmware d'origine dérive de [KnightSin/Grbl_Esp32](https://github.com/KnightSin/Grbl_Esp32), lui-même un fork de [bdring/Grbl_Esp32](https://github.com/bdring/Grbl_Esp32).

## Licence

[MIT](LICENSE). Les corrections et les retours d'autres machines sont bienvenus : ouvrez une issue avec la réponse à `$I` et votre journal de démarrage.
