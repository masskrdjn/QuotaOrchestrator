---
name: quota-orchestrator
description: >-
  Protocole complet de routage multi-modèles Google Gemini dans Antigravity :
  choisir un modèle et un effort précis dans swarm/CLI (Gemini 3.8 Flash,
  Gemini 4 Hydrogen, Neon, Argon), arbitrer une escalade architect ou
  strategist, organiser une revue indépendante ou évaluer le coût complet.
  Ne pas charger pour une tâche locale ni dans un sous-agent déjà mandaté.
---

# QuotaOrchestrator — Routage Google Gemini pour Antigravity

## Objectif et priorités

1. **Préserver la qualité et la pertinence du résultat** — ne jamais abaisser
   les critères d'acceptation ni sauter une vérification pour rendre un modèle
   moins cher utilisable.
2. **Réduire le coût total en dollars API** (tokens d'entrée, cache et sortie ×
   tarif du modèle, racine + enfants + intégration + reprises) et **préserver
   les quotas** (notamment le quota hebdomadaire de `gemini-4-argon` et le quota
   partagé de `gemini-4-neon`).
3. **Réduire le délai**, sans multiplier les reprises.

Plus de tokens sur un palier moins cher reste un bon échange à qualité égale.
Sans mesure comparable sur des runs complets, annoncer un **gain attendu**,
jamais un gain démontré.

Ce skill est réservé à la racine. Un sous-agent déjà mandaté ne le charge pas,
ne refait pas le triage et ne redélègue pas.

---

## Deux surfaces de sélection dans Antigravity

### 1. Sous-agents natifs (`invoke_subagent` + `agents/*.md`)

`invoke_subagent` sélectionne un **palier abstrait** (`flash_lite`, `flash`,
`pro`, `inherit`). Les sept rôles fournis par le plugin fixent leur palier, leur
politique d'exécution et leur liste d'outils :

| Rôle | Palier (`model`) | Outils autorisés | Usage normal |
|---|---|---|---|
| `runner` | `flash_lite` | `run_command`, `manage_task`, `read_file`, `edit_file` | Barrière de validation longue (>= 3 commandes ou ~2 min) ou en parallèle d'un travail racine disjoint |
| `scout` | `flash` | `read_file` | Exploration en lecture seule (> ~8 fichiers ou 60 Ko), preuve `chemin:ligne` |
| `researcher` | `flash` | `search_web`, `read_file` | Recherche documentaire à plusieurs questions ou sources |
| `builder-flash` | `flash` | `read_file`, `edit_file`, `write_file`, `run_command`, `manage_task` | Implémentation substantielle au contrat figé et à validation fiable |
| `builder` | `pro` | `read_file`, `edit_file`, `write_file`, `run_command`, `manage_task` | Implémentation complexe demandant jugement technique ou intégration délicate |
| `strategist` | `pro` | `read_file`, `search_web` | Cadrage, découpage en lots disjoints et spécification sans écriture |
| `architect` | `pro` | `read_file` | Arbitrage structurant rare sur enveloppe déjà préparée |

### 2. Modèles et efforts exacts (`swarm` et CLI `agy --model`)

Pour un travail multi-pistes dans `swarm` (ou un lancement `agy --model`),
Antigravity expose les modèles Google avec leurs niveaux d'effort explicites
(vérifiés par `agy models` et `swarm(action="models", all=true)` le 2026-11-21) :

| Modèle Google | Identifiants Antigravity | Tarifs API indicatifs ($/1M entrée / sortie) | Pool de quota observé | Candidature projet |
|---|---|---|---|---|
| **Gemini 3.8 Flash** | `gemini-3.8-flash-{low,medium,high}` | ~0,75 / 3,75 *(tarif introductif)* | Pool 5 h partagé | Validations, triage volumineux, tâches rapides à faible ambiguïté |
| **Gemini 4 Hydrogen** | `gemini-4-hydrogen-{low,medium,high,xhigh}` | 1,50 / 7,50 *(cache lecture ~0,075)* | Pool 5 h partagé | Exploration, recherche structurée, implémentation bien spécifiée (`builder-flash`) |
| **Gemini 4 Neon** | `gemini-4-neon-{low,medium,high,xhigh}` | 3,00 / 15,00 *(cache lecture ~0,15)* | Pool 5 h partagé | Racine par défaut, ingénierie complexe, intégration multi-fichiers (`builder`, `strategist`) |
| **Gemini 4 Argon** | `gemini-4-argon-{low,medium,high}` | Palier frontière *(vérifier grille Vertex/AI Studio)* | **Pool hebdomadaire dédié** | Raisonnement profond longue portée, arbitrage `architect` rare |

