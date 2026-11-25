# Audit produit MaClasse V25 — modules, ergonomie et rendu

**État : audit en cours — 25 novembre 2026**  
**Périmètre :** interface web, modules métier, cohérence visuelle, parcours Direction / Professeur / Élève.  
**Branche de travail :** \`feat/v25.0.25-stabilisation-reseau-migrations\`  
**Référence actuelle :** PR #13, non fusionnée.

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

La navigation principale déclare actuellement 13 entrées :

| Module | Identifiant de page | Périmètre principal | État de l'audit |
|---|---|---|---|
| Tableau de bord | \`dashboard\` | Vue d'ensemble, accès rapides et priorités | À vérifier dans le navigateur |
| Centre d'activité | \`activity\` | Actions et événements récents | À vérifier ; chevauchement avec le tableau de bord à mesurer |
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

La nouvelle recette navigateur génère 48 captures de véritables états (14 écrans Direction/Professeur et 10 états élève, en clair et sombre). Elle vérifie aussi les écrans représentatifs aux largeurs de 900 et 390 px, les débordements horizontaux du document, le titre de page, l'application du thème sélectionné malgré un thème système opposé, et le comportement automatique lors du basculement système clair/sombre. Ces contrôles sont des garde-fous de mise en page, pas un test complet de chaque interaction responsive.

**Validation en attente sur le dernier commit UI :** la précédente validation complète #1680 reste verte pour le lot V25.0.25 avant ces ajustements d'interface. Les corrections UI et les nouveaux contrôles doivent encore obtenir leur propre passage complet Linux, Firefox réel et macOS. Les captures de la nouvelle exécution devront être inspectées avant d'affirmer que le reflet sombre a disparu visuellement sur tous les écrans.
