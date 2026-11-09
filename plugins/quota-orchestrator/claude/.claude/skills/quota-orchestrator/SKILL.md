---
name: quota-orchestrator
description: Routage sélectif multi-modèles pour la racine lorsqu'une délégation ou un arbitrage de palier peut améliorer le résultat, le délai ou le coût global. Les tâches locales bornées et consultations documentaires ponctuelles peuvent rester directes. Ne s'applique pas aux sous-agents déjà mandatés.
---

# Routage sélectif multi-modèles

## Objectif et périmètre

Préserver la qualité et la pertinence du résultat, puis réduire le coût total,
puis le délai, sous contrainte d'accès au palier le plus cher. Ne pas abaisser
les critères d'acceptation, omettre une vérification nécessaire ou simplifier la
demande pour rendre un modèle moins coûteux utilisable.
Comparer le coût du travail complet : lancement, contexte, exécution, attente,
intégration et éventuelle reprise. Le modèle le moins cher par token ne rend
pas automatiquement une délégation rentable. Comparer les consommations de
tous les agents, racine comprise, pondérées par les tarifs applicables au
modèle et aux tokens entrants, en cache et sortants. Plus de tokens sur un
palier moins cher est un bon échange tant que la qualité tient et que le délai
ne se dégrade pas sensiblement.
Sans mesure, annoncer un gain attendu, pas démontré.
Toute comparaison économique exige un rapport de mesure `Complete = true`.
Un run incomplet a exactement le statut `non observable` : ne jamais citer ses
tokens ou durées dans un ratio, une médiane, une comparaison ou une
recommandation économique. S'il reste moins de deux runs complets, conclure
qu'aucune comparaison économique n'est possible et conserver les diagnostics.

Ce skill est destiné à la racine uniquement. Un enfant déjà mandaté ne le
recharge pas, ne refait pas de triage et ne redélègue pas. Il suit sa mission,
son rôle et remonte les inconnues qui nécessitent une décision.

## Choisir le chemin

Une courte inspection initiale est autorisée : grouper les lectures et
recherches indépendantes, puis décider avec les faits disponibles. Ne pas
compter les opérations pour déclencher une délégation.

| Situation | Chemin normal |
|---|---|
| Petit travail local, lot déterministe borné ou implémentation locale au contrat explicite | Racine : lecture, modification et validation |
| Exploration étendue ou indépendante d'un travail utile de la racine | `scout` |
| Barrière de validation sur arbre figé, matrice d'au moins trois commandes ou environ deux minutes, ou validation en parallèle d'un travail racine disjoint (voir « Quand `runner` est le chemin normal ») | `runner` |
| Implémentation substantielle ou indépendante dont la délégation est amortie | `builder`, validation ciblée comprise |
| Consultation documentaire ponctuelle | Racine directement |
| Recherche documentaire à plusieurs questions ou sources | `researcher` |
| Raisonnement complexe ou intégration | Racine |
| Arbitrage technique difficile, ou décision structurante coûteuse à corriger nécessitant un avis expert | `architect` |

Le routage `researcher` est impératif : créer ce sous-agent avant toute
consultation ou attente, vérifier qu'un identifiant actif a été retourné, puis
l'attendre. La racine ne réalise pas elle-même la recherche documentaire
multiple et n'attend jamais sans enfant actif.

Le routage `scout` est impératif lorsqu'il faut établir une cause en traçant
des appelants ou un flux à travers plusieurs fichiers ou modules. La racine
peut seulement inspecter assez pour borner la mission ; elle crée effectivement
`scout`, vérifie son identifiant actif et l'attend au lieu de réaliser elle-même
l'exploration.

Choisir le rôle le moins coûteux capable de respecter les critères
d'acceptation sans perte de pertinence, lorsque la coordination est amortie.
La capacité de la racine à faire le travail elle-même n'interdit pas de déléguer.
Une petite modification risquée peut demander une revue indépendante ; le
nombre de fichiers ne détermine ni le niveau nécessaire ni la rentabilité.
Si une ambiguïté décisive dépasse le rôle choisi, la racine garde cet arbitrage
et ne transmet que la partie suffisamment définie ; ne pas déléguer à bas coût
en comptant sur une reprise systématique pour obtenir la qualité attendue.

Quand un choix de palier est utile, annoncer une ligne de triage après cette
inspection et avant la délégation. Pour une simple lecture directe, ne pas
charger ce skill uniquement pour annoncer l'absence de délégation.
Ne pas lancer un enfant puis attendre si effectuer le petit lot directement
est plus économique. Une attente reste légitime pour un lot substantiel
dépendant ; ne pas inventer du travail parallèle ni dupliquer celui de l'enfant.

