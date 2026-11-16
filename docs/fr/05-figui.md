# 5. Installer FigUI

FluidNC est livré avec WebUI 2, une interface fonctionnelle mais datée. [FigUI](https://github.com/figamore/FigUI) est une remplaçante moderne : un seul fichier `index.html.gz` dans la mémoire interne de la carte. Le changement est rapide et réversible.

Validé ici : **FigUI v1.4.3 sur FluidNC v4.1.1**. FigUI ne documente aucune version minimale de FluidNC ; ses notes de version parlent de FluidNC 4.0.3 et suivants. Vous pouvez l'essayer sans machine grâce à sa [démonstration en ligne](https://figamore.github.io/FigUI/).

## 5.1 Attention à la place

Le système de fichiers interne de cette carte 4 Mo ne fait que 192 Ko.

| Fichier | Taille |
|---|---|
| `index.html.gz` de WebUI 2 (livré avec FluidNC 4.1.1) | 112 Ko |
| `index.html.gz` de FigUI v1.4.3 | 152 Ko |
| `config.yaml` + `favicon.ico` | 8 Ko |

Il faut donc supprimer l'ancienne interface avant d'envoyer la nouvelle, et il reste ensuite environ **20 Ko libres**. C'est suffisant pour la configuration et les macros. Gardez les fichiers d'usinage sur la carte SD.

## 5.2 Installation

Téléchargez `index.html.gz` depuis la [version v1.4.3 de FigUI](https://github.com/figamore/FigUI/releases/tag/v1.4.3) et contrôlez son empreinte avec [CHECKSUMS.md](../../CHECKSUMS.md).

Mettez d'abord de côté l'interface actuelle : c'est le fichier `wifi/index.html.gz` du paquet FluidNC téléchargé à l'étape 3.

Par USB :

```bash
python3 tools/fluidnc_serial.py upload index.html.gz index.html.gz --delete-first
```

Le transfert prend environ 35 secondes et doit se terminer par `Received 152129 bytes`. Aucun redémarrage n'est nécessaire.

Ou depuis l'interface web : supprimez `index.html.gz` dans les fichiers internes, puis téléversez le nouveau. Si quelque chose se passe mal entre les deux vous n'avez plus de page web, donc la méthode USB est la plus sûre.

Rechargez la page en contournant le cache (Cmd+Maj+R ou Ctrl+F5).

## 5.3 Revenir en arrière

Renvoyez de la même façon le fichier WebUI 2 mis de côté :

```bash
python3 tools/fluidnc_serial.py upload chemin/vers/wifi/index.html.gz index.html.gz --delete-first
```

## 5.4 Bon à savoir

- **En anglais uniquement.** FigUI n'a ni traductions ni sélecteur de langue à l'heure où ces lignes sont écrites. WebUI 3 ([michmela44/ESP3D-WEBUI](https://github.com/michmela44/ESP3D-WEBUI)) est l'alternative si vous avez besoin d'une autre langue : elle dispose de packs de langue, dont le français, et son fichier de 108 Ko tient aussi. Elle n'a pas été installée sur la machine testée.
- **Les plugins sont rangés sur la carte SD** (`/sd/plugins/`), pas dans la mémoire interne : ils n'entament donc pas les 20 Ko. Il faut une carte SD fonctionnelle pour s'en servir.
- **FigUI peut mettre à jour FluidNC par le réseau** depuis son panneau de réglages. Ne mettez pas à jour à l'aveugle : cette configuration a été validée sur la v4.1.1, et une mise à jour par le réseau qui échoue oblige à reflasher par USB.

Suite : [notes et dépannage](06-notes-et-depannage.md).
