# Registre de suivi — correctifs V25

Ce fichier est le journal de référence des problèmes remontés, des vérifications, des modifications et de leurs résultats. Il doit être mis à jour à chaque intervention, y compris lorsqu'un correctif échoue ou qu'un diagnostic invalide une hypothèse. Ne pas rouvrir un problème déjà résolu sans élément nouveau.

## Campagne du 15 novembre 2026 — EDT, espace élève, messagerie et bulletins

**Branche de travail :** `fix/v25-student-teacher-workflows`  
**Base :** `main` au démarrage de la campagne (V25.0.22, commit de fusion précédent `8546a2be89c0bf463588abafa87003d433d62e57`).  
**Statut global :** diagnostic en cours. Aucun correctif fonctionnel de cette campagne n'est encore déclaré réussi. Aucun changement sur l'installation locale ou les données de l'utilisateur.

### Demandes utilisateur (formulation conservée)

1. Pourquoi le module EDT n'a-t-il pas le même aspect chez les élèves et les professeurs ?
2. Après modification puis clic sur « Enregistrer un créneau », la page se décharge/recharge encore.
3. Pourquoi ne peut-on pas modifier la couleur d'une matière ?
4. Les élèves ont accès aux boutons de modification des séances **et** des créneaux ; ils ne doivent avoir aucun droit d'édition.
5. L'espace élève n'a pas de module Paramètres adapté à ses besoins.
6. La messagerie est inaccessible sauf tentative via le widget de la page d'accueil, qui ne fonctionne pas correctement.
7. Le problème des bulletins n'est toujours pas réglé.

### État initial vérifié dans la documentation du dépôt

- `ETAT_V25.txt` indique que la messagerie élève et le Cloud élève ont été volontairement désactivés en attendant un audit dédié (entrée du 12/11/2026).
- `CHANGELOG_V25.txt` mentionne un moteur de calendrier commun aux vues élève et professeur et des protections serveur récentes ; cela ne valide pas la parité visuelle ni l'absence de commandes d'édition dans l'interface élève.
- `AUDIT.txt` conserve des réserves sur la recette multi-comptes, les permissions globales, les bulletins et la messagerie.
- La campagne précédente a fusionné des permissions EDT/enseignants et un filtrage des évaluations publiées ; cela ne constitue pas une recette complète des parcours décrits ici.

### Suivi des sept problèmes

| ID | Problème | État initial | Diagnostic | Correctif | Tests / résultat |
|---|---|---|---|---|---|
| EDT-01 | Parité visuelle élève/professeur | Signalé par utilisateur | À faire | À faire | Non testé |
| EDT-02 | Enregistrement créneau décharge/recharge la page | Signalé par utilisateur | À faire | À faire | Non testé |
| EDT-03 | Couleur matière modifiable | Signalé par utilisateur | À faire | À faire | Non testé |
| SEC-01 | Élève voit les commandes d'édition séances et créneaux | Signalé par utilisateur ; gravité élevée | À faire (UI + serveur) | À faire | Non testé |
| ELEVE-01 | Module Paramètres adapté absent | Signalé par utilisateur | À faire | À faire | Non testé |
| MAIL-01 | Messagerie inaccessible / widget défaillant | Signalé par utilisateur ; accès élève désactivé historiquement | À faire | À faire | Non testé |
| BUL-01 | Parcours bulletins toujours défaillant | Signalé par utilisateur malgré correctifs antérieurs | À faire : reproduire le symptôme exact | À faire | Non testé |

### Journal des interventions

#### 15/11/2026 — Initialisation
- Création de la branche isolée `fix/v25-student-teacher-workflows` depuis `main`.
- Création de ce registre AVANT les modifications fonctionnelles.
- Aucune modification de `main`, aucune fusion et aucun déploiement.
- Prochaine action : localiser précisément les fonctions UI et endpoints serveur des sept sujets, puis écrire des tests de reproduction avant de corriger.
