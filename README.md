# Scanner de Doublons — Dashboard Dash

Interface modernisée pour le pipeline de déduplication de fichiers.
Le pipeline original (4 scripts fournis) est utilisé **tel quel**, encapsulé
en fonctions, et s'exécute automatiquement en arrière-plan dès le lancement
de l'application.

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python3 app.py
```

L'application démarre sur `http://localhost:8050`. Dès le premier chargement
de la page, le pipeline complet se lance automatiquement en arrière-plan :

1. **Scan** — parcours récursif du dossier ciblé + hash MD5 de chaque fichier
2. **Nettoyage** — normalisation, validation des dates, feature engineering
3. **Détection** — identification des doublons exacts par (hash, taille)
4. **Enrichissement** — segmentation par dépôt / unité métier / propriétaire

Un écran de chargement animé (radar + LEDs d'étapes + console de logs en
direct) s'affiche pendant le traitement, puis le dashboard apparaît
automatiquement une fois terminé — sans aucune action de l'utilisateur.

## Configuration

Deux variables d'environnement permettent d'ajuster le scan sans toucher au
code :

```bash
# Dossier à scanner (par défaut : dossier personnel de l'utilisateur courant)
export DEDUP_SCAN_DIR=/chemin/vers/dossier

# Nombre de threads pour le scan parallèle (par défaut : 4)
export DEDUP_THREADS=8

python3 app.py
```

## Fonctionnalités

- **Thème clair / sombre** — bascule instantanée via le bouton en haut à
  droite, sans rechargement de page.
- **Multilingue FR / EN** — la langue du navigateur est détectée
  automatiquement au premier chargement (via l'en-tête HTTP
  `Accept-Language`). Bascule manuelle possible à tout moment.
- **Suppression réelle** — clique sur 🗑️ sur une ligne, ou coche plusieurs
  lignes et utilise "Supprimer la sélection". Une fenêtre de confirmation
  s'affiche avec le(s) chemin(s) concerné(s) avant toute action irréversible.
- **Archivage réel** — clique sur 📦, ou "Archiver la sélection". Les
  fichiers sont déplacés vers le dossier `archive_doublons/` (créé
  automatiquement à la racine du projet), avec un suffixe horodaté pour
  éviter toute collision de noms.
- **Export PDF** — génère un PDF des doublons actuellement filtrés.
- **Filtres** — par dépôt et par extension, mis à jour dynamiquement.

## Architecture du projet

```
dedup_app/
├── app.py                  # Application Dash (layout + callbacks)
├── i18n.py                 # Traductions FR/EN + détection de langue navigateur        
├── requirements.txt
├── assets/
│   ├── style.css           # Design system (thème clair/sombre, animations)
│   └── radar.js             # Injection du radar SVG animé (écran de chargement)
└── pipeline/
    ├── step1_scan.py        # Script 1 fourni, encapsulé en fonction
    ├── step2_clean.py       # Script 2 fourni, encapsulé en fonction
    ├── step3_detect.py      # Script 3 fourni, encapsulé en fonction
    ├── step4_enrich.py      # Script 4 fourni, encapsulé en fonction
    └── runner.py             # Orchestrateur : lance les 4 étapes dans un
                                thread d'arrière-plan, expose un état partagé
                                consulté par l'interface via polling.
```

La logique métier des 4 scripts originaux n'a **pas été modifiée** — seule
leur exécution a été encapsulée dans des fonctions afin de pouvoir les
piloter depuis l'interface (progression, logs, démarrage automatique).

## Notes

- Le serveur de développement Dash (`app.run`) n'est pas destiné à la
  production. Pour un déploiement réel, utilisez un serveur WSGI comme
  Gunicorn.
- L'application suppose un usage mono-utilisateur (un seul process scanne
  le disque du serveur). Pour un usage multi-utilisateurs, il faudrait
  isoler l'état du pipeline par session.
