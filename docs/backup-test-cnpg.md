# Procédure de Test de Restauration GitOps (CloudNativePG & R2)

Ce document décrit la méthode pour tester la restauration d'une base de données CloudNativePG depuis Cloudflare R2.

## Prérequis
Avoir les variables de restauration (`bootstrap.recovery`) prêtes dans le manifest de votre base de données (ex: `vaultwarden-db.yaml`).

---

## Phase 1 : Préparation et Nettoyage

### 1. Désactiver le Self-Heal d'ArgoCD
Modifiez le fichier YAML de votre application ArgoCD (`apps/vaultwarden/vaultwarden.yaml`) :
```diff
  syncPolicy:
    automated:
      prune: true
-     selfHeal: true
+     selfHeal: false
```
*Poussez sur Git pour désactiver la réconciliation auto.*

### 2. Couper l'application & Détruire le cluster
```bash
kubectl scale deployment vaultwarden --replicas=0 -n vaultwarden
kubectl delete cluster vaultwarden-db -n vaultwarden
kubectl delete pvc -n vaultwarden -l cnpg.io/cluster=vaultwarden-db
```

---

## Phase 2 : Bascule en mode Restauration

### 3. Configurer la Restauration dans Git
Dans le manifest du cluster (`vaultwarden-db.yaml`) :
1. **Activer** le bloc `bootstrap.recovery` et `externalClusters`.
2. **Commenter** le bloc `plugins:` (l'archiveur WAL R2) pour éviter les conflits d'écriture.

### 4. Déclencher la récupération
Remettez `selfHeal: true` dans le fichier YAML et effectuez un Sync. ArgoCD va :
- Reconstruire le cluster et rejouer les données distantes.
- Attendez le statut `Cluster in healthy state`.

---

## Phase 3 : Retour en Production

Pour que le cluster continue d'archiver la base de données :
1. **Commenter** `bootstrap.recovery` et `externalClusters`.
2. **Activer** `bootstrap.initdb` (crucial pour fixer le nom d'utilisateur à `vaultwarden`).
3. **Activer** le bloc `plugins:` (WAL archiving).

*Poussez sur Git pour finaliser.*
