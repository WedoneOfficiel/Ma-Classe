# Audit produit MaClasse V25 — modules, ergonomie et rendu

**État : audit produit poursuivi — candidat V25.1.0 — 25 novembre 2026**  
**Périmètre :** interface web, modules métier, cohérence visuelle, parcours Direction / Professeur / Élève.  
**Branche de travail :** \`feat/v25.0.25-stabilisation-reseau-migrations\`  
**Référence actuelle :** [PR #13](https://github.com/WedoneOfficiel/Ma-Classe/pull/13), non fusionnée.  
**Validation automatisée :** workflow [#1793](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45713179841) vert (3/3) : Linux, macOS Apple Silicon et Firefox réel. Les recettes sur le Mac et le PC Fedora physiques restent distinctes.

Ce document complète l'audit technique et réseau. Il ne déclare pas un module « validé » sur la seule base de la présence d'une fonction ou d'un test unitaire : la validation finale exige aussi un parcours réel dans le navigateur.

## 1. Principes de l'audit

Pour chaque module, l'audit vérifie :

- **Fonctionnalité :** parcours complet, création, lecture, modification, suppression, erreurs et états vides.
- **Données visibles :** cohérence des informations affichées, filtres, tris, statuts et mises à jour.
- **Interface :** hiérarchie, densité, alignements, lisibilité, navigation, tableaux, modales et retours d'action.
- **Thèmes :** clair, sombre et automatique, sans dépendance involontaire au thème système lorsque l'utilisateur a choisi un thème manuel.
- **Rôles :** Direction, Professeur et Élève ; le même module peut avoir des parcours distincts.
- **Régressions :** Firefox réel et tests ciblés. Les tests hébergés ne remplacent pas la recette sur l'installation physique.

Les états utilisés dans le registre sont : **confirmé** (défaut reproduit ou prouvé par le code), **à vérifier** (hypothèse ou parcours incomplet), **corrigé en branche** (changement effectué, CI à confirmer), **recette physique restante**.

## 2. Inventaire des modules actifs

### Espace Direction / Professeur

La navigation principale déclare actuellement 14 entrées :

| Module | Identifiant de page | Périmètre principal | État de l'audit |
|---|---|---|---|
| Tableau de bord | \`dashboard\` | Vue d'ensemble, accès rapides et priorités | À vérifier dans le navigateur |
| Centre d'activité | \`activity\` | Actions et événements récents | À vérifier ; chevauchement avec le tableau de bord à mesurer |
| Suivi de classe | `ppDashboard` | Synthèse des classes, assiduité, travaux, évaluations et échéances | Implémenté ; CI #1793 verte, recette réelle à effectuer |
| Emploi du temps | \`schedule\` | Vues jour/semaine/mois, créneaux et couleurs | Parcours Firefox présent ; synchronisation multi-postes en investigation |
| Séances & leçons | \`lessons\` | Contenus, devoirs et pièces jointes | Tests de persistance et parcours élève présents ; audit visuel à poursuivre |
| Élèves | \`students\` | Fiches et suivi | Permissions et périmètres serveur testés ; ergonomie à vérifier |
| Évaluations | \`evaluations\` | Notes, barèmes, critères, compétences et moyennes | Moteur métier et tests présents ; consolidation du code à prévoir |
| Appels | \`attendance\` | Présences, absences et retards | Périmètres et tests existants ; affichage à vérifier |
| Bulletins | \`bulletins\` | Préparation, saisie par matière, validation et publication | Tests de persistance, permissions et PDF présents ; recette complète à refaire |
| Messagerie | \`messages\` | Boîtes, fils, brouillons, copies, pièces jointes | Mail V2 actif ; tests d'identité, de visibilité et de sécurité présents ; recette utilisateur encore nécessaire |
| Cloud | \`documents\` | Espaces personnels, classe, groupe et partages | Permissions serveur et identité des éléments testées ; navigation et rendu à vérifier |
| Professeurs | \`teachers\` | Profils et comptes enseignants | Tests de sécurité et d'identité présents ; ergonomie à vérifier |
| Classes | \`classes\` | Classes, groupes et rattachements | Fusion des données par périmètre testée ; ergonomie à vérifier |
| Paramètres | \`settings\` | Apparence, périodes, salles, stockage, maintenance | Sélecteur de thème présent ; parité visuelle à tester |

### Espace Élève

Les pages élève sont distinctes : \`studentHome\`, \`studentSchedule\`, \`studentLessons\`, \`studentWork\`, \`studentResults\`, \`studentLife\`, \`studentMessages\`, \`studentDocuments\`, \`studentSettings\`.

Points à vérifier : cohérence entre l'accueil et les modules, affichage de l'emploi du temps, visibilité des notes seulement après publication, accès aux bulletins PDF, messagerie, pièces jointes et réglages propres à l'élève.

## 3. Constatations techniques déjà confirmées

### Messagerie — Mail V2

- Les points d'entrée actifs sont \`window.messages\` et \`window.studentMessages\`, tous deux reliés au moteur V21.04 \`renderBox\`. Un ancien \`studentMessages()\` affiche encore un message de fonctionnalité future, mais il est remplacé à l'exécution par l'entrée Mail V2 : ce fragment est un reste de code, pas la page effectivement affichée.
- Le modèle sépare les états par boîte (lu/non lu, dossier, favoris), les destinataires et les brouillons. Les tests couvrent les identités, les destinataires, les CCI, les réponses, les brouillons et la visibilité.
- Les contrôles serveur filtrent les messages, états, dossiers, brouillons et pièces jointes par utilisateur. Des tests de sécurité vérifient les URL de pièces jointes et les périmètres de stockage.
- **Point de vigilance migration :** lorsque \`mailboxV2.resetPending\` est actif, \`activate()\` vide les anciennes collections \`conversations\`, \`messages\` et \`mailFolders\`. Le test V21.04 confirme ce comportement, mais la reprise de données d'anciennes installations doit être documentée et validée avant toute modification. Ce n'est pas déclaré ici comme une perte accidentelle confirmée : cela ressemble à une réinitialisation de migration intentionnelle.
- La présence de l'interface et des tests ne suffit pas à clôturer le signalement historique MAIL-02 : une recette avec un compte élève sur l'installation de référence reste nécessaire.

### Évaluations

- Le dernier moteur actif est le moteur V21.17, qui centralise notes, barèmes, coefficients, critères, compétences et statistiques.
- Plusieurs anciennes définitions de \`evaluations()\` subsistent plus haut dans \`_all.js\`. La dernière définition remplace les précédentes à l'exécution. Cette accumulation est une dette de maintenance : les prochains correctifs doivent viser le point d'entrée actif et éviter de faire diverger les anciens fragments.
- Des tests couvrent les droits par matière, la publication, les barèmes, les compétences et la saisie rapide. Le parcours complet d'un professeur puis d'un élève doit encore être rejoué.

### Bulletins

- Le module actif V21.09 propose le suivi collectif, la saisie par matière et la validation/publication.
- Les tests contrôlent la génération idempotente, la persistance, les droits d'appréciation et la reconstruction des données PDF côté serveur.
- Plusieurs anciennes définitions de \`bulletins()\` subsistent également. Il faudra consolider le code après validation fonctionnelle, sans supprimer les chemins historiques avant d'avoir cartographié leurs dépendances.

### Emploi du temps

- Le rendu professeur et élève s'appuie sur un calendrier commun, avec filtres de classe/groupe et vues jour, semaine et mois.
- Le test Firefox réel vérifie la navigation aujourd'hui/semaine/mois, la création d'un créneau, l'absence de saut de scroll, les couleurs de matière et la structure visuelle comparée entre professeur et élève.
- Un défaut de rendu du calendrier élève a été localisé : le nouveau créneau arrivait dans le modèle et les fonctions de calcul et de génération HTML le renvoyaient, mais le DOM conservait le calendrier précédent. La branche force désormais un nouveau render() lors de l'adoption d'une nouvelle révision lorsque l'utilisateur ne saisit rien. Le test de non-régression est ajouté ; sa validation Firefox sur le dernier commit reste requise.

### Thème clair / sombre

- Le choix utilisateur est stocké localement et appliqué via \`html[data-mc-theme]\`. Les styles principaux de l'application utilisent ce marqueur.
- Certaines règles \`prefers-color-scheme\` découvertes dans \`_all.js\` sont contenues dans le document temporaire produit pour l'impression du bulletin ; elles ne gouvernent pas directement le thème de l'application. Elles ne doivent donc pas être modifiées comme si elles causaient une incohérence générale dans l'interface.
- Aucune validation visuelle globale n'est encore revendiquée. Il faut parcourir les modules en thème clair et sombre, avec le choix manuel opposé au thème du système, et vérifier en particulier tableaux, champs, modales, calendriers, badges, cartes, menu latéral, messagerie et Cloud.

### Structure du code et navigation

- \`_all.js\` concentre une grande partie de la logique et des styles injectés ; plusieurs fonctions de modules sont redéfinies au fil des versions historiques. Cela accroît le risque de corriger une ancienne implémentation qui n'est plus active.
- Le tableau de bord, le Centre d'activité et la page Aujourd'hui peuvent présenter des informations proches. Il faut mesurer les doublons et la valeur réelle de chaque écran avant de proposer une fusion ou une suppression.
- Aucun module ne sera supprimé sur un simple jugement esthétique : il faut vérifier son usage, ses liens depuis les autres écrans et les données dont il est propriétaire.

## 4. Corrections et travaux applicatifs déjà conservés

Ce chantier produit s'ajoute aux correctifs techniques déjà présents dans la branche :

- contrôle d'intégrité des assets de mise à jour ;
- migration d'installation historique V25.0.19 ;
- supervision réseau DHCP Linux/macOS et renouvellement HTTPS ;
- endpoint de révision applicative et synchronisation entre modules ;
- tentative de fusion de modifications concurrentes indépendantes avec détection des conflits.

Ces travaux restent dans la branche et ne doivent pas être annulés par l'audit UX.

## 5. Plan de recette produit

| Lot | Scénarios | Critère de sortie |
|---|---|---|
| PQA-01 — navigation & shell | Toutes les pages Direction/Professeur/Élève, titres, navigation, retours, modales, états vides | Aucun écran cassé, pas de page obsolète ou inaccessible |
| PQA-02 — apparence | Thème clair, sombre, automatique ; thème manuel opposé au système | Contraste et lisibilité cohérents dans chaque module |
| PQA-03 — emploi du temps | Jour/semaine/mois, 7 jours, cours qui se chevauchent, longues matières, classes/groupes, scroll, couleurs | Aucun cours masqué, aucun débordement ou saut visuel |
| PQA-04 — évaluations & bulletins | Saisie, conversion, moyenne, publication différée, appréciations, PDF élève | Les calculs et statuts affichés correspondent aux données publiées |
| PQA-05 — messagerie | Composer, répondre, répondre à tous, transférer, CC/CCI, brouillon, pièce jointe, dossier, archive, suppression, élève/professeur | Aucun message perdu ou visible au mauvais compte |
| PQA-06 — séances & travaux | Créer séance/devoir, fichiers prof, rendu élève, correction, échéance | Parcours complet et fichiers lisibles par les seuls utilisateurs autorisés |
| PQA-07 — Cloud | Personnel/classe/groupe/partagé, aperçu, déplacement, renommage, suppression, recherche et filtres | Actions cohérentes, pas de lien cassé ni de perte silencieuse |
| PQA-08 — vie scolaire & profils | Appels, suivi, notifications, profils, paramètres élève | Informations compréhensibles, droits cohérents, aucune donnée superflue |
| PQA-09 — rationalisation | Tableau de bord, Aujourd'hui, Centre d'activité et modules peu utilisés | Proposition argumentée de fusion/suppression/création, sans retrait avant validation |

## 6. Règles de clôture

Un module ne passe à **corrigé** qu'après un test ciblé ou une reproduction navigateur réussie. Un module ne passe à **validé visuellement** qu'après inspection dans les deux thèmes. Un signalement historique ne passe à **résolu** qu'après un parcours représentatif et, lorsque pertinent, une confirmation sur l'installation de référence.

La liste des anomalies confirmées, des hypothèses et des demandes d'évolution est maintenue dans \`REGISTRE_BUGS_V25.md\`. Le présent document porte le diagnostic produit, les priorités et la recette.



## 7. Résultat de l'investigation EDT — 25/11/2026

Le scénario Firefox « Sciences » a été suivi de bout en bout :

1. `GET /api/sync-status` renvoie la nouvelle révision après l'écriture enseignant.
2. `GET /api/data` renvoie bien le créneau `firefox-live-student-course`.
3. Le navigateur élève a le même SHA de révision et le même créneau dans `db.schedule`.
4. Pour vendredi 13/11/2026, `recurring()`, `dayOcc()` et `studentScheduleOcc()` renvoient tous le créneau.
5. `studentSchedule()` et `scheduleWeek()` génèrent un HTML contenant « Sciences ».
6. En revanche, `.scheduleCalendarSurface` dans le DOM ne contient pas le créneau et son nombre d'éléments avec cet identifiant reste nul.

**Conclusion :** la donnée, la récurrence et le gabarit fonctionnent dans ce cas ; le point défaillant était le rafraîchissement du DOM après la nouvelle révision. Le code de synchronisation ne relançait le rendu que si la comparaison JSON indiquait une différence. Le garde-fou est désormais plus robuste : dès qu'une nouvelle révision est adoptée alors qu'aucune saisie locale ou modale n'est active, le module visible est reconstruit, même si le modèle en mémoire semble déjà à jour.

Un test supplémentaire vérifie que le DOM doit être reconstruit sur une nouvelle révision même si le JSON local est identique au JSON reçu. La correction reste au statut **candidate dans la branche** jusqu'à la réussite du workflow Linux/macOS/Firefox sur le dernier SHA et une recette visuelle.
## 8. Régression globale de rendu — 25/11/2026

Le premier scénario Firefox V25.0.25 échouait avant même l'affichage du calendrier. Le diagnostic enrichi a identifié l'erreur exacte : \`ReferenceError: today is not defined\`, levée lors de la construction de la table des vues dans \`render()\`.

La route \`today\` avait été redirigée vers le Centre d'activité dans \`go()\`, mais une ancienne entrée \`today:today\` subsistait dans la table de rendu alors que la fonction \`today()\` avait été retirée. Comme cette table est construite à chaque rendu, l'erreur bloquait aussi les pages qui n'avaient aucun rapport avec l'écran Aujourd'hui.

**Correction candidate dans la branche :** l'entrée \`today\` de la table de rendu pointe désormais vers \`studentActivityCenter\` pour un élève et vers \`activity\` pour les autres rôles, comme la route \`activity\`. La compatibilité est ainsi gérée au niveau du moteur, sans alias global dans \`index.html\`. Le test Firefox confirme à nouveau le rendu, la navigation jour/semaine/mois, la création d'un créneau, l'enregistrement, la synchronisation inter-comptes et la parité structurelle de l'EDT élève/professeur.

Le diagnostic Firefox conserve désormais dans le message d'échec l'état d'authentification, \`lastRenderError\`, le HTML réel de \`#main\`, les révisions de synchronisation et les vraies erreurs JavaScript/console collectées par Playwright. Cela évite de confondre une erreur de rendu générale avec un défaut de calendrier.

## 9. Recette visuelle automatisée — 25/11/2026

Le workflow Firefox génère des captures de modules en thème clair et sombre, en plaçant volontairement le thème système à l'opposé du thème MaClasse choisi. Les contrôles examinés comprennent notamment l'accueil, le Centre d'activité, l'EDT, les séances, les évaluations, les bulletins, la messagerie, le Cloud, les paramètres, les pages élève et les écrans de vie scolaire.

L'inspection des captures confirme que les thèmes clair et sombre sont appliqués même lorsque le thème système est volontairement inversé. Elle a toutefois révélé un défaut précis : un pseudo-élément blanc hérité des surfaces vitrées restait visible au-dessus des cartes en mode sombre. Ce reflet éclaircissait les cartes de manière irrégulière. Le rendu est corrigé dans la branche en supprimant ce reflet uniquement en thème sombre. La comparaison de l'EDT professeur/élève confirme la même structure de calendrier et l'absence des commandes d'édition côté élève.

**Limites à conserver :** les captures reposent sur des données de test minimales et ne valident pas tous les états chargés d'un établissement réel. Les contextes Firefox sont maintenant créés et contrôlés en \`fr-FR\`, fuseau \`Europe/Paris\`. Malgré cela, les champs natifs \`input[type=date]\` apparaissent encore au format \`mm/dd/yyyy\` dans les captures Linux CI ; leur présentation dépend du moteur et de l'environnement graphique. Le format devra être confirmé sur Firefox/macOS en français avant de conclure sur l'affichage des dates.

Les captures et tests CI ne remplacent pas la recette physique sur le Mac Apple Silicon de référence, ni la vérification d'une installation ayant des données historiques. Les modules ne sont pas déclarés définitivement validés sur cette seule base.

## 10. Cohérence de la semaine dans Séances & leçons — 25/11/2026

Les captures ont révélé un décalage entre la date sélectionnée dans le cahier de cours et la colonne « Semaine » : le centre pouvait afficher le mercredi 25 novembre alors que la navigation rapide montrait encore la semaine du 9 au 15 novembre.

La cause était une fonction \`weekDates()\` qui lisait toujours la variable globale \`selectedWeek\`, alors que les vues professeur et élève lui transmettaient déjà la date \`lessonDay\`. L'argument était donc ignoré. La fonction accepte désormais une date de référence optionnelle et calcule la semaine correspondante. Le libellé du mini-calendrier utilise également le mois abrégé pour éviter la troncature dans la colonne étroite.

Un contrôle Firefox supplémentaire vérifie que la semaine affichée contient la date sélectionnée dans les deux espaces. Le workflow #1679, sur le commit `7380a1c`, a passé les trois jobs : tests Linux, régression Firefox réelle et validation macOS (installateur Apple Silicon, service `launchd` et tests Python). La correction est donc validée par la CI ; la recette sur l'installation physique reste nécessaire.

## 11. Finition du tableau de bord — 25/11/2026

La relecture du tableau de bord a révélé des libellés de compteurs générés sous la forme « créneau(x) » et « travail(aux) », ainsi qu'un manque d'espacement entre l'intitulé du cours et le nom de la classe. Les compteurs utilisent maintenant des formulations françaises accordées au nombre et les informations du cours sont visuellement séparées.

Un contrôle de cohérence statique empêche le retour des marqueurs de pluriel entre parenthèses. Cette correction améliore la lisibilité sans modifier les calculs ni les données.

## 12. Audit visuel approfondi — 25/11/2026

### Inspection réelle des captures

L'archive de captures Firefox précédant ce lot contient 54 images : pages de l'espace professeur et de l'espace élève, chacune en clair et sombre. La préférence MaClasse a été placée à l'opposé du thème système pour détecter les styles CSS qui dépendraient à tort de `prefers-color-scheme`.

Constats :
- Les surfaces principales, la barre latérale, les tableaux, les formulaires, la messagerie et les pages élève suivent globalement le thème choisi.
- Le calendrier reste lisible dans les deux thèmes ; les cours conservent leurs couleurs de matière. L'espace élève n'expose pas les commandes de modification du professeur.
- Le thème sombre avait un reflet blanc diagonal sur les cartes et les bulletins, provenant de `::before`. Le correctif neutralise ce reflet seulement en sombre, sans modifier les finitions du thème clair.
- Plusieurs compteurs métier affichaient des accords de développement (« créneau(x) », « séance(s) », « 1 élèves », « événement(s) »). Un helper `countLabel` produit désormais les formes françaises singulier/pluriel sur les écrans Emploi du temps, Séances & leçons et Paramètres.

### Fiabilité du contrôle des écrans

La relecture du test a également montré que certaines captures portaient le nom d'une page qui n'était pas réellement distincte :
- `today` et `notifications` redirigent vers le Centre d'activité.
- `studentWork` est un alias de `studentLessons` ; le travail à faire est présenté comme un onglet de ce module, pas comme une page autonome.
- Le parcours élève propose trois états distincts dans Séances & leçons : contenu de séance, devoir à la maison et travaux à faire.

Le test de capture a été ajusté pour ne plus présenter ces alias comme des écrans supplémentaires. Il capture les états réels du module élève et contrôle maintenant la présence d'un titre, le thème effectivement appliqué, l'absence de débordement horizontal au viewport de recette et la disparition du reflet sur les cartes sombres.

### Périmètre restant

Ce lot améliore le contrôle visuel, mais ne transforme pas les captures en validation fonctionnelle exhaustive. Les données de démonstration sont volontairement minimales ; les tableaux très remplis, les longues chaînes, les gros volumes Cloud, les conversations longues et les formulaires complexes doivent encore être parcourus avec des jeux de données plus denses. La recette responsive sur plusieurs largeurs, l'accessibilité clavier/lecteur d'écran et la vérification native des champs de date sur Firefox/macOS restent à poursuivre.

Les tests interactifs Firefox couvrent déjà des parcours concrets (navigation et synchronisation de l'EDT, création de cours, séance avec pièce jointe et remise élève, messagerie avec reprise de brouillon et nouvel essai après échec réseau, et périmètre Cloud élève). Ils ne signifient pas que chaque action de chaque module a été testée. Les modules restent donc suivis individuellement dans le registre des anomalies et le plan PQA.


### Correctifs UI complémentaires — même audit

Le passage transversal a également relevé des libellés de quantité non accordés hors du tableau de bord : fiches professeurs, profil enseignant, appels, suivi du professeur principal, gestion des cours, restauration, import Cloud et arborescence documentaire. Ces affichages actifs utilisent maintenant le helper commun `countLabel`, avec les formes irrégulières françaises nécessaires (par exemple « travaux »).

Le Cloud élève était présent comme écran et ses règles de lecture seule étaient couvertes par les tests serveur, mais il n'était pas exposé dans la navigation latérale. Une entrée « Cloud » est ajoutée dans la section « Ressources » de l'espace élève ; le test Firefox doit ouvrir cette page depuis le menu, pas seulement l'appeler directement.

Les titres de dates du cahier de cours et du calendrier n'utilisent plus `text-transform: capitalize` sur toute la chaîne : seul le premier caractère du titre est capitalisé, les noms de mois restent en minuscules selon l'usage français.

La nouvelle recette navigateur a généré 74 captures PNG : 48 états desktop (14 écrans Direction/Professeur et 10 états élève, en clair et sombre), 2 captures supplémentaires de composition d'un mail (clair/sombre), et 24 captures mobiles à 390 px sur les écrans représentatifs (6 par rôle et par thème). Elle vérifie aussi les écrans représentatifs à 900 px et 390 px, les débordements horizontaux du document, le titre de page, l'application du thème sélectionné malgré un thème système opposé, et le comportement automatique lors du basculement système clair/sombre. Ces contrôles sont des garde-fous de mise en page, pas un test complet de chaque interaction responsive.

**Validation CI du lot UI :** le workflow #1717 (run `45664713921`, commit `cce2d2b`) est entièrement vert sur Linux, Firefox réel et macOS Apple Silicon. Il inclut l'installation macOS, le démarrage du service réel `launchd` et la suite complète des tests Python. Les captures de ce run ont été inspectées ; les corrections du reflet sombre et du layout mobile ont été confirmées visuellement sur les écrans représentatifs. La vérification native des champs de date sur le Mac physique reste à faire.


### Champs de date natifs — limite identifiée

Sur le runner Firefox Linux, les champs `input[type=date]` des périodes scolaires s'affichent au format natif américain malgré le contexte navigateur `fr-FR` et le document `lang="fr"`. Le stockage et la valeur ISO restent corrects, mais la présentation peut prêter à confusion pour un utilisateur français. Le format natif dépend aussi de la plateforme et des paramètres régionaux : l'affichage doit être contrôlé sur Firefox/macOS du Mac cible avant de décider s'il faut conserver le champ natif ou construire un contrôle de date localisé. Aucun format n'est changé arbitrairement à ce stade.


## 13. Correction du layout mobile et validation finale — 25/11/2026

### Défaut responsive reproduit

L'inspection des captures mobiles du run précédent a révélé un défaut qui échappait au contrôle de débordement horizontal : sous 800 px, une ancienne règle CSS empilait la barre latérale au-dessus du contenu, tandis qu'une règle plus récente conservait sur `.main` la marge et la largeur calculées pour la barre latérale desktop réduite à 76 px. Le contenu principal se retrouvait donc comprimé et partiellement masqué, même si `document.scrollWidth` restait dans la largeur du viewport à cause de `overflow-x:hidden`.

### Correction appliquée

Sous 800 px, MaClasse utilise maintenant une vraie composition mobile :
- barre de navigation dans le flux, en haut de page, sur toute la largeur ;
- navigation horizontale défilante avec les libellés visibles ;
- groupes de navigation déployés en une seule rangée ;
- contenu principal sans marge latérale desktop, sur toute la largeur utile ;
- comportement identique même lorsqu'un état « menu réduit » avait été mémorisé sur l'appareil.

La navigation mobile reste volontairement compacte et défilante : le produit demeure desktop-first et ce lot ne constitue pas une refonte mobile complète de chaque écran.

### Vérification

Le test Firefox calcule maintenant non seulement la largeur du document, mais aussi les limites réelles des surfaces de contenu principales. Il vérifie les vues représentatives à 900 px et 390 px, en clair et sombre. Une assertion spécifique empêche qu'une page semble tenir dans l'écran alors que ses blocs sont comprimés ou masqués.

Le run #1717 a produit et publié 74 captures PNG ; les 24 captures à 390 px et les états desktop représentatifs ont été inspectés. L'espace élève, le Cloud, la messagerie, les paramètres, le cahier de cours et l'EDT sont visibles dans leur largeur utile. Le calendrier hebdomadaire conserve son défilement horizontal interne, qui est attendu pour présenter les sept jours.

**Résultat CI #1717 :** trois jobs réussis — tests Linux, Firefox réel et validation macOS Apple Silicon. Le job macOS comprend l'installateur, le service `launchd` et tous les tests Python.

### Réserves qui demeurent

- Les champs natifs de date doivent être vérifiés sur Firefox/macOS du Mac physique pour confirmer leur présentation française ; leur valeur ISO et le stockage ne sont pas modifiés.
- Les données de capture restent peu volumineuses : les listes très longues, les textes exceptionnellement longs, les gros dossiers Cloud et les conversations massives demandent une recette avec des données plus denses.
- L'accessibilité complète au clavier et aux lecteurs d'écran n'est pas certifiée par les captures et reste à auditer.
- Le passage CI sur un runner macOS Apple Silicon ne remplace pas une installation/recette finale sur le Mac cible et ses données historiques.


## 14. Corrections produit complémentaires — 25/11/2026

### Messagerie élève — cohérence des destinataires

La projection serveur de l'élève construit maintenant la liste des enseignants joignables à partir des droits réellement calculés par `_student_accessible_teacher_ids` : titulaires, co-enseignants, enseignants des séances et affectations actives. L'interface élève ne réduit plus une seconde fois cette liste aux seuls titulaires. Un test Python couvre l'inclusion des enseignants autorisés et l'exclusion d'un enseignant hors périmètre.

**État :** correctif dans la branche et tests CI verts ; la connexion et l'envoi d'un message depuis un vrai compte élève de l'installation de référence restent à confirmer.

### Bulletins — cohérence entre publication et export PDF

Le contrôle de lecture du PDF utilise maintenant le statut officiel strict (`validated is True` et `published is True`) sans exiger la présence d'un horodatage `publishedAt`. Cette date reste une métadonnée d'affichage ; son absence sur un ancien bulletin ne doit pas annuler une publication déjà validée. La page Résultats ne propose que les bulletins officiellement publiés et validés.

**État :** tests de propriété du bulletin, de refus des bulletins non officiels et de compatibilité des données anciennes passés en CI ; recette depuis un compte élève réel et un poste client reste nécessaire. BUL-02/BUL-03 ne sont donc pas clos.

### Emploi du temps — couleurs et thème sombre

Deux causes concrètes ont été corrigées :
- la fusion des sauvegardes professeur restaurait l'objet `settings` du serveur et annulait les nouvelles couleurs ; `subjectColors` est désormais fusionné côté serveur, uniquement pour les matières que le professeur est autorisé à enseigner ;
- le fond blanc de la grille journalière venait d'un `background-image` répétitif qui n'était pas remplacé par l'ancienne règle `background-color` du thème sombre ; la grille reçoit maintenant un dégradé sombre explicite.

Des tests vérifient le filtrage des couleurs par matière et l'apparence du fond sombre.

**État :** code et tests verts ; rendu sur des données denses, semaine/jour/mois et couleurs personnalisées à confirmer sur le Mac et le PC Fedora.

### Limites toujours suivies

- BUL-02 : accès PDF depuis un poste client du réseau à valider physiquement.
- BUL-03 : parcours complet d'ouverture d'un bulletin depuis le compte élève à valider physiquement.
- MAIL-02 : accès élève à confirmer avec un vrai compte sur l'installation de référence.
- BUL-04 : persistance et réouverture des campagnes/bulletins à auditer.
- AFFECT-02 : découvrabilité et gestion des remplacements à reprendre.
- UI-ADM-01, UI-SET-01 et UI-PROFIL-01 : contrôles de finition de l'interface à compléter.
- Accessibilité clavier/lecteurs d'écran et écrans très denses : non certifiés par l'audit actuel.


## 15. Accessibilité des remplacements et contrôles UI complémentaires — 25/11/2026

### Remplacements / co-enseignement

La gestion des affectations temporaires existait dans le détail du créneau EDT, avec contrôles par rôle et attribution du créateur. Son principal défaut était la découvrabilité. Un nouvel accès « Remplacements & co-enseignement » est ajouté à la barre d'actions de l'EDT. Il ouvre un répertoire filtrable des seuls créneaux autorisés, avec recherche par classe, matière, jour et horaire. Le bouton « Gérer » ouvre le gestionnaire existant, sans dupliquer les règles métier. Les exceptions ponctuelles restent dans le gestionnaire des exceptions.

### Confidentialité Administration

Le message d'information des comptes a été actualisé : il ne présente plus la messagerie et le Cloud élève comme désactivés. Il indique que les données, messages, pièces jointes et ressources restent filtrés côté serveur par identité et autorisations.

### Contrôles supplémentaires

- Le test de persistance des bulletins couvre la génération idempotente, l'attente de confirmation serveur et le rollback en cas d'échec.
- Les tests UI vérifient les dimensions fixes de la navigation, la densité des paramètres, la séparation des champs de profil, la version partagée et la composition de la rubrique Vie scolaire.
- Ces tests contrôlent la présence des règles et la logique des fonctions ; ils ne remplacent pas une inspection visuelle avec des données denses dans les trois espaces.


## 16. Dette de code et portée réelle de la revue visuelle — 25/11/2026

### Dette de maintenance dans les fichiers applicatifs

Le relevé statique de la branche donne les ordres de grandeur suivants :
- `_all.js` : 2 076 lignes, environ 630 Ko et 551 déclarations de fonctions.
- 26 noms de fonctions sont déclarés plusieurs fois dans ce même fichier. `evaluations()` apparaît cinq fois ; `bulletins()`, trois fois. Plusieurs autres moteurs et handlers possèdent deux ou trois déclarations.
- `index.html` : environ 262 Ko, avec plusieurs blocs CSS historiques qui redéfinissent les mêmes sélecteurs. Exemples : `.top` apparaît dix fois, `.scheduleGrid` sept fois, et `.side`, `.main`, `.event` ou `.card` plusieurs fois.
- `server.py` : 3 101 lignes ; deux fonctions locales nommées `contains` ont été relevées dans des portées distinctes.

Ces doublons ne prouvent pas à eux seuls un bug : les déclarations JavaScript successives remplacent les implémentations précédentes dans le contexte global, et les règles CSS tardives peuvent être des surcharges intentionnelles. Ils rendent toutefois difficile l'identification du code actif et augmentent le risque de corriger une ancienne définition au lieu de celle réellement appelée.

**Décision pour V25.0.25 :** pas de suppression massive de fonctions ou de règles CSS dans cette branche de stabilisation. La consolidation doit être un chantier séparé, avec cartographie des appels HTML inline, fonctions exportées, événements et tests de chaque module.

### Plan de nettoyage post-livraison

1. Cartographier les fonctions actives et les références dynamiques, puis consolider les moteurs Évaluations et Bulletins en premier.
2. Supprimer les anciennes implémentations uniquement après preuve qu'elles ne sont plus appelées et que tous les tests de rôle/parcours passent.
3. Déplacer progressivement les styles communs, les variantes thème clair/sombre et les règles mobile vers des feuilles organisées par module ; comparer les captures avant/après.
4. Conserver un commit par module nettoyé pour faciliter le retour arrière et l'identification des régressions.

### Inspection des captures Firefox

Le workflow #1754 a publié un artefact de 74 captures : écrans Professeur et Élève, thèmes clair/sombre et plusieurs dimensions mobiles. Les vues Emploi du temps, Paramètres, Résultats, Vie scolaire et Messagerie ont été examinées sur un échantillon de ces captures.

Constats :
- les surfaces clair/sombre et les principaux espacements sont cohérents sur les écrans examinés ;
- l'EDT mobile reste défilant horizontalement pour afficher la semaine complète ; la navigation supérieure est également horizontale et une partie des libellés n'est pas visible sans défilement ;
- les vues élève Messagerie et Résultats ont une structure lisible en largeur étroite, mais l'empilement de la boîte de réception et du panneau de lecture allonge la page ;
- les captures automatisées contiennent peu de données de démonstration ; elles ne certifient pas les états avec classes nombreuses, longues listes de messages ou profils incomplets ;
- la campagne de captures porte sur les espaces Professeur et Élève ; l'espace Direction doit encore bénéficier d'une recette visuelle complète distincte.

**Limite de validation :** les captures montrent le rendu d'un navigateur Firefox de CI. Elles ne remplacent pas une recette sur l'installation utilisateur, sur des données réelles anonymisées, ni un contrôle clavier/lecteur d'écran.


## 17. Authenticité des mises à jour — signature Ed25519

Le SHA-256 précédent liait le contenu de l'archive au manifeste de la release, mais ne garantissait pas que le manifeste provenait de l'éditeur. Le candidat V25.0.25 ajoute une signature détachée Ed25519.

- `release_signing.py` charge une clé publique épinglée et valide la signature sur les octets exacts du JSON.
- `update_manager.py` exige exactement un asset `maclasse-update.sig` et refuse une release non signée, une clé absente, une signature malformée ou une clé qui ne correspond pas.
- `scripts/generate_release_signing_key.py` génère localement la paire ; la clé privée reste dans le dossier utilisateur hors du dépôt.
- `scripts/sign_release.py` signe le manifeste dans le workflow avec le secret GitHub Actions `MACLASSE_RELEASE_SIGNING_KEY_B64`. Le script vérifie que la clé privée correspond à la clé publique versionnée, sans afficher le secret.
- Le workflow publie les trois assets : archive, manifeste et signature.
- Les tests couvrent la signature correcte, un manifeste modifié, une mauvaise clé, une signature absente et un contenu malformé.

**État : code ajouté, provisionnement réel non effectué.** Le fichier public du dépôt est volontairement non configuré ; il faut générer la paire sur un poste de confiance, committer la clé publique et créer le secret GitHub avant de publier une release. Le workflow de publication sera volontairement en échec tant que l'éditeur n'aura pas effectué cette opération. La première mise à niveau depuis V25.0.23 ne peut pas être authentifiée par un ancien updater qui ne connaissait pas Ed25519 ; la signature protège strictement le flux après installation du pont V25.0.25.


### Retour CI #1758 — fixture launchd macOS

Le run #1758 a validé Linux, dont les tests Ed25519, et Firefox réel. Le seul échec macOS venait du test de démarrage HTTPS sous launchd : le répertoire temporaire de ce test n'emportait pas le nouveau module `release_signing.py` pourtant importé par `update_manager.py`. La copie du module est ajoutée au fixture de serveur réel et une assertion confirme sa présence. La validation macOS doit être relancée ; aucun assouplissement du test launchd n'est fait.


## 18. Validation de la chaîne Ed25519 et du fixture macOS — 25/11/2026

Le workflow [#1759](https://github.com/WedoneOfficiel/Ma-Classe/actions/runs/45704572819) est entièrement vert sur la tête `b3f44aa` :
- tests Linux, y compris les scénarios de signature Ed25519 ;
- régression EDT Firefox réel ;
- macOS Apple Silicon, installateur, tests JavaScript, démarrage HTTPS réel sous launchd et tests Python complets.

Le workflow #1758 avait échoué uniquement parce que le test launchd copiait le serveur et le gestionnaire sans copier le nouveau module `release_signing.py`. Le fixture a été complété ; le test lance maintenant le vrai serveur et répond en HTTPS sous launchd.

**Limites non automatisables restantes :**
- génération de la paire de clés de l'éditeur et création du secret GitHub Actions ;
- validation de la clé avec une release de test ;
- migration d'une copie représentative des données de l'installation réelle ;
- recette Wi-Fi multi-appareils et certificat approuvé sur le réseau cible ;
- parcours complets avec comptes Direction, Professeur, Élève et remplaçant sur les appareils de référence.

Les tests CI s'appuient sur une clé éphémère uniquement. La clé publique d'éditeur du dépôt reste volontairement non configurée tant que son propriétaire n'a pas procédé au provisionnement.


## 19. Validation finale des outils Ed25519 — workflow #1763

Le commit `b06f8ef` a passé les trois jobs Linux, macOS Apple Silicon et Firefox réel. En plus de vérifier la cryptographie, les tests exécutent maintenant le générateur de paire de clés et le script de signature en sous-processus : permissions de la clé privée, signature valide, refus lorsque le secret manque et absence de fichier de signature en cas de refus. Les secrets ne sont pas affichés et les clés de test restent temporaires.

Le fichier public épinglé par MaClasse demeure volontairement à l'état non configuré. Le mécanisme est donc testé, mais l'authenticité d'une future release réelle dépend encore du provisionnement de la paire éditeur et du secret GitHub Actions.


## 10. Nouvelle vue « Suivi de classe » — 25/11/2026

La vue transversale est implémentée dans `class_tracking.js` et réutilise la route historique `ppDashboard` afin de conserver les liens déjà présents dans les profils et les classes.

### Accès et cloisonnement

- Direction : toutes les classes disponibles dans son espace.
- Professeur : classes issues des affectations pédagogiques actives et classes dont il est professeur principal.
- Professeur non-PP : travaux et évaluations limités aux matières sur lesquelles ses affectations lui donnent accès.
- Professeur principal : vue transversale de sa classe, en cohérence avec sa responsabilité de classe.
- Élève : aucun accès à cette vue.
- La sélection d'une classe est revalidée contre la liste accessible avant affichage. Un accès de retour à la liste est disponible depuis la fiche de classe.
- Les raccourcis vers les modules conservent le contexte de classe.

### Informations affichées

- Effectif de la classe.
- Absences et retards sur les 30 derniers jours.
- Travaux nécessitant un dépôt dont l'échéance est passée et pour lesquels aucun dépôt n'a été reçu.
- Dernières évaluations effectivement publiées, avec le nombre de notes publiées dans le périmètre de la classe ou du groupe.
- Prochaines échéances.
- Tableau des élèves avec accès direct à leur fiche et à leur suivi individuel.

Aucun score de risque, classement ou seuil automatique n'est calculé. Les nombres affichés sont des décomptes factuels, avec une période explicitement indiquée pour l'assiduité. Les évaluations non publiées, programmées dans le futur et les notes d'un autre groupe sont exclues des indicateurs.

### Tests et validation

- `tests/test_v25_class_tracking.js` couvre le périmètre Direction/Professeur/Élève, la fenêtre de 30 jours, les groupes, les travaux rendus, les échéances et la publication des évaluations.
- Le parcours Firefox réel vérifie l'ouverture du module, la sélection d'une classe accessible, le retour à la liste et le refus d'accès depuis un compte élève. Le workflow peut aussi être lancé manuellement depuis GitHub Actions pour valider explicitement la dernière tête de branche.
- La validation CI de cette nouvelle tête et l'inspection visuelle des captures restent nécessaires avant de déclarer la fonctionnalité validée.


## 11. Navigation Cloud après un suivi de classe — 25/11/2026

Le contexte de classe est désormais libéré lorsque l'utilisateur choisit un espace Cloud personnel, partagé, de groupe ou documentaire. Il reste conservé pour l'espace « Classe », afin de garder le raccourci vers la classe courante.

Le changement d'espace passe par `setCloudSpace()`, qui réinitialise également le chemin, la sélection et les filtres. Le test Firefox vérifie l'espace réellement rendu, l'absence de colonne latérale dans les espaces personnels/partagés et le maintien de la navigation latérale pour l'espace classe.
