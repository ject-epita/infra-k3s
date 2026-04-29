# Procédure de Test de Restauration GitOps (CloudNativePG & R2)

Ce document décrit la méthode pour tester la restauration d'une base de données gérée par CloudNativePG depuis les sauvegardes distantes (ex: Cloudflare R2).

## Prérequis
La configuration de restauration (`bootstrap.recovery`) doit être à jour et **validée / poussée** dans votre dépôt Git central.

## Étapes de Restauration

### 1. Désactiver le Self-Heal d'ArgoCD
Modifiez les paramètres de synchronisation de l'application ArgoCD concernée afin de suspendre la réconciliation immédiate :

```diff
  syncPolicy:
    automated:
      prune: true
-     selfHeal: true
+     selfHeal: false
```

*Commitez et poussez cette modification dans votre dépôt Git.*

### 2. Isoler la charge applicative
Fermez les sessions et les accès en cours sur la base de données :
```bash
kubectl scale deployment <app-name> --replicas=0 -n <namespace>
```

### 3. Purger l'état local
Supprimez le cluster existant ainsi que ses disques persistants pour forcer la reconstruction complète :
```bash
kubectl delete cluster <cluster-name> -n <namespace>
kubectl delete pvc -n <namespace> -l cnpg.io/cluster=<cluster-name>
```

### 4. Déclencher la restauration
Poussez la configuration intégrant `bootstrap.recovery` sur Git, puis rétablissez le paramètre `selfHeal: true` sur l'application.

ArgoCD détectera la divergence et déclenchera de lui-même :
- La création du nouveau cluster PostgreSQL configuré pour récupérer le dump.
- La création et la montée en charge (scaling) automatique de vos pods applicatifs une fois l'infrastructure disponible.

## Suivi
La progression globale ainsi que l'état de santé des ressources peuvent être suivis directement depuis la **WebUI ArgoCD**.
