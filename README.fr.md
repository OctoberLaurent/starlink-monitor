# 🛰️ Starlink Incident Monitor

![CI](https://github.com/OctoberLaurent/starlink-monitor/actions/workflows/ci.yml/badge.svg)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 🌐 Langues / Languages / Idiomas: **Français** · [English](README.md) (défaut) · [Español](README.es.md)

Application web qui surveille en continu une parabole **Starlink** via son API
gRPC locale (`192.168.100.1:9200`), détecte les incidents et affiche un
**tableau de bord temps réel très stylé** (thème spatial, glassmorphisme,
graphiques live, carte d'obstruction polaire, journal d'incidents).

## Fonctionnalités

- **Polling live** de la parabole (1 sondage/seconde) via `grpcurl` (si la parabole est injoignable, bascule automatique en **mode démo** avec données simulées réalistes).
- **Détection d'incidents** :
  - 🛑 `outage` — parabole injoignable / déconnexion
  - 📉 `packet_loss` — taux de perte de paquets > 10 %
  - 📡 `latency` — latence > 150 ms
  - 🌲 `obstruction` — obstruction du signal
  - 🔻 `snr` — SNR sous le seuil de bruit
  - ⚠️ `alert` — alertes matérielles (moteurs bloqués, étranglement thermique, mât non vertical, ethernet lent…)
- **Persistance** des incidents dans `incidents.jsonl` (rechargés au redémarrage).
- **Interface stylée** : champ d'étoiles animé, nébuleuse, jauges néon, 2 graphiques temps réel (Chart.js), carte d'obstruction polaire SVG, timeline d'incidents avec niveaux de sévérité.
- **Multilingue 🇬🇧 🇫🇷 🇪🇸** : interface et incidents traduits en anglais, français et espagnol. L'anglais est la langue par défaut ; sélectionnez une autre langue via les drapeaux en haut à droite. Le choix est mémorisé.

## Démarrage rapide

```bash
cd /Users/laurentleplat/Web/starlink
./run.sh
```

Puis ouvrir **http://127.0.0.1:5050**

> Le port par défaut est `5050` (le `5000` est pris par AirPlay Receiver sur macOS).
> Pour changer : `PORT=8000 ./run.sh`

### Sans le script

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # runtime
.venv/bin/pip install -r requirements-dev.txt    # build + lint
.venv/bin/python app.py
```

### Qualité du code

```bash
.venv/bin/ruff check .          # lint
.venv/bin/black --check .       # formatage
.venv/bin/mypy                  # analyse statique des types (strict, équivalent PHPStan)
```

### Tests unitaires

```bash
.venv/bin/pytest                # 29 tests (détection, parsing, persistance, simulateur, routes)
```

Les tests couvrent : la détection d'incidents (ouverture/fermeture, sévérités),
le parsing de la réponse gRPC, la persistance JSONL, les bornes du simulateur
démo, et les routes Flask.

## Connexion à la vraie parabole

L'app appelle `grpcurl -plaintext 192.168.100.1:9200 SpaceX.API.Device.Device/Handle`.
Pour utiliser la vraie parabole :

1. Installez `grpcurl` : `brew install grpcurl` (ou `go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest`).
2. Soyez sur le réseau Wi-Fi de la parabole Starlink (l'API n'est accessible qu'en local).
3. Lancez l'app. Si la parabole répond, le mode démo se désactive automatiquement.

Variables d'environnement :

| Variable            | Défaut                | Rôle |
|--------------------|------------------------|------|
| `STARLINK_TARGET`  | `192.168.100.1:9200`   | Cible gRPC de la parabole |
| `STARLINK_POLL`    | `1.0`                  | Intervalle de sondage (s) |
| `STARLINK_DEMO`    | (auto)                | `1` pour forcer le mode démo |
| `STARLINK_GRPCURL` | (auto)                | Chemin du binaire grpcurl |
| `HOST`             | `127.0.0.1`            | Hôte d'écoute (localhost par défaut) |
| `PORT`             | `5050`                 | Port du serveur web |

## Architecture

```
app.py                 → backend Flask + thread de polling + détection d'incidents
  ├── _try_grpcurl()       interroge la parabole via grpcurl (JSON)
  ├── _parse_status()      convertit le JSON gRPC en Sample + infos parabole
  ├── DemoSimulator        données simulées réalistes (mode démo)
  ├── MonitorState         échantillons + incidents + détection (ouvert/fermé)
  └── /api/state, /api/incidents, /
templates/index.html   → dashboard stylé (starfield, jauges, charts, radar, timeline)
incidents.jsonl        → journal persistant des incidents
```

## Aperçu des seuils (configurables en haut de `app.py`)

| Paramètre          | Valeur | Incident déclenché |
|--------------------|--------|--------------------|
| `TH_DROPRATE`      | 0.10   | perte de paquets > 10 % |
| `TH_LATENCY`       | 150 ms | pic de latence |
| `TH_OBSTRUCTION`   | 5 %    | obstruction du signal |
| `ALERT_FIELDS`     | …      | alertes matérielles Starlink |

## Packaging macOS (.app + .dmg)

L'application peut être empaquetée en une app macOS native (fenêtre WebKit via
pywebview) puis en un installateur DMG. Le DMG n'est **pas** inclus dans le dépôt
(fichier de build, trop volumineux) : il se compile localement.

**Prérequis** : macOS (Apple Silicon de préférence), Xcode command line tools,
et `grpcurl` (bundlé dans l'app) :

```bash
xcode-select --install
brew install grpcurl
.venv/bin/pip install -r requirements-dev.txt   # pyinstaller, pillow, pywebview…
```

**Compilation** :

```bash
.venv/bin/python build_icon.py                              # 1. génère l'icône .icns
.venv/bin/python -m PyInstaller StarlinkMonitor.spec --noconfirm   # 2. build .app
./build_dmg.sh                                              # 3. build .dmg
```

Le résultat se trouve dans `dist/StarlinkMonitor.dmg`. Le binaire `grpcurl` et
les assets statiques (Chart.js) sont bundlés — l'app fonctionne hors-ligne.

> Le `StarlinkMonitor.spec` résout `grpcurl` via la variable `STARLINK_GRPCURL`
> ou le `PATH`. Pour forcer un binaire : `STARLINK_GRPCURL=/chemin/grpcurl`.
>
> L'app est signée *ad-hoc*. Au premier lancement, macOS peut bloquer l'ouverture :
> clic droit sur l'app → **Ouvrir** → confirmer.
> Build actuel : **arm64** (Apple Silicon). Pour Intel, rebuildez sur une machine x86_64.

## Notes

- L'API gRPC locale Starlink est non officielle et non supportée par SpaceX — susceptible de changer.
- Mode démo : s'active automatiquement si `grpcurl` est absent ou la parabole injoignable, pour que l'interface reste démontrable.
- **100 % hors-ligne** : Chart.js est bundlé en local (`static/`), le dashboard fonctionne même sans Internet.
- Le serveur web n'écoute que sur `127.0.0.1` par défaut (sécurité) ; surcharge via `HOST=0.0.0.0` pour un accès réseau.