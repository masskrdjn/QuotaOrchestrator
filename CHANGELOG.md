# Historique des évolutions

La version courante est définie dans le manifeste du plugin. Voir
[CONTRIBUTING.md](CONTRIBUTING.md) pour les règles de version et de maintenance.
Les fixtures conservent les anciennes sources ; cet historique ne reconstitue
pas les changements des versions précédentes.

## 0.15.0 — 2026-11-21

- Codex, Claude Code et Antigravity embarquent une délégation externe
  facultative vers les CLI Codex, Claude Code, Grok Build et Antigravity.
  Le script commun retourne la réponse ou l'erreur en JSON.
- Codex exécute une session éphémère en lecture seule et transmet son dernier
  message. Codex et Claude Code lisent la mission sur l'entrée standard.
  Grok lit un fichier temporaire UTF-8 sans BOM.
- Claude Code et Antigravity désactivent l'expansion des commandes slash
  pour les missions. Antigravity reçoit son propre délai d'arrêt.
- Sous Windows, le script résout les shims npm de Codex, Claude Code et Grok.
  Il distingue un CLI introuvable d'une erreur de lancement.

## 0.14.0 — 2026-11-21 (préparée localement)

- Ajout d'un hook `SessionStart` pour Google Antigravity (`hooks.json` et
  `scripts/check_updates.py`) vérifiant la disponibilité d'une version plus
  récente de QuotaOrchestrator sur GitHub avec un cache TTL de **2 heures**
  (timeout réseau de 2 s, fail-open hors-ligne, notification non bloquante via
  `systemMessage`, désactivable avec `QUOTA_ORCHESTRATOR_DISABLE_UPDATE_CHECK=1`).
- Intégration de `scripts/check_updates.py` dans l'archive déterministe
  Antigravity (`scripts/build_antigravity_bundle.py`) et ajout de la suite de
  tests hors-ligne `AntigravityUpdateCheckTest` dans
  `tests/antigravity_plugin_test.py`.

## 0.13.1 — 2026-11-21 (préparée localement)

- Refonte complète des README racine (`README.md`, `README.fr.md`) en un hub
  multi-plateformes équilibré couvrant Codex, Claude Code et Google Antigravity
  (tableau comparatif des plateformes, démarrages rapides dédiés, politique
  commune, correspondance des rôles, limites de sécurité et structure du dépôt).
- Extraction de la documentation détaillée spécifique à Codex dans
  `plugins/quota-orchestrator/codex/README.md` et `README.fr.md`, en symétrie
  avec `plugins/quota-orchestrator/claude/README*.md` et
  `.antigravity-plugin/README*.md`.
- Alignement des sous-README (`plugins/quota-orchestrator/README.md`,
  `.antigravity-plugin/README*.md`, `plugins/quota-orchestrator/claude/README*.md`) :
  liens croisés entre guides, version courante synchronisée (`0.13.1`) et ajout
  des sections politique de routage / validation dans le guide Antigravity.

## 0.13.0 — 2026-11-21 (préparée localement)

- Ajout du support natif Google Antigravity à la racine du dépôt
  (`.antigravity-plugin/plugin.json`, `agents/`, `rules/`, `skills/`,
  `hooks.json`, `assets/logo.png`, documentation bilingue `.antigravity-plugin/README*.md`),
  permettant l'installation directe par `agy plugin install https://github.com/masskrdjn/QuotaOrchestrator`
  ou `agy plugin install .` sans sous-chemin ni collision avec Codex ou Claude Code.
- Orchestration complète des modèles Google Gemini dans Antigravity :
  sept sous-agents natifs (`runner` sur `flash_lite` ; `scout`, `researcher` et
  `builder-flash` sur `flash` ; `builder`, `strategist` et `architect` sur
  `pro`), règles toujours actives (`rules/AGENTS.md`) et skill à la demande
  (`skills/quota-orchestrator/SKILL.md`) couvrant `gemini-3.8-flash-*`,
  `gemini-4-hydrogen-*`, `gemini-4-neon-*` et `gemini-4-argon-*` pour `swarm`
  et `agy --model`.
