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

Une première inspection des captures disponibles ne révèle pas de rupture générale du thème sombre ni de défaut structurel majeur sur les écrans représentatifs. L'EDT élève et professeur conserve la même structure de calendrier ; l'interface élève ne présente pas les commandes d'édition du professeur.

**Limites à conserver :** les captures reposent sur des données de test minimales et ne valident pas tous les états chargés d'un établissement réel. Les contextes Firefox sont maintenant créés et contrôlés en \`fr-FR\`, fuseau \`Europe/Paris\`. Malgré cela, les champs natifs \`input[type=date]\` apparaissent encore au format \`mm/dd/yyyy\` dans les captures Linux CI ; leur présentation dépend du moteur et de l'environnement graphique. Le format devra être confirmé sur Firefox/macOS en français avant de conclure sur l'affichage des dates.

Les captures et tests CI ne remplacent pas la recette physique sur le Mac Apple Silicon de référence, ni la vérification d'une installation ayant des données historiques. Les modules ne sont pas déclarés définitivement validés sur cette seule base.

## 10. Cohérence de la semaine dans Séances & leçons — 25/11/2026

Les captures ont révélé un décalage entre la date sélectionnée dans le cahier de cours et la colonne « Semaine » : le centre pouvait afficher le mercredi 25 novembre alors que la navigation rapide montrait encore la semaine du 9 au 15 novembre.

La cause était une fonction \`weekDates()\` qui lisait toujours la variable globale \`selectedWeek\`, alors que les vues professeur et élève lui transmettaient déjà la date \`lessonDay\`. L'argument était donc ignoré. La fonction accepte désormais une date de référence optionnelle et calcule la semaine correspondante. Le libellé du mini-calendrier utilise également le mois abrégé pour éviter la troncature dans la colonne étroite.

Un contrôle Firefox supplémentaire vérifie que la semaine affichée contient la date sélectionnée dans les deux espaces. Le correctif reste en attente de la réussite du workflow sur le dernier commit.

## 11. Finition du tableau de bord — 25/11/2026

La relecture du tableau de bord a révélé des libellés de compteurs générés sous la forme « créneau(x) » et « travail(aux) », ainsi qu'un manque d'espacement entre l'intitulé du cours et le nom de la classe. Les compteurs utilisent maintenant des formulations françaises accordées au nombre et les informations du cours sont visuellement séparées.

Un contrôle de cohérence statique empêche le retour des marqueurs de pluriel entre parenthèses. Cette correction améliore la lisibilité sans modifier les calculs ni les données.

