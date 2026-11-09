# Routage sélectif multi-modèles pour Claude Code

[English](README.md) · [Dépôt et guide Codex](../../../README.fr.md)

Une configuration Claude Code, installable en plugin ou par projet, qui confie
le travail à des rôles spécialisés uniquement quand la délégation préserve la qualité tout en réduisant
le coût total ou le délai. L'agent principal reste responsable des décisions, de
l'intégration et de la communication avec l'utilisateur.

## Politique de routage

Priorités, dans cet ordre :

1. Préserver la qualité et la pertinence du résultat.
2. Réduire le coût total, coordination et reprises comprises.
3. Réduire le délai.

Un coût total plus bas obtenu avec davantage de tokens sur un palier moins cher
est un bon échange. Une qualité dégradée ou un délai multiplié ne l'est pas.

Les tâches petites et bornées restent à l'agent principal. La délégation sert
quand un rôle clairement cadré peut abattre un travail substantiel plus
efficacement, ou apporter une analyse indépendante utile.

| Rôle | Modèle | Effort | $/1M entrée | $/1M sortie | Responsabilité |
| --- | --- | --- | --- | --- | --- |
| Principal | `opus` | `xhigh` | 4 | 20 | Triage, décisions, intégration, petites tâches locales |
| `scout` | `sonnet` | `medium` | 2 | 10 | Exploration en lecture seule du code et des logs |
| `researcher` | `sonnet` | `medium` | 2 | 10 | Recherche documentaire multi-sources |
| `runner` | `claude-haiku-5-5` | `medium` | 0.10 / 0.50 | 0.50 / 2.50 | Validations longues et lots mécaniques |
| `builder` | `sonnet` | `high` | 2 | 10 | Implémentation bornée avec validation ciblée |
| `architect` | `opus`, ou `fable` sur accès confirmé | `xhigh` | 4 → 10 | 20 → 50 | Décisions d'architecture, rares et bornées |

`opus` désigne Opus 5.5 sur l'API Anthropic et les abonnements, ce qui exige
Claude Code 2.1.280 ou plus récent ; un CLI plus ancien ou un autre fournisseur
sert un autre modèle. `sonnet` désigne Sonnet 5.5 sur l'API Anthropic à partir de
Claude Code 2.1.284 ; selon la documentation, il résout vers un Sonnet plus
ancien sur Bedrock, Vertex, Foundry et Claude Platform on AWS. Les niveaux
d'effort de Sonnet 5.5 sont recalibrés par rapport à Sonnet 5 : les réglages ont
été rechoisis d'après les recommandations officielles, pas reportés.

