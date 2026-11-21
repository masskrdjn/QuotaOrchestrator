# QuotaOrchestrator pour Antigravity (Google Gemini)

[English](README.md) · [Vue d'ensemble du dépôt](../README.fr.md) · [Guide Codex](../plugins/quota-orchestrator/codex/README.fr.md) · [Guide Claude Code](../plugins/quota-orchestrator/claude/README.fr.md)

Routage sélectif multi-modèles pour les modèles **Google Gemini** dans **Google Antigravity** (App, CLI et IDE). Confie les lots substantiels et bornés à des sous-agents spécialisés et à des paliers Gemini moins coûteux, tout en conservant décisions, intégration et petites tâches locales à la racine.

> [!IMPORTANT]
> Version actuelle du plugin : **0.13.1**.

## Prérequis

- **Google Antigravity** (CLI `agy`, App ou IDE).
- **Python 3.11+** disponible dans le `PATH` sous la commande `python` (requis par le hook garde-fou `PreToolUse`).

## Installation

### Depuis GitHub

```bash
agy plugin install https://github.com/masskrdjn/QuotaOrchestrator
```

### Depuis un clone local

```bash
agy plugin validate .
agy plugin install .
agy plugin list
```

> **Note (dépôt multi-outils)** : `agy plugin validate .` signale un avertissement attendu sur le fichier racine `AGENTS.md` (destiné à Codex et aux contributeurs ; Antigravity charge `rules/AGENTS.md`). L'archive `.zip` de release passe `agy plugin validate --strict` sans aucun avertissement.

### Empaquetage et catalogue Marketplace

Le validateur `agy plugin validate ./.antigravity-plugin/marketplace.json` exige une URL `https://` pointant vers une archive `.zip` accompagnée de son empreinte `sha256`. Depuis la racine du dépôt, construisez et contrôlez le bundle déterministe avant de publier une release GitHub :

```bash
python scripts/build_antigravity_bundle.py
python scripts/build_antigravity_bundle.py --check
agy plugin validate --strict ./dist/quota-orchestrator-antigravity-0.13.1.zip
```

Joignez le fichier `dist/quota-orchestrator-antigravity-<version>.zip` à la release GitHub correspondante (`v<version>`), puis vérifiez le catalogue distant avec `agy plugin validate --strict ./.antigravity-plugin/marketplace.json`.

## Composants inclus

- **7 sous-agents natifs** (`agents/*.md`) pour `invoke_subagent` :
  - `runner` (`flash_lite`) — barrières de validation longues et matrices de tests indépendantes.
  - `scout` (`flash`) — exploration en lecture seule avec preuves `chemin:ligne`.
  - `researcher` (`flash`) — recherche documentaire multi-sources.
  - `builder-flash` (`flash`) — implémentation substantielle au contrat figé et testable.
  - `builder` (`pro`) — implémentation complexe demandant un jugement technique.
  - `strategist` (`pro`) — cadrage, découpage et spécification sans écriture.
  - `architect` (`pro`) — décisions d'architecture rares sur enveloppe bornée.
- **Règles de routage actives** (`rules/AGENTS.md`) — seuils de triage, interdiction même modèle/même effort et préservation des quotas.
- **Skill à la demande** (`skills/quota-orchestrator/SKILL.md`) — grille complète des modèles Google Gemini et de leurs efforts pour `swarm` et `agy --model` (`gemini-3.8-flash-*`, `gemini-4-hydrogen-*`, `gemini-4-neon-*`, `gemini-4-argon-*`).
- **Garde-fou `PreToolUse`** (`hooks.json` + `scripts/check_delegation.py`) — refuse les délégations redondantes au même modèle et même effort que la racine (`invoke_subagent` en `inherit` sur rôle générique, ou `swarm` `add` sans modèle ou avec un modèle identique à la racine). Requiert Python 3.11+ disponible en tant que `python`.

## Paliers de modèles Google Gemini

| Surface | Palier / Identifiants modèle | Usage typique |
|---|---|---|
| `invoke_subagent` | `flash_lite` | `runner` |
| `invoke_subagent` | `flash` | `scout`, `researcher`, `builder-flash` |
| `invoke_subagent` | `pro` | `builder`, `strategist`, `architect` |
| `swarm` / CLI | `gemini-3.8-flash-{low,medium,high}` | Validations rapides, triage volumineux (~0,75 / 3,75 $/MTok) |
| `swarm` / CLI | `gemini-4-hydrogen-{low,medium,high,xhigh}` | Exploration, recherche structurée, implémentation spécifiée (1,50 / 7,50 $/MTok) |
| `swarm` / CLI | `gemini-4-neon-{low,medium,high,xhigh}` | Racine par défaut, ingénierie complexe, intégration (3,00 / 15,00 $/MTok) |
| `swarm` / CLI | `gemini-4-argon-{low,medium,high}` | Raisonnement frontière rare et consultations `architect` (quota hebdomadaire dédié) |

## Politique de routage et limites de sécurité

- **Petites tâches locales à la racine** : modifications locales, vérifications directes, recherches à source unique et tâches dont le point d'entrée est connu n'amortissent pas la coordination.
- **Aucune délégation redondante** : déléguer au même modèle et même effort que la racine est interdit et bloqué par `scripts/check_delegation.py`.
- **Pas de polling** : après `invoke_subagent`, attendre la notification automatique de réveil.
- **Éditions parallèles isolées** : ne jamais laisser deux agents d'implémentation modifier les mêmes fichiers simultanément ; utiliser des périmètres disjoints ou `workspace: "share"` / `"branch"` dans `swarm`.
- **Rôles en lecture seule** : `architect` et `strategist` n'éditent rien et ne délèguent pas ; les sous-agents mandatés ne chargent pas le skill de routage et ne délèguent pas.
- **Ne pas contourner les permissions** : ne jamais lancer Antigravity sous `--dangerously-skip-permissions`.

## Validation

Depuis la racine du dépôt :

```bash
python -m unittest tests/antigravity_plugin_test.py
agy plugin validate .
python scripts/build_antigravity_bundle.py --check
```