- Ajout d'un garde-fou `PreToolUse` (`hooks.json` et `scripts/check_delegation.py`)
  refusant les délégations redondantes au même modèle et même effort que la
  racine sur `invoke_subagent` et `swarm`, ainsi que la suite de tests
  `tests/antigravity_plugin_test.py`, le catalogue `.antigravity-plugin/marketplace.json`
  (`source.url` HTTPS + `source.sha256`) et le script d'empaquetage déterministe
  `scripts/build_antigravity_bundle.py`.

## 0.12.0 — 2026-11-20

- Codex conserve par défaut à la racine le travail qu’un sous-agent ferait
  avec le même modèle à un effort supérieur. Les exceptions reposent sur un
  besoin précis de qualité ou de délai, ou sur un gain de coût complet mesuré.
- Le triage distingue les lots spécifiés adaptés à Luna des lots qui demandent
  un builder Sol. Avant d’ajouter un deuxième builder Sol, il faut réévaluer
  le coût complet ou établir un besoin précis de qualité ou de délai.
- Les installateurs reconnaissent les consignes Codex d’origine de la 0.11.0
  pour les mettre à jour avec sauvegarde, en préservant les personnalisations.

## 0.11.0 — 2026-11-17 (préparée localement)

- Codex utilise désormais GPT-6.2 Sol pour `builder`, `strategist`,
  `researcher_complex` et `scout_complex`, et GPT-6.2 Astra pour `architect`.
  Les efforts restent respectivement `high`, `medium`, `xhigh`, `xhigh` et `low`.
- Les installateurs migrent les fichiers d’origine de la 0.10.2 avec sauvegarde
  et conservent les personnalisations. L’accès aux modèles suit le déploiement
  Codex annoncé par OpenAI. Les tarifs API sont documentés dans les deux README.

## 0.10.2 — 2026-11-09

- Installation depuis GitHub et migration depuis CodexSkills et ClaudeSkills.
- Nom d’affichage du catalogue Codex aligné sur QuotaOrchestrator.

## 0.10.1 — 2026-11-09 (préparée, commitée et poussée, non publiée)

- Mise à jour de la route dynamique Fable vers Fable 5.2, avec le prérequis
  Claude Code 2.1.321, les restrictions de disponibilité et de conservation
  des données.
- Tarifs standards Fable 5.2 documentés et ajoutés à l'estimateur ; les tarifs
  historiques de Fable 5.1 restent en place.
- Mode Fast et limites de l'estimation JSONL explicités ; contrôles de cohérence
  adaptés à la version et aux tarifs du modèle.

## 0.10.0 — 2026-11-06 (préparée localement, non publiée)

- Les deux catalogues distribuent le même paquet pour Codex et Claude Code.
  Les identifiants d’installation et les préfixes existants restent disponibles.
- Import des cinq rôles Claude Code, de sa skill, de ses deux hooks, de
  l’installateur par projet et des outils de mesure avec leurs tests.
- Séparation des chemins de découverte Codex et Claude Code ; même version
  dans les deux manifestes et guides d’installation et de migration à jour.
- Licence MIT (`LICENSE` à la racine et dans le paquet, champ `license` des deux
  manifestes) et icône du paquet Claude Code (`.claude-plugin/icon.png`).

## 0.9.1 — 2026-11-06 (préparée localement, non publiée)

- Ajout d’un démarrage rapide dans les README anglais et français, avec des liens
  directs vers les options d’installation et les consignes d’utilisation.

## 0.9.0 — 2026-10-26 (préparée localement, non publiée)

- Ajout de GPT-6.1 Terra avec `visual_operator` pour les missions visuelles et
  parcours d'interface bornés, et `writer` pour la rédaction et la synthèse
  de faits établis.
- Raisonnement `medium` par défaut, sélection d'efforts supérieurs selon la
  difficulté et leur application effective par le runtime. Sources officielles,
  tarifs datés et limites documentés ; aucun gain économique projet démontré.
- Routage et copies distribuées actualisés ; migration depuis `0.8.5` avec
  sauvegardes, conservation des personnalisations et tests de régression.
- Guide de maintenance, règle obligatoire de version dans les consignes du
  dépôt et contrôles de cohérence de distribution.
- La proposition intermédiaire `0.8.6`, non publiée, est regroupée dans cette
  évolution mineure. Publication et chargement des profils dans une nouvelle
  conversation restent distincts de la préparation locale.
