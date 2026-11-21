# QuotaOrchestrator — Routage multi-modèles

[English](README.md)

Pour modifier ce dépôt : lire [CONTRIBUTING.md](CONTRIBUTING.md).
Les évolutions sont décrites dans [CHANGELOG.md](CHANGELOG.md).

> [!IMPORTANT]
> Version actuelle du plugin : **0.14.0**.
>
> Un seul dépôt, trois intégrations natives : **Codex** (OpenAI), **Claude Code** (Anthropic) et **Google Antigravity** (Google Gemini).

QuotaOrchestrator fournit des plugins de routage sélectif multi-modèles pour **Codex**, **Claude Code** et **Google Antigravity**. Il délègue les travaux substantiels et bien cadrés à des agents spécialisés sur des paliers moins coûteux ou mieux adaptés à la tâche, lorsque la délégation préserve la qualité tout en réduisant le coût total ou le délai. L'agent principal reste responsable du triage, des décisions, de l'intégration et de la communication avec l'utilisateur.

## Plateformes prises en charge

| Plateforme | Famille de modèles | Agents / profils | Hooks et garde-fous | Guide complet |
|---|---|---|---|---|
| **Codex** | OpenAI GPT-6 Luna, Sol (5.6 / 6 / 6.1 / 6.2), Terra 6.1, Astra 6.2 | 9 profils standard + 2 variantes `_complex` facultatives | Réconciliation `SessionStart` + garde-fou `PreToolUse` | [Guide Codex](plugins/quota-orchestrator/codex/README.fr.md) ([EN](plugins/quota-orchestrator/codex/README.md)) |
| **Claude Code** | Anthropic Haiku 5.5, Sonnet 5.5, Opus 5.5, Fable 5.2 | 5 agents spécialisés (`scout`, `researcher`, `runner`, `builder`, `architect`) | Injection des règles `SessionStart` + hook d'identité observée `PostToolUse` | [Guide Claude Code](plugins/quota-orchestrator/claude/README.fr.md) ([EN](plugins/quota-orchestrator/claude/README.md)) |
| **Google Antigravity** | Google Gemini 3.8 Flash, Gemini 4 Hydrogen, Neon, Argon | 7 sous-agents natifs (`invoke_subagent`) + routage `swarm` / CLI | Garde-fou `PreToolUse` + vérificateur de mises à jour `SessionStart` (TTL 2 h) | [Guide Antigravity](.antigravity-plugin/README.fr.md) ([EN](.antigravity-plugin/README.md)) |

## Démarrage rapide

Les trois plugins requièrent **Python 3.11+** disponible dans le `PATH` sous la commande `python` pour leurs hooks embarqués.

### Codex

```sh
codex plugin marketplace add masskrdjn/QuotaOrchestrator
codex plugin add quota-orchestrator@quota-orchestrator
```

1. Depuis un clone local, remplacez la première commande par `codex plugin marketplace add .`.
2. Quand Codex le demande, examinez puis approuvez les hooks `SessionStart` et `PreToolUse` pour configurer les neuf profils globaux standard et activer le garde-fou de délégation.
3. Ouvrez une nouvelle tâche Codex pour charger les profils.