## Modèles, efforts et tarifs

| Rôle | Modèle | Effort | $/1M entrée | $/1M sortie |
|---|---|---|---|---|
| Racine | `opus` — `claude-opus-5-5` | `xhigh` | 4 | 20 |
| `scout` | `sonnet` — `claude-sonnet-5-5` | `medium` | 2 | 10 |
| `researcher` | `sonnet` — `claude-sonnet-5-5` | `medium` | 2 | 10 |
| `runner` | `claude-haiku-5-5` | `medium` | 0.10 / 0.50 | 0.50 / 2.50 |
| `builder` | `sonnet` — `claude-sonnet-5-5` | `high` | 2 | 10 |
| `architect` | `opus`, ou `fable` sur accès confirmé | `xhigh` | 4 → 10 | 20 → 50 |

`runner` utilise l'identifiant fixe de Haiku 5.5. Ses deux tarifs concernent
respectivement les prompts jusqu'à / au-delà de 100 000 tokens : entrée non
mise en cache, écritures et lectures de cache de chaque requête, hors sortie.
Le tarif choisi s'applique à toute la requête, avant agrégation des coûts.
Les tarifs Haiku 4.5 restent dans le script pour les anciens transcripts.
La lecture de cache de Sonnet 5.5 coûte désormais 0,10 $/MTok, contre 0,20 pour
Opus 5.5. Sources du 7 octobre 2026 : [annonce Haiku 5.5](https://www.anthropic.com/claude-haiku-5-5),
[tarifs](https://platform.claude.com/docs/en/about-claude/pricing) et
[guide de prompting](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5#use-effort-to-control-thinking).

`opus` désigne Opus 5.5 sur l'API Anthropic et les abonnements à partir de
Claude Code 2.1.280 ; un CLI plus ancien ou un autre fournisseur sert un autre
modèle, et `resolvedModel` fait foi. L'effort par défaut d'Opus 5.5 est
`medium`, mais chaque rôle fixe le sien.

`sonnet` désigne Sonnet 5.5 sur l'API Anthropic à partir de Claude Code
2.1.284 ; selon la documentation, l'alias résout vers un Sonnet plus ancien
sur Bedrock, Vertex, Foundry et Claude Platform on AWS. Les niveaux d'effort
de Sonnet 5.5 sont recalibrés par rapport à Sonnet 5 : un niveau ne produit pas
le même raisonnement, et la documentation demande de refaire un balayage
d'évals plutôt que de reporter un réglage. Elle recommande `medium` pour
l'agentique bien spécifié, `high` pour le plus dur, et `xhigh`/`max`
seulement là où des évals montrent un gain. Le défaut est `high` sur l'API et
`medium` dans Claude Code : chaque rôle fixe donc son effort.

`runner` tourne sur le palier le moins cher parce qu'il exécute et rapporte sans
concevoir, et parce que ses bornes — trois cycles, règle du signal nouveau, deux
tentatives sur problème d'environnement — sont précisément ce qui rend ce palier
sûr ici. Haiku 5.5 prend en charge `effort` : `medium` est le point de départ
recommandé pour le travail agentique. `low` peut omettre des vérifications ou
arrêter trop tôt sur de longs prompts ; le rôle exige des contrôles exécutés.

`scout` et `researcher` ne descendent pas à ce palier : ils produisent des faits
que la racine va croire sans les revérifier. Un palier trop bas y produit des
affirmations assurées et fausses, dont le coût de reprise dépasse l'économie.
Leur effort reste `medium` : leur travail est borné par les entrées et sorties
plus que par le raisonnement, et un effort plus bas consolide les appels
d'outils — moins cher et plus rapide à qualité tenue.

`builder` reste sur le palier intermédiaire en `high` plutôt que de monter d'un
palier : l'effort est le premier levier de qualité à l'intérieur d'un modèle,
avant le changement de palier, et Sonnet 5.5 coûte deux fois moins en entrée,
en sortie et en lecture de cache. `xhigh` n'est pas le défaut : la
documentation le réserve aux tâches longues à budget de tokens très large et
aux cas où des évals montrent un gain, ce que les tâches bornées de `builder`
(trois tentatives) ne sont pas. Passer `builder` en `xhigh` seulement sur
mesure, run complet à l'appui.

Deux escalades existent, par le paramètre de modèle à l'invocation, qui prime
sur le rôle. Aucune ne demande de modifier un fichier :

- `builder` → `opus`, pour une tâche difficile : invariants subtils, couplage
  entre plusieurs modules, ou premier échec porteur d'un signal conceptuel.
  Opus 5.5 coûte deux fois Sonnet 5.5 en entrée, sortie et lecture de cache ;
- `architect` → `fable`, sur accès confirmé seulement, en second appel : quand
  l'avis Opus 5.5 laisse une contradiction technique décisive. Directement
  seulement si une erreur de décision coûterait exceptionnellement cher.

Chacune est une décision explicite, annoncée et motivée, jamais un défaut.
Ne jamais monter d'un palier pour un problème d'environnement.

## Accès Fable

Fable 5.2 est l'escalade de raisonnement la plus coûteuse du plugin. Pour le
modèle 5.2, les tarifs API standard par million de tokens sont : entrée 8 $,
sortie 40 $, écriture de cache 5 min 10 $, écriture de cache 1 h 16 $, lecture
de cache 0,20 $. Cela représente deux fois les tarifs Opus 5.5 pour l'entrée,
la sortie et les écritures de cache, et le même tarif pour la lecture. Fable
5.1 reste à ses tarifs historiques de 10/50 $ pour l'entrée et la sortie.

En Claude Code first-party, l'alias `fable` sert Fable 5.2 à partir de la
version 2.1.321, mais un réglage épinglé, une restriction d'organisation ou le
mapping d'un fournisseur peut encore servir 5.1. L'identifiant du modèle 5.2
est `claude-fable-5-2`. La version du CLI et l'alias demandé ne prouvent pas
le modèle résolu : vérifier `resolvedModel` avant d'annoncer une consultation
Fable 5.2 ou de lui appliquer son tarif.

Le contexte maximal documenté est de 1 million de tokens, avec jusqu'à 128 000
tokens en sortie. Fable 5.2 exige une conservation des données de 30 jours ;
il n'est pas disponible sous ZDR (zero data retention) sans autorisation
expresse d'Anthropic. Si l'organisation exige ZDR sans cette autorisation,
traiter Fable 5.2 comme indisponible.

**Présumer l'accès indisponible par défaut.** La détermination est déterministe
et tient en deux commandes :

```
claude auth status --json     # loggedIn, authMethod, apiProvider, subscriptionType
claude --version              # Fable 5.2 exige 2.1.321 ou plus récent
```

Le verdict se lit dans cet ordre ; le premier constat qui tranche l'emporte :

| Constat | Verdict |
|---|---|
| `availableModels` défini dans les settings | il fait foi pour les modèles autorisés |
| version du CLI < 2.1.321 | Fable 5.2 indisponible sur ce CLI ; une ancienne version peut encore servir 5.1 |
| `loggedIn` faux | indéterminable — aucune session |
| `apiProvider` ≠ `firstParty` (Bedrock, Vertex, Foundry) | indéterminable — vérifier l'identifiant et le mapping du fournisseur ; ne pas supposer que l'alias `fable` fonctionne |
| `authMethod` indiquant une clé API Anthropic ou une facturation à l'usage | accès complet si le modèle n'est pas exclu par les réglages ou la politique de rétention |
| `subscriptionType` = `free` | indisponible |
| `subscriptionType` ∈ {`pro`, `max`} | disponible si les réglages ne l'excluent pas ; l'alias peut être actualisé en Fable 5.2 sur CLI 2.1.321+ |
| `subscriptionType` ∈ {`team`, `enterprise`} | vérifier les réglages de l'organisation ; ils peuvent autoriser Fable 5.2 ou garder une version épinglée |
| toute autre valeur de `subscriptionType` | indéterminable — demander |

Cette liste de valeurs n'est pas garantie exhaustive : une valeur inconnue ne
s'interprète pas, elle se demande. Pour les fournisseurs tiers, la disponibilité
dépend du modèle et du mapping qu'ils exposent. Si le compte est soumis à ZDR,
l'autorisation expresse d'Anthropic doit aussi être vérifiée.

**Disponible ne vaut pas autorisé.** Sur abonnement, une requête Fable peut
débiter des usage credits, c'est-à-dire de l'argent en plus de l'abonnement.
Demander donc une fois, avant la première consultation, en nommant le modèle
résolu et ses tarifs standard : 8/40 $ par million pour Fable 5.2, ou 10/50 $
pour Fable 5.1 si le modèle est encore épinglé. Le mode Fast est optionnel et
double les tarifs d'entrée et de sortie de Fable 5.2 à 16/80 $ par million :
il exige un consentement distinct. Consigner les autorisations dans
`.claude/settings.local.json` pour ne pas les redemander.

L'exporteur JSONL du projet calcule les tarifs standards et ne lit pas le niveau
de service. Il ne chiffre donc pas correctement le mode Fast ; utiliser la
facture comme coût réel, et ne pas présenter son estimation standard comme le
coût d'une session Fast.

En mode non interactif (`-p`) et via le SDK, Claude Code débite **sans**
demander de consentement : ne jamais y escalader vers Fable sans une
autorisation explicite obtenue au préalable.

Sans accès, sur refus, ou faute de pouvoir trancher : consulter `architect` tel
qu'il est défini, en Opus `xhigh`, et **annoncer explicitement qu'il s'agit
d'un avis Opus 5.5, pas Fable**. Ne jamais présenter un repli comme une
consultation Fable.
## Transmettre sans perdre les conditions

Utiliser les rôles nommés. Un enfant part d'un contexte propre : le message doit
être autonome. Ne pas transmettre l'historique complet par commodité pour une
tâche mécanique.

Sélectionner le rôle dans le champ `subagent_type` prévu par l'outil Agent,
avec son nom exact exposé par le runtime, qualifié pour un plugin. Le champ
`name` du frontmatter reste l'identifiant stable du rôle, pas un nom de modèle.
Transmettre l'enveloppe suivante dans le prompt et la récupérer en première
ligne du rapport :
`name: <rôle sélectionné> | model_requested: <modèle demandé> | effort_requested: <effort configuré ou hérité>`.
Exemple sans override : `name: scout | model_requested: sonnet | effort_requested: medium`.
Reporter tout override de modèle réellement passé à l'appel ; l'effort vient
du profil ou de l'héritage, sans inventer un argument d'appel non supporté.
Pour Haiku 5.5, reporter l'effort configuré ou hérité (`medium` pour `runner`).
Ces champs du rapport sont déclaratifs et propres au projet, pas des champs
natifs ajoutés au résultat de l'outil. L'enfant ne s'auto-atteste pas : il ne
fournit un modèle/effort effectif qu'avec une métadonnée runtime et sa provenance.
La racine réutilise les preuves du rapport et effectue l'acceptation ciblée ;
l'absence d'attestation ne déclenche pas une nouvelle exploration ou validation.

Source : [documentation Anthropic des sous-agents](https://code.claude.com/docs/en/sub-agents),
consultée le 5 octobre 2026 : `name`, `model` et `effort` dans le frontmatter,
`subagent_type` pour sélectionner un rôle. La page décrit aussi l'affichage du
modèle et de l'effort dans l'interface et `/tasks` ; elle n'établit pas le schéma
de retour universel supposé auparavant. Ne pas confondre visibilité UI et
métadonnées accessibles à l'agent principal.

Le champ natif `resolvedModel` a été observé localement le 5 octobre 2026 dans
un résultat `async_launched`, concordant avec `message.model` et `effort` dans
le transcript enfant. C'est une observation du format local, pas une garantie
universelle d'Anthropic. Le lecteur vérifie le format et signale les inconnues.
Le transport du rapport utilise le mécanisme `PostToolUse` / `additionalContext`
de la [référence officielle des hooks](https://code.claude.com/docs/en/hooks).
`SubagentStop` ne sert pas à prétendre injecter cette preuve dans le parent.

Le message autonome contient les seuls éléments utiles :

- objectif et critères d'acceptation de l'utilisateur ;
- fichiers/périmètre et contraintes, dont les permissions ;
- faits établis et sources ou extraits probants ;
- hypothèses, inconnues et question à trancher, séparées des faits ;
- commandes, résultats, état des fichiers et environnement déjà vérifiés ;
- résultat attendu et limites de la mission.

Transmettre notamment l'absence déjà vérifiée de dépôt Git et les validations
réussies. Ne pas réexécuter une découverte d'environnement sans changement.
L'enfant groupe ses lectures indépendantes et répond proportionnellement au
travail : un résultat simple ne nécessite pas de rapport cérémoniel.

La synthèse conserve les réserves, alternatives conditionnelles et mesures
nécessaires de l'expert. La racine distingue toute décision nouvelle qu'elle
ajoute. Une hypothèse métier non établie reste une hypothèse. Si elle change le
choix et ne peut pas être résolue par inspection, demander la précision à
l'utilisateur ou présenter une recommandation conditionnelle, sans fabriquer de
fait métier.

## Validation et arrêt

La validation ciblée appartient à celui qui réalise le changement. La racine lit
le résultat et inspecte les modifications (diff Git si disponible).
Ne pas créer un runner pour répéter une validation dont la commande, le
résultat et l'état pertinent des fichiers/environnement sont connus et
inchangés. Si cet état est incertain, vérifier avant de réutiliser le résultat.
Après une modification pertinente, un échec ou une nouvelle inquiétude, lancer
le contrôle nécessaire. Pour un changement à risque (sécurité, perte de données,
migration, contrat public), conserver une revue indépendante ciblée ; ne pas
confondre cette revue avec la répétition du même test. `architect` n'est pas le
testeur final et n'exécute pas cette revue de validation.

### Quand `runner` est le chemin normal

`runner` ne s'appelle jamais pour être appelé : une condition ci-dessous est
nécessaire, jamais suffisante. Il faut en plus un bénéfice concret et annoncé en
une ligne (racine libre pendant l'attente, sortie volumineuse qui n'entrera pas
dans le contexte racine, ou verdict seul requis) qui dépasse le coût de
l'enveloppe et de la lecture du rapport. Sans ce bénéfice, la racine lance la
commande elle-même. Conditions :

- **barrière finale sur arbre figé** : suite complète, build ou smoke avant
  commit ou remise, quand la racine n'a plus de modification en cours sur les
  fichiers testés et n'a besoin que du verdict ;
- **matrice de validation** : au moins trois commandes ou environ deux minutes
  d'exécution cumulées, dont la racine n'a pas à lire la sortie intégrale ;
- **validation en parallèle** : la racine a un travail utile sur des fichiers
  que la validation ne touche pas, et la commande est connue.

`runner` n'est pas indiqué si la validation s'enchaîne avec des corrections
décidées par la racine (boucle correction/test), si c'est une commande unique
dont la sortie filtrée tient en quelques lignes, ou si le `builder` l'a déjà
exécutée sur l'état actuel. Le gain attendu est surtout un contexte racine plus
court et une racine libre pendant l'attente ; il n'est pas démontré tant qu'aucun
run complet n'a mesuré le coût `runner` contre le coût racine.

Dans l'enveloppe, donner au `runner` les commandes exactes, le critère de
passage, les fichiers à ne pas modifier et l'état connu ; il rapporte le code de
sortie mesuré et l'erreur essentielle, et remonte tout échec dont la cause n'est
pas évidente et locale.

L'échec est un livrable valide. Garder les bornes des rôles : runner, trois
cycles correction/test ; environnement, deux tentatives ; scout, trois
recherches infructueuses ; researcher, cinq requêtes ; builder, trois tentatives.
Deux fois la même erreur impose l'arrêt ou une reclassification avec un signal
nouveau ; pas de troisième essai identique. Toute relance change le périmètre,
la spécification ou le niveau pour une raison factuelle. Les problèmes
d'environnement ne montent pas d'un palier. Une contradiction factuelle appelle
une vérification ciblée, pas un arbitrage expert à l'aveugle.

## Consultation architecte

`architect` traite uniquement les arbitrages conceptuels ou d'architecture.
Jamais exploration, lecture répétitive, commande, test, log, retry, modification
mécanique, problème d'environnement ou choix d'intention de l'utilisateur.

Fixer le budget quand la consultation devient utile : zéro sans besoin ; un
appel initial, au plus deux par tâche standard. Annoncer le budget restant.
Un second appel nécessite des faits nouveaux ou une contradiction technique
restante susceptible d'invalider la décision. Pas de deuxième avis systématique
ni de retry sur le même échec. Au-delà, demander un nouveau budget.

Préparer une enveloppe concise (viser environ 60 lignes) avec objectif,
acceptation, extraits, faits, hypothèses, inconnues, résultats déjà obtenus et
question ouverte aux alternatives. La longueur est un objectif, pas un plafond :
ne jamais supprimer une preuve ou condition décisive pour y tenir.
Pas de logs complets ou historique lorsqu'un extrait suffit.

`architect` travaille sur cette enveloppe, sans exécution, sans écriture ni
délégation. Il peut rejeter le cadrage. Son livrable est une décision avec
conditions, interfaces/invariants utiles, alternatives/risques et mesures
nécessaires ; environ 80 lignes si cela suffit, sans forcer la longueur.
Pas de patch ni implémentation complète ; courts extraits d'interface autorisés.
La racine fait effectuer les mesures manquantes selon le routage sélectif, et ne
reconsulte que si elles changent la décision.

## Permissions

Conserver les restrictions de chaque rôle : elles tiennent à sa liste d'outils,
qui est réellement appliquée. Ne jamais lancer la session sous
`--dangerously-skip-permissions` ni en mode `bypassPermissions`, et ne jamais
élargir les permissions du parent pour consulter `architect`. Si les
restrictions d'`architect` ne tiennent plus, isoler la décision dans une session
aux permissions adaptées plutôt que les contourner.
