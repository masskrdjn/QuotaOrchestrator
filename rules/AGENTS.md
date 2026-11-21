# Instructions projet — routage sélectif multi-modèles (Antigravity / Google Gemini)

Priorités : préserver la qualité et la pertinence du résultat, puis réduire le
coût total, puis le délai, tout en préservant le quota des paliers supérieurs
(notamment `gemini-4-argon` au quota hebdomadaire et `gemini-4-neon`). Le coût
s'entend en dollars API (tokens de chaque type × tarif du modèle), pas en nombre
de tokens : plus de tokens sur un palier moins cher est un bon échange à qualité
égale. Le modèle racine choisi par l'utilisateur reste prioritaire, comme ses
instructions.

## Triage, avant toute exploration

Une demande locale précise (renommage, modification, validation ou lecture
nommés) se fait directement à la racine, sans inventaire ni délégation.
Reste à la racine, sans charger le skill : petite tâche locale, lot
déterministe borné, implémentation locale au contrat explicite, consultation
documentaire à une seule source, recherche de cause dont le point d'entrée est
connu et vérification directe.

Le travail confié doit amortir la coordination de chaque enfant, y compris les
requêtes racine à tarif complet.

**Même modèle et même effort (ou `inherit` sur rôle générique) : rester à la
racine.** Cette règle prime sur tout routage et est contrôlée par le hook
`PreToolUse` (`scripts/check_delegation.py`).

**Même modèle et effort supérieur** : garder le travail à la racine par défaut.
Déléguer seulement pour un besoin précis de qualité ou de délai, ou sur mesure
comparable montrant un gain de coût complet.

## Rôles Antigravity (`invoke_subagent` et `swarm`)

Antigravity expose deux mécanismes complémentaires :
- **`invoke_subagent`** avec les agents du plugin (`agents/*.md`), qui sélectionnent
  un palier abstrait (`flash_lite`, `flash`, `pro`) :
  - `runner` (`flash_lite`) : barrière de validation longue ou matrice de
    commandes indépendante.
  - `scout` (`flash`) : exploration en lecture seule dépassant ~8 fichiers ou
    60 Ko, réponse courte `chemin:ligne`.
  - `researcher` (`flash`) : toute recherche documentaire à plusieurs questions
    ou sources (décidé avant la première recherche).
  - `builder-flash` (`flash`) : implémentation substantielle entièrement
    spécifiée et testable de façon fiable.
  - `builder` (`pro`) : implémentation demandant un jugement technique ou une
    intégration délicate.
  - `strategist` (`pro`) : cadrage et spécification d'un lot complexe sans écriture.
  - `architect` (`pro`) : arbitrage structurant rare sur contexte déjà rassemblé.
- **`swarm`** (et CLI `agy --model`) lorsque le choix précis du modèle Google et
  de son effort est requis :
  - `gemini-3.8-flash-{low,medium,high}` (~0,75 / 3,75 $/MTok) : exécution rapide,
    validations, triage volumineux.
  - `gemini-4-hydrogen-{low,medium,high,xhigh}` (1,50 / 7,50 $/MTok) : code
    courant bien spécifié, exploration, recherche structurée.
  - `gemini-4-neon-{low,medium,high,xhigh}` (3,00 / 15,00 $/MTok) : ingénierie
    complexe, raisonnement rapide, intégration multi-fichiers.
  - `gemini-4-argon-{low,medium,high}` (quota hebdomadaire dédié) : raisonnement
    profond de frontière, décisions d'architecture rares.

## Protocole de délégation

1. Avant création, une ligne de triage : rôle, modèle/palier, livrable exclusif,
   critère d'arrêt, raison économique ou de capacité. À défaut, rester à la racine.
2. Prompt autonome et concis : question, périmètre, preuve d'arrêt, format de
   retour, faits établis séparés des hypothèses et inconnues.
3. Après lancement (`invoke_subagent`), ne pas poller : attendre la notification
   automatique. Le périmètre confié est réservé à l'enfant.
4. Acceptation : lire le rapport et ne vérifier que les preuves `chemin:ligne`
   citées. Ne jamais promouvoir une hypothèse d'un enfant en fait.

## Le skill `quota-orchestrator`

Le charger uniquement pour arbitrer un modèle/effort précis dans `swarm`, une
escalade vers `gemini-4-argon`, une consultation `architect`, une revue
indépendante ou une comparaison de coûts. Jamais pour une tâche locale ni pour
un sous-agent déjà mandaté.

## Règles permanentes

- Ne pas laisser deux agents d'implémentation éditer les mêmes fichiers (utiliser
  `workspace: "share"` ou `"branch"`, ou des périmètres disjoints).
- Revue indépendante : jamais par défaut ; ciblée uniquement pour la sécurité,
  la perte de données, une migration irréversible, un contrat public ou une
  contradiction non résolue.
- Un sous-agent déjà mandaté suit sa mission : il ne lit pas le skill, ne refait
  pas le triage et ne délègue pas.
- Ne jamais lancer Antigravity sous `--dangerously-skip-permissions` pour
  contourner les restrictions d'un rôle.
