# Registre des bugs — MaClasse V25

**Document de référence des anomalies remontées et de leur résolution.**  
Branche de travail : `fix/v25-student-teacher-workflows`  
Dernière mise à jour : 15 novembre 2026

## Règles de suivi

- **Détecté** : le problème est identifié, mais aucun correctif n'est encore engagé.
- **En cours de résolution** : diagnostic et/ou correctif en cours ; tests ou recette restent à faire.
- **Résolu** : le correctif est intégré et validé par les tests pertinents ainsi que par la recette fonctionnelle nécessaire.
- Un test automatisé réussi ne suffit pas à lui seul à déclarer résolu un bug qui nécessite une vérification visuelle ou un parcours réel avec plusieurs rôles.
- Chaque anomalie conserve son identifiant dans le journal technique `SUIVI_CORRECTIFS_V25.md`.

## Tableau de suivi

| Identifiant | Bug | Description simple du bug | Description détaillée | État |
|---|---|---|---|---|
| EDT-01 | Différence d'affichage des emplois du temps | L'emploi du temps n'a pas le même aspect pour un élève et un professeur. | Les deux espaces utilisaient des structures et des assemblages visuels différents, même si une partie du moteur de calendrier était commune. La vue élève a été rapprochée de la structure et des composants de la vue professeur, tout en conservant ses restrictions. Il reste à comparer les vues réelles dans le navigateur (jour, semaine et mois) pour confirmer la parité visuelle. | En cours de résolution |
| EDT-02 | Rechargement apparent après enregistrement d'un créneau | Quand on enregistre un créneau, la page semble se décharger ou se recharger. | Le parcours de sauvegarde provoquait un rendu global de l'application après la confirmation serveur, donnant une impression de rechargement et pouvant faire perdre le contexte visuel. Un rafraîchissement ciblé du calendrier et la conservation de la position de défilement ont été mis en place. Les tests automatisés passent ; il reste à vérifier le parcours complet en utilisation réelle, y compris en cas d'erreur serveur. | En cours de résolution |
| EDT-03 | Couleur personnalisée des matières | On ne peut pas choisir librement la couleur d'une matière. | Le formulaire de créneau ne proposait pas de choix de couleur et la couleur était déterminée automatiquement. Un sélecteur et une préférence globale `settings.subjectColors` ont été ajoutés, avec transmission aux espaces professeur et élève. Il reste à vérifier qu'une couleur choisie est cohérente dans toutes les classes, tous les créneaux et les deux types de comptes. | En cours de résolution |
| SEC-01 | Droits d'édition indus dans l'EDT élève | Un élève voit ou peut déclencher des commandes qui devraient être réservées aux professeurs. | Les commandes de modification des séances/créneaux et les zones de dépôt drag-and-drop doivent être absentes de l'espace élève. Le serveur doit également refuser toute tentative d'écriture falsifiée, même si elle est envoyée hors de l'interface. Les contrôles d'interface et les tests de refus serveur sont en place et passent ; une vérification avec un vrai compte élève reste à effectuer. | En cours de résolution |
| ELEVE-01 | Absence de paramètres adaptés à l'élève | L'espace élève ne dispose pas d'un véritable module Paramètres. | La navigation élève ne proposait pas de module dédié et les paramètres globaux d'administration ne sont pas adaptés à ce rôle. Un écran Paramètres élève a été ajouté avec profil en lecture seule, changement de mot de passe et préférence de thème locale. Le parcours doit encore être vérifié avec un compte élève réel, notamment la persistance des préférences et les limites d'accès. | En cours de résolution |
| MAIL-01 | Messagerie élève inaccessible ou défaillante | L'élève ne peut pas accéder normalement à la messagerie ; le widget d'accueil ne fonctionne pas correctement. | L'ancien écran élève indiquait que la messagerie arriverait ultérieurement et la projection serveur masquait volontairement les conversations. Une interface élève et une projection serveur cloisonnée ont été ajoutées : conversations autorisées, brouillons, pièces jointes et confidentialité des destinataires. Les tests de périmètre élève/professeur et de pièces jointes passent dans la CI ; une recette réelle avec au moins un compte élève et un compte professeur reste indispensable. | En cours de résolution |
| BUL-01 | Remplissage des bulletins refusé | Lorsqu'on veut remplir un bulletin, l'application refuse de remplir une case. | Le signalement initial mentionne le message « Vous ne pouvez pas remplir cette case ». Le contrôle des droits d'appréciation a été corrigé pour tenir compte de la matière, des accents, des remplacements ponctuels et de la période du bulletin plutôt que de la seule situation actuelle. Des tests couvrent notamment un enseignant qui a assuré une matière pendant une période passée. Le texte exact du message initial n'a pas été retrouvé tel quel dans le code frontend actuel : il faut encore reproduire le parcours complet avec un compte enseignant, identifier le contrôle qui bloque éventuellement la saisie, puis vérifier l'enregistrement et la publication. | En cours de résolution |

## État global

- Bugs suivis : **7**
- Résolus : **0**
- En cours de résolution : **7**
- Détectés sans correctif engagé : **0**

Ce bilan est volontairement prudent : les tests automatisés sont verts sur la tête de branche vérifiée, mais les recettes fonctionnelles réelles ne sont pas toutes terminées.
