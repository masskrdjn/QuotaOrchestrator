# Historique des évolutions

La version courante est définie dans le manifeste du plugin. Voir
[CONTRIBUTING.md](CONTRIBUTING.md) pour les règles de version et de maintenance.
Les fixtures conservent les anciennes sources ; cet historique ne reconstitue
pas les changements des versions précédentes.

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