`runner` utilise l'identifiant fixe de Haiku 5.5. Ses tarifs ci-dessus concernent
respectivement les prompts jusqu'à / au-delà de 100 000 tokens. Le seuil inclut
l'entrée non mise en cache, les écritures et les lectures de cache de chaque
requête ; les tokens de sortie n'y comptent pas. L'entrée et la sortie prennent
le tarif sélectionné pour toute la requête. Voir l'[annonce Haiku 5.5](https://www.anthropic.com/claude-haiku-5-5)
et les [tarifs](https://platform.claude.com/docs/en/about-claude/pricing).

Trois choix méritent une justification :

- **`runner` sur le palier le moins cher.** Le rôle exécute et rapporte, il ne
  conçoit pas. Ses bornes — trois cycles correction/test, arrêt au premier signal
  répété, deux tentatives sur un problème d'environnement — sont précisément ce
  qui rend ce palier sûr ici. Haiku 5.5 prend en charge `effort` ; `medium` est
  le point de départ recommandé pour le travail agentique. `low` peut arrêter
  le travail trop tôt ou omettre des vérifications sur de longs prompts : le
  rôle exige donc d'exécuter les contrôles avant d'annoncer un succès. Voir le
  [guide de prompting Haiku 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5#use-effort-to-control-thinking).
- **`scout` et `researcher` n'y descendent pas.** Tous deux produisent des faits
  que l'agent principal croira sans les revérifier ; un palier trop bas y produit
  des affirmations assurées et fausses, dont la reprise coûte plus que
  l'économie. Leur effort reste `medium` : leur travail est borné par les entrées
  et sorties plus que par le raisonnement, et un effort plus bas consolide les
  appels d'outils — moins cher et plus rapide, à qualité tenue.
- **`builder` monte en effort plutôt qu'en palier, mais s'arrête à `high`.**
  L'effort est le premier levier de qualité à l'intérieur d'un modèle ;
  `sonnet`/`high` coûte deux fois moins que le palier au-dessus en entrée et en
  sortie et en lecture de cache. `xhigh` n'est pas le défaut : la
  documentation le réserve aux tâches longues à très gros budget de tokens et
  aux cas où des évals montrent un gain, ce que les tâches bornées de `builder`
  (trois tentatives) ne sont pas. Ne le passer en `xhigh` que sur mesure, à
  partir de runs complets.

Deux escalades, décidées explicitement et passées à l'invocation, sans modifier
aucun fichier de rôle : `builder` vers `opus` pour une tâche difficile,
`architect` vers `fable` sur accès confirmé, en second appel lorsque l'avis
Opus 5.5 laisse une contradiction décisive. Un problème d'environnement ne fait
jamais monter d'un palier.

## Accès à Fable 5.2

Fable 5.2 est sorti le 9 novembre 2026. Ses tarifs API standards par million
de tokens sont de 8 $ en entrée, 40 $ en sortie, 10 $ pour une écriture de
cache de 5 minutes, 16 $ pour une écriture d'une heure et 0,20 $ en lecture de
cache. L'entrée, la sortie et les écritures de cache coûtent deux fois les
tarifs d'Opus 5.5 ; la lecture de cache coûte le même prix. Fable 5.1 conserve
ses tarifs historiques de 10/50 $ en entrée/sortie.

Sur Claude Code first-party, l'alias `fable` sélectionne Fable 5.2 avec le CLI
2.1.321 ou plus récent ; son identifiant est `claude-fable-5-2`. Des réglages
épinglés, des restrictions d'organisation ou le mapping d'un fournisseur tiers
peuvent encore servir Fable 5.1 ou rendre Fable inaccessible. Vérifiez
`resolvedModel` : l'alias et la version du CLI ne prouvent pas le modèle
effectivement exécuté.

Fable 5.2 accepte un contexte de 1 million de tokens et jusqu'à 128 000 tokens
en sortie. Il exige une conservation des données de 30 jours et n'est pas
disponible sous ZDR (zero data retention) sans autorisation expresse
d'Anthropic. Si l'organisation impose ZDR sans cette autorisation, considérez
Fable 5.2 indisponible.

Le mode Fast est optionnel et double les tarifs d'entrée/sortie de Fable 5.2 à
16/80 $ par million de tokens. Il demande un consentement explicite distinct.
L'exporteur des transcripts applique les tarifs standards et ne lit pas le
niveau de service ; son estimation ne chiffre donc pas correctement Fast.
Utilisez la facture pour connaître le coût réel.

L'accès est **présumé indisponible**. Vérifiez :

```bash
claude auth status --json
claude --version
```

La table de décision complète figure dans le skill. Les fournisseurs tiers
exigent leur propre identifiant ou mapping de modèle Fable ; ne supposez pas que
l'alias `fable` fonctionne partout. Les réglages Team et Enterprise peuvent
restreindre le modèle ou garder Fable 5.1 épinglé.

Disponible ne vaut pas autorisé. Sur abonnement, Fable peut débiter des *usage
credits*, c'est-à-dire de l'argent en plus de l'abonnement. Avant la première
consultation, l'agent principal demande une fois en nommant le modèle effectif
et ses tarifs standards ; le mode Fast exige un consentement distinct. La
réponse est consignée dans `.claude/settings.local.json`, ignoré par Git et
propre à chaque poste. Les lancements non interactifs (`-p`) et les appels SDK
peuvent facturer sans demander : ne jamais y escalader sans autorisation
explicite préalable.

Sans accès ou sur refus, `architect` répond en Opus 5.5 `xhigh` et **annonce
explicitement qu'il ne s'agit pas d'un avis Fable**. Après coup, le modèle
effectif est vérifié dans les métadonnées runtime lorsqu'elles sont disponibles
(par exemple `resolvedModel`). Leur absence ne fait pas rejeter le travail ni
répéter ses validations ; elle interdit seulement de présenter Fable comme attesté.

Sources consultées le 9 novembre 2026 : [présentation de Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/overview),
[guide de migration Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/whats-new-fable-5-2)
et [configuration des modèles Claude Code](https://code.claude.com/docs/en/model-config).
## Identité réellement observée

Le hook `.claude/hooks/agent_identity.py` ajoute au contexte du parent un rapport
avec `resolvedModel`, sa provenance et l'effort observé lorsqu'il est disponible.
Il lit les métadonnées natives et le transcript du seul agent concerné. Il ne
remplit jamais un modèle effectif à partir de l'alias demandé ou du profil, et
ne modifie pas la réponse native de Claude Code. Un champ inconnu reste `null`.
Le modèle résolu au lancement et celui observé après exécution restent distincts ;
les divergences, changements de modèle et preuves incomplètes sont signalés.

Le hook est livré dans le plugin et dans l'installation classique. Python 3 doit
être accessible via `python` au processus Claude Code. Redémarrez la session
après mise à jour et vérifiez que le hook est activé : sans son rapport, l'identité
n'est pas attestée. Les erreurs de métadonnées demandent un contrôle ciblé,
jamais une reprise intégrale du travail. Le format interne des transcripts peut
évoluer ; les tests couvrent le format observé, pas une garantie future du CLI.
Transport : [hooks Anthropic](https://code.claude.com/docs/en/hooks).

Validation sans appel de modèle : `python plugins/quota-orchestrator/claude/test_agent_identity.py`.

## Structure du projet

- `CLAUDE.md`, `.claude/agents/` et
  `.claude/skills/quota-orchestrator/SKILL.md` définissent les règles de routage,
  les rôles et le processus de décision.
- `.claude/settings.json` fixe les réglages partagés ;
  `.claude/hooks/agent_identity.py` rapporte les métadonnées de modèle observées
  pour chaque sous-agent.
- Le [catalogue Claude Code](../../../.claude-plugin/marketplace.json) sélectionne le paquet commun. Son [manifeste](../.claude-plugin/plugin.json) charge la skill et les hooks. Claude Code découvre les rôles dans `../agents/`.
- `extract_claude_jsonl.ps1` calcule l'usage de tokens, la durée et le coût en
  dollars à partir des transcripts de session.

## Utilisation

### Héritage et précédence

Claude Code construit sa chaîne d'instructions, de la plus faible à la plus forte
précédence : les instructions gérées par l'organisation, puis `~/.claude/CLAUDE.md`,
puis le `CLAUDE.md` à la racine du dépôt, puis `CLAUDE.local.md`. Le `CLAUDE.md`
d'un sous-dossier est chargé à la demande, quand Claude y travaille. La syntaxe
`@chemin` importe un autre fichier ; les chemins relatifs se résolvent depuis le
fichier qui importe, pas depuis le répertoire courant.

Si votre projet a déjà un `CLAUDE.md`, **ne le remplacez pas** : gardez son
contenu et ajoutez-y les règles de routage. Pour restreindre des instructions à
un sous-dossier, placez-y un autre `CLAUDE.md`.

Pour les réglages, `~/.claude/settings.json` fournit vos valeurs personnelles.
`.claude/settings.json` du projet passe au-dessus, `.claude/settings.local.json`
au-dessus encore, et les réglages gérés par l'organisation priment sur tout.

### Installer comme plugin

Le dépôt est aussi une marketplace de plugins Claude Code. Le plugin fournit les
cinq rôles, la skill `quota-orchestrator` et un hook `SessionStart` qui charge
`CLAUDE.md` dans le contexte de l'agent principal au démarrage, à la reprise,
après `/clear` et après compactage. Les sous-agents ne le reçoivent pas, ce qui
est cohérent avec la règle qui leur interdit de router.

Depuis le CLI :

```bash
claude plugin marketplace add ./
```

```bash
claude plugin install quota-orchestrator@quota-orchestrator
```

Depuis un checkout local, `claude plugin marketplace add ./` remplace la première
commande, et `claude --plugin-dir ./plugins/quota-orchestrator` charge le plugin pour une seule session
sans l'installer. Dans l'application desktop (onglet Code), cliquez sur **+** à
côté de la zone de saisie, puis sur **Add plugins**. Si le menu affiche
**Plugins**, choisissez **Browse plugins**. Sélectionnez `quota-orchestrator`
dans le marketplace local ; une installation en portée utilisateur faite depuis le
CLI est aussi disponible dans les sessions locales de l'application. Ouvrez
ensuite une nouvelle session, ou lancez `/reload-plugins`.

À savoir :

- Les composants du plugin sont préfixés : les rôles apparaissent comme
  `quota-orchestrator:scout` et ainsi de suite, la skill comme
  `quota-orchestrator:quota-orchestrator`. Un agent projet ou utilisateur de même nom
  court prime sur celui du plugin.
- Le hook exécute `cat` et demande donc un shell POSIX : Git Bash sous Windows.
- Le plugin ne charge pas les réglages de `.claude/settings.json`. Choisissez `opus` et `xhigh` avec
  `/model` et `/effort`, ou copiez `effortLevel`, `modelSettings` et
  `permissions.deny` depuis le `.claude/settings.json` de ce dépôt vers
  `~/.claude/settings.json`.
- Ne cumulez pas le plugin et `install.py` sur un même projet : les règles
  seraient chargées deux fois et les rôles du projet masqueraient ceux du plugin.
- Les deux manifestes partagent la même version (**0.10.1**). Le catalogue ne la duplique pas.
- `.claude/settings.json` est une configuration partagée, volontairement suivie
  par Git. Gardez vos réglages personnels et secrets dans
  `.claude/settings.local.json`, qui est ignoré.

Pour migrer une ancienne installation ClaudeSkills, vérifiez sa portée avec
`claude plugin list`, désinstallez `claudeskills@claudeskills`, puis retirez son
marketplace. Ajoutez le marketplace de ce projet, puis installez
`quota-orchestrator@quota-orchestrator` avec la même portée (`--scope user`,
`project` ou `local`). Le préfixe des composants Claude devient
`quota-orchestrator:`.

La parité décrite ici concerne Claude Code, y compris ses sessions locales dans
l’application de bureau. Le chat Claude.ai ne fournit pas le même environnement
pour les hooks et les sous-agents.

### Mettre à jour et valider une livraison

Après publication du commit :

```bash
claude plugin marketplace update quota-orchestrator
claude plugin update quota-orchestrator@quota-orchestrator
```

Démarrez une nouvelle session ou utilisez `/reload-plugins`. Python 3.11+ doit
être accessible via `python`, y compris depuis Claude Code, pour le hook d’identité.

Avant commit, validez séparément les deux manifestes (la racine est reconnue
comme marketplace par le CLI) et les tests sans consommation de modèle :

```bash
claude plugin validate plugins/quota-orchestrator/.claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json --strict
python plugins/quota-orchestrator/claude/test_plugin.py
python plugins/quota-orchestrator/claude/test_agent_identity.py
python plugins/quota-orchestrator/claude/test_extract_claude_jsonl.py
python plugins/quota-orchestrator/claude/test_install.py
python plugins/quota-orchestrator/claude/smoketest.py
```

`smoketest.py` nécessite Windows PowerShell 5.1. Les tests avec appel de modèle
restent séparés dans `smoketest_live.py` et consomment du budget.

### Installer dans un projet

1. Python 3.11 ou plus récent est requis. Depuis ce dépôt, lancez :

   ```text
   python plugins/quota-orchestrator/claude/install.py chemin/vers/votre/projet
   ```

   `--dry-run` affiche le plan sans rien écrire. L'installateur ajoute les
   règles de routage à un `CLAUDE.md` existant entre des marqueurs
   `claudeskills:routing`, n'ajoute que les clés manquantes de
   `.claude/settings.json`, ajoute le hook d’identité sans retirer les hooks
   existants, sauvegarde les fichiers modifiés sous
   `.claudeskills-backup/`, et avertit au lieu d'écraser un fichier de rôle ou
   de skill ou de hook divergent.
2. Relisez les avertissements, puis les modèles, les efforts et les règles de
   permission pour votre environnement, puis `/agents` pour confirmer que les
   cinq rôles sont vus avec le bon modèle et le bon effort.
3. Démarrez une nouvelle session depuis le dépôt pour que la chaîne
   d'instructions soit reconstruite.
4. Demandez à Claude de résumer ses instructions actives si vous voulez vérifier
   la détection.

Claude Code découvre les instructions de dépôt dans `CLAUDE.md`, les skills dans
`.claude/skills`, les rôles dans `.claude/agents` et les réglages dans
`.claude/settings.json`. Voir la documentation officielle :
[CLAUDE.md](https://code.claude.com/docs/en/memory),
[skills](https://code.claude.com/docs/en/skills),
[sous-agents](https://code.claude.com/docs/en/sub-agents),
[modèles](https://code.claude.com/docs/en/model-config),
[réglages](https://code.claude.com/docs/en/settings).

## Mesure

Sans mesure, un gain est attendu, pas démontré. `extract_claude_jsonl.ps1` lit
les transcripts JSONL de session et agrège tokens, durées et **coût en dollars**
par modèle, par effort et par rôle.

```powershell
.\plugins\quota-orchestrator\claude\extract_claude_jsonl.ps1
```

Le rapport porte un champ `Complete`. Il ne vaut `true` qu'en l'absence de tout
diagnostic. Un rapport incomplet a exactement le statut *non observable* : ses
tokens, coûts et durées ne doivent jamais servir dans un ratio, une médiane, une
comparaison ou une recommandation économique. Comparer au moins deux rapports
complets, sinon conclure qu'aucune comparaison n'est possible.

Le script lit deux niveaux : le transcript de la session pour l'agent principal,
et `<session>/subagents/agent-*.jsonl` pour chaque rôle délégué. Cette seconde
source est indispensable — le résultat de l'appel qui a lancé un sous-agent ne
porte que son **tour final**, pas son cumul. S'y fier sous-compte massivement.
Un sous-agent de fond est mesuré comme les autres ; ce qui rend un run non
observable, c'est un transcript manquant, un modèle absent de la table de prix,
ou une écriture de cache dont la durée de vie est inconnue.

Autre piège, également corrigé : un même message apparaît une fois par bloc de
contenu et son `usage` est **cumulatif**. Le script retient le maximum par
identifiant de message ; retenir le premier perdrait la majeure partie des
tokens de sortie.

Une écriture de cache se tarife selon sa durée de vie : 1,25× l'entrée pour un
cache de 5 minutes, **2× pour un cache d'une heure**. Claude Code utilise les
deux dans une même session — typiquement 1 heure pour l'agent principal et
5 minutes pour un sous-agent. Confondre les deux sous-estime la facture d'un
tiers ; le script lit donc la ventilation par durée de vie, et refuse de chiffrer
une écriture dont le TTL est inconnu.

Les tarifs vivent dans une seule table en tête du script ; c'est le seul endroit
à mettre à jour quand ils changent. `python plugins/quota-orchestrator/claude/test_extract_claude_jsonl.py` vérifie
le contrat du script sur des transcripts synthétiques, sans aucun appel de modèle.

Fable 5.2 utilise les tarifs API standards de cette table. L'exporteur des
transcripts ne lit pas le niveau de service et ne chiffre donc pas Fast, qui
double l'entrée/sortie ; utilisez les données de facturation pour obtenir le
coût réel d'une session Fast.

Les coûts Haiku 5.5 sont calculés par requête dédupliquée avant agrégation : un
rôle peut mélanger des prompts de part et d'autre du seuil de 100 000 tokens.
Les tarifs Haiku 4.5 restent disponibles pour les anciens transcripts. La
lecture de cache de Sonnet 5.5 coûte désormais 0,10 $ par million de tokens,
selon la mise à jour du 7 octobre 2026.

## Limites de sécurité

- Ne jamais lancer sous `--dangerously-skip-permissions` ni en mode
  `bypassPermissions`.
- Ne pas élargir les permissions de la session pour consulter `architect` ; si
  ses restrictions ne tiennent plus, isoler la décision dans une autre session.
- `architect` n'explore pas, n'exécute aucune commande, n'écrit aucun fichier et
  ne délègue pas.
- Les rôles restent dans leur périmètre et ne font pas de routage eux-mêmes :
  `Agent` est absent de la liste d'outils de chacun, ce qui l'empêche
  effectivement de déléguer.

## Personnalisation

Modifiez `.claude/settings.json` pour les efforts par défaut, et le fichier
correspondant sous `.claude/agents/` pour changer un rôle. Gardez modèles,
efforts et frontières de rôle synchronisés entre `CLAUDE.md`,
`.claude/skills/quota-orchestrator/SKILL.md` et ce README. Gardez chaque rôle de `../agents/` identique à sa copie dans
`.claude/agents/` ; `python plugins/quota-orchestrator/claude/test_plugin.py`
vérifie les manifestes par rapport au dépôt.

Les paliers proposés ici sont défendables, pas mesurés sur votre travail. Le
script de mesure existe précisément pour que vous les régliez sur vos propres
tâches — et la doctrine interdit d'annoncer un gain démontré tant que deux runs
complets ne le montrent pas.

La disponibilité des modèles dépend de votre compte et de votre environnement.