Pour migrer depuis **CodexSkills** ou installer manuellement sans plugin, consultez le [guide Codex](plugins/quota-orchestrator/codex/README.fr.md#migrer-depuis-codexskills).

### Claude Code

```sh
claude plugin marketplace add masskrdjn/QuotaOrchestrator
claude plugin install quota-orchestrator@quota-orchestrator
```

1. Depuis un clone local, utilisez `claude plugin marketplace add ./` (ou `claude --plugin-dir ./plugins/quota-orchestrator` pour une session unique sans installation).
2. Démarrez une nouvelle session ou exécutez `/reload-plugins`.
3. Les composants du plugin sont préfixés `quota-orchestrator:<rôle>` et `quota-orchestrator:quota-orchestrator`. Sous Windows, le hook `SessionStart` requiert un shell POSIX (Git Bash).

Pour migrer depuis **ClaudeSkills**, installer par projet avec `install.py` ou mesurer vos sessions avec `extract_claude_jsonl.ps1`, consultez le [guide Claude Code](plugins/quota-orchestrator/claude/README.fr.md#installer-comme-plugin).

### Google Antigravity

```sh
agy plugin install https://github.com/masskrdjn/QuotaOrchestrator
```

1. Depuis un clone local, exécutez `agy plugin validate .` puis `agy plugin install .` (et `agy plugin list` pour vérifier).
2. Le plugin installe 7 sous-agents natifs (`agents/*.md`), les règles de routage toujours actives (`rules/AGENTS.md`), le skill à la demande `quota-orchestrator` (`skills/quota-orchestrator/SKILL.md`) et le garde-fou `PreToolUse` (`hooks.json`).
3. Utilisez `invoke_subagent` pour déléguer par palier (`flash_lite`, `flash`, `pro`) et `swarm` ou `agy --model` lorsqu'un choix exact de modèle et d'effort Google Gemini est nécessaire.

Pour empaqueter l'archive `.zip` de release ou valider le catalogue Antigravity, consultez le [guide Antigravity](.antigravity-plugin/README.fr.md).

## Politique de routage commune

Priorités partagées sur les trois plateformes, dans l'ordre :

1. **Préserver la qualité et la pertinence du résultat.**
2. **Réduire le coût total en dollars API** (tokens de chaque type × tarif du modèle, coordination racine, intégration et reprises comprises : plus de tokens sur un palier moins cher est un bon échange à qualité égale), tout en préservant les quotas limités des paliers frontière (Astra, Fable, Argon).
3. **Réduire le délai.**

Règles fondamentales :

- **Garder les petites tâches bornées à la racine.** Les modifications locales, consultations à source unique, vérifications directes et tâches dont le point d'entrée est connu n'amortissent pas le coût de coordination.
- **Même modèle et même effort → rester à la racine.** Cette règle prime sur tous les critères de délégation, y compris les revues indépendantes ; un autre nom de rôle ne suffit pas et les paramètres ne doivent pas être modifiés pour la contourner. Codex et Antigravity l'appliquent via des hooks `PreToolUse` synchrones.
- **Même modèle et effort supérieur → rester à la racine par défaut.** Ne déléguer que pour un besoin précis de qualité ou de délai, ou sur mesure comparable démontrant un coût total inférieur.
- **Chemin courant allégé.** Les consignes toujours actives (`AGENTS.md`, `CLAUDE.md`, `rules/AGENTS.md`) couvrent le triage quotidien et les rôles standard. Le skill `quota-orchestrator` n'est chargé qu'à la demande pour les escalades, choix hors profils, revues indépendantes ou comparaisons de coûts.
- **La délégation transfère l'exécution, pas la responsabilité.** L'agent principal rapproche les rapports, vérifie les preuves `chemin:ligne` ciblées (sans relire des fichiers entiers, ce qui annule l'économie) et ne transforme jamais une hypothèse d'un enfant en fait établi.
- **Mesurer avant d'affirmer une économie.** Sans exécutions complètes comparables, un choix de routage reste un gain attendu, pas démontré. Un run incomplet (`Complete = false`) est `non observable` et exclu des ratios et recommandations économiques.

## Correspondance des rôles par plateforme

| Rôle | Responsabilité | Codex (secours) | Claude Code | Google Antigravity (`invoke_subagent` / `swarm`) |
|---|---|---|---|---|
| **Principal** | Triage, décisions, intégration, petites tâches locales | Choisi par l'utilisateur | `opus` (`xhigh`) | Choisi par l'utilisateur (typiquement `gemini-4-neon-*`) |
| `runner` | Suites de validation longues, matrices de tests, lots mécaniques | `gpt-6-luna` (`high`) | `claude-haiku-5-5` (`medium`) | `flash_lite` / `gemini-3.8-flash-*` |
| `scout` | Exploration en lecture seule du code et des logs (`chemin:ligne`) | `gpt-6-luna` (`high`) | `sonnet` (`medium`) | `flash` / `gemini-4-hydrogen-*` |
| `researcher` | Recherche documentaire et web multi-sources | `gpt-6-luna` (`high`) | `sonnet` (`medium`) | `flash` / `gemini-4-hydrogen-*` |
| `builder_luna` / `builder-flash` | Implémentation substantielle entièrement spécifiée et testable | `gpt-6-luna` (`max`) | — (utiliser `builder`) | `flash` / `gemini-4-hydrogen-*` |
| `builder` | Implémentation exigeant conception, arbitrage ou intégration délicate | `gpt-6.2-sol` (`high`) | `sonnet` (`high`, escalade `opus`) | `pro` / `gemini-4-neon-*` |
| `strategist` | Cadrage complexe, découpage et spécification en lecture seule | `gpt-6.2-sol` (`medium`) | — | `pro` / `gemini-4-neon-*` |
| `architect` | Rares décisions d'architecture sur contexte déjà rassemblé | `gpt-6.2-astra` (`low`) | `opus` (`xhigh`) ou `fable` (sur accès confirmé) | `pro` / `gemini-4-argon-*` |
| `visual_operator` | Inspection visuelle et parcours d'interface bornés | `gpt-6.1-terra` (`medium`) | — | Sous-agent natif `browser` |
| `writer` | Rédaction ou réécriture substantielle à partir de faits établis | `gpt-6.1-terra` (`medium`) | — | — |
| `scout_complex` / `researcher_complex` | Exploration ou synthèse avancée quand le palier standard ne suffit pas | `gpt-6.2-sol` (`xhigh`) | — | `swarm` (`gemini-4-neon-*`) |

Pour les tables de tarifs détaillées, grilles de choix d'effort, conditions d'escalade et spécificités de chaque hôte, consultez les guides dédiés [Codex](plugins/quota-orchestrator/codex/README.fr.md), [Claude Code](plugins/quota-orchestrator/claude/README.fr.md) et [Antigravity](.antigravity-plugin/README.fr.md).

## Limites de sécurité

- **Ne jamais contourner les permissions ni le bac à sable :** ne pas exécuter sous `--yolo`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-skip-permissions` ni `bypassPermissions`.
- **Respecter les rôles en lecture seule :** `architect` n'explore pas, n'exécute aucune commande, n'édite rien et ne délègue pas ; `strategist` prépare le plan sans écrire ni lancer de sous-agents.
- **Pas de routage récursif :** les sous-agents restent dans leur mission, ne chargent pas le skill de routage et ne délèguent pas à leur tour.
- **Pas d'éditions concurrentes sur les mêmes fichiers :** attribuer des périmètres disjoints ou des espaces de travail isolés (`workspace: "share"` / `"branch"` dans `swarm` sous Antigravity).
- **Revues indépendantes conditionnelles :** jamais par défaut ; uniquement pour la sécurité, la perte de données, une migration irréversible, un contrat public, une contradiction non résolue ou un comportement critique sans test fiable.

## Structure du dépôt

```text
.
├── README.md, README.fr.md          # Vue d'ensemble multi-plateformes (EN / FR)
├── CONTRIBUTING.md, CHANGELOG.md    # Maintenance, versions et historique
├── AGENTS.md                        # Consignes hôte Codex (synchronisées dans templates/)
├── .agents/
│   ├── plugins/marketplace.json     # Catalogue marketplace local Codex
│   └── skills/quota-orchestrator/   # Skill local de routage Codex (FR)
├── .codex/
│   ├── config.toml                  # Configuration de secours Codex
│   └── agents/*.toml                # 11 profils Codex (9 standard + 2 facultatifs)
├── .claude-plugin/marketplace.json  # Catalogue marketplace Claude Code
├── .antigravity-plugin/
│   ├── plugin.json, marketplace.json # Manifeste et catalogue natifs Google Antigravity
│   └── README.md, README.fr.md      # Guide Antigravity (EN / FR)
├── agents/*.md                      # 7 sous-agents natifs Antigravity
├── rules/AGENTS.md                  # Règles de routage Antigravity toujours actives
├── skills/quota-orchestrator/       # Skill Antigravity Gemini à la demande
├── hooks.json, assets/logo.png      # Configuration du hook PreToolUse et icône Antigravity
├── scripts/
│   ├── check_delegation.py          # Garde-fou PreToolUse Antigravity
│   ├── check_updates.py             # Vérificateur de mises à jour SessionStart (TTL 2 h)
│   └── build_antigravity_bundle.py  # Empaqueteur .zip déterministe et vérificateur sha256
├── plugins/quota-orchestrator/      # Paquet plugin commun Codex et Claude Code
│   ├── README.md                    # Résumé du paquet commun
│   ├── .codex-plugin/plugin.json    # Manifeste plugin Codex
│   ├── .claude-plugin/plugin.json   # Manifeste plugin Claude Code
│   ├── codex/README.md, README.fr.md # Guide complet Codex (EN / FR)
│   ├── codex-skills/                # Skills du plugin Codex (routage + setup)
│   ├── hooks/                       # Réconciliation SessionStart et garde-fou PreToolUse Codex
│   ├── scripts/install.py           # Installateur Codex embarqué
│   ├── templates/                   # Copies synchronisées de AGENTS.md, .codex/, .agents/
│   ├── agents/*.md                  # 5 agents du plugin Claude Code
│   └── claude/                      # Guide Claude Code, skill, hooks, installateur, tests, outil JSONL
├── fixtures/release_*/              # Fichiers authentiques des anciennes versions (tests de migration)
└── tests/, test_install.py, test_reconcile.py
```

Cette organisation permet à Google Antigravity d'installer directement depuis l'URL du dépôt (`agy plugin install https://github.com/masskrdjn/QuotaOrchestrator`) sans sous-chemin, tout en gardant Codex et Claude Code isolés sous `plugins/quota-orchestrator/` sans aucune collision de composants.

## Validation

Python 3.11 ou supérieur est requis. Depuis la racine du dépôt :

```sh
python -m unittest discover -s tests -p '*_test.py'
python test_install.py
python test_reconcile.py
agy plugin validate .
python scripts/build_antigravity_bundle.py --check
```

Pour les validations Claude Code (`claude plugin validate`, `test_plugin.py`, `test_agent_identity.py`, `test_extract_claude_jsonl.py`), voir la [section de validation Claude Code](plugins/quota-orchestrator/claude/README.fr.md#mettre-à-jour-et-valider-une-livraison). Pour les tests natifs du garde-fou Codex (`CODEX_GUARD_TEST_BINARY`), voir la [section plugin Codex](plugins/quota-orchestrator/codex/README.fr.md#installation-comme-plugin).

## Licence

Distribué sous [licence MIT](LICENSE).