> **Sources et date (2026-11-21)** : tarifs indicatifs issus de la documentation
> publique Google AI / Gemini API (Gemini 4 Hydrogen, Neon, Argon et Gemini 3.8
> Flash) et disponibilité runtime vérifiée sur `agy models`. Les niveaux d'effort
> ne sont pas équivalents entre familles : `hydrogen-xhigh` n'équivaut pas à
> `neon-medium`, ni `neon-xhigh` à `argon-low`. Toujours vérifier la disponibilité
> effective dans la session courante via `swarm(action="models", all=true)`.

---

## Grille capacité puis coût

Évaluer d'abord la **capacité** (ambiguïté du contrat, dépendances,
contradictions, difficulté de validation, coût d'une erreur), puis comparer le
**coût complet** (racine + enfants + reprises) parmi les candidats admissibles :

| Difficulté et preuves | Candidats `invoke_subagent` | Candidats `swarm` / CLI | Validation et signal de requalification |
|---|---|---|---|
| Contrat explicite, faible ambiguïté, validation directe | Rester à la racine ; `runner` (`flash_lite`) si validation longue | `gemini-3.8-flash-medium`, `gemini-4-hydrogen-low/medium` | Vérification directe. Petites tâches restent à la racine. |
| Lot multi-fichiers spécifié, jugement limité | `scout` / `researcher` / `builder-flash` (`flash`) | `gemini-4-hydrogen-medium/high` | Contrôler les interactions ; remonter toute ambiguïté décisive. |
| Interactions non triviales, invariants subtils, hypothèses concurrentes | `builder` / `strategist` (`pro`) ou racine | `gemini-4-neon-medium/high`, `gemini-4-hydrogen-xhigh` si capacité suffisante | Valider les invariants ; escalader si la capacité limite le résultat. |
| Preuves contradictoires, synthèse délicate, validation indirecte | Racine ou `strategist` (`pro`) | `gemini-4-neon-high/xhigh`, `gemini-4-argon-medium` | Préserver les réserves ; ne jamais transformer une hypothèse en fait. |
| Décision structurante coûteuse à corriger, contradiction persistante | `architect` (`pro`) | `gemini-4-argon-medium/high` | Enveloppe bornée, aucune exploration ni écriture par `architect`. |

---

## Règles anti-gaspillage et garde-fou `PreToolUse`

1. **Même modèle et même effort que la racine** : interdit, quel que soit le
   rôle. Le hook `PreToolUse` (`scripts/check_delegation.py`) bloque
   automatiquement :
   - `invoke_subagent` avec `Model="inherit"` (ou omis) vers un rôle qui
     n'abaisse ni ne spécialise le modèle (`self`, `research`, ou agent
     configuré en `inherit`) ;
   - `swarm` (`action="add"`) sans `model` explicite ou avec le même identifiant
     modèle/effort que la racine.
2. **Même modèle à effort supérieur** : rester à la racine par défaut, sauf
   besoin précis de qualité ou de délai annoncé explicitement.
3. **Parallélisme maîtrisé** : dans `swarm`, privilégier `workspace: "share"` ou
   `"branch"` pour les workers qui écrivent, afin que deux agents n'éditent
   jamais les mêmes fichiers. Ne pas lancer plusieurs workers `neon`/`argon`
   coûteux en parallèle sans gain démontré ou besoin de délai explicite.
4. **Revue indépendante** : jamais par défaut. Réservée à la sécurité, la perte
   de données, une migration irréversible, un contrat public ou une
   contradiction non résolue.

---

## Consultation `architect`

Avant d'invoquer `architect` (ou un worker `gemini-4-argon-*`), préparer une
enveloppe autosuffisante :
- objectif et contraintes non négociables ;
- extraits exacts (`chemin:ligne`) déjà collectés ;
- commandes exécutées et erreur essentielle ;
- hypothèse courante, alternatives envisagées et question précise à trancher.

`architect` ne fait ni exploration, ni commande, ni écriture, ni délégation.
S'il manque une donnée, il la demande dans « Mesures nécessaires » et la racine
la collecte via `scout` ou directement.
