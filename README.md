# titiCloud
Ce repo contient les ressources Helmfile pour déployer titiCloud, le homelab des Thivillons.

## Prérequis

- k3s installé sur le NUC
- NAS Synology avec NFS et MinIO activés
- Helmfile installé (`brew install helmfile` ou équivalent)
- `.env` créé depuis `.env.example` avec toutes les variables remplies

## Déploiement

```bash
# Copier et remplir les variables
cp .env.example .env
# Editer .env avec vos valeurs

# Déployer tout
helmfile --environment homelab apply
```

## Mise à jour des dépendances

### Helm charts
Dependabot est configuré (`.github/dependabot.yml`) pour ouvrir automatiquement des PRs
quand de nouvelles versions de charts Helm sont disponibles.

> **Note** : Dependabot pour Helm ne peut analyser que les fichiers `helmfile.yaml` racines.
> Les fichiers de release dans `releases/` ne sont pas scannés automatiquement.
> Pour une couverture complète (charts + images Docker), il est recommandé d'utiliser
> [Renovate Bot](https://docs.renovatebot.com/modules/manager/helmfile/) qui supporte
> nativement les fichiers Helmfile et les images Docker dans les valeurs Helm.

### Tags d'images Docker
Les tags Docker dans les fichiers `values/*/values.yaml` ne sont pas mis à jour
automatiquement par Dependabot.

Pour mettre à jour les tags manuellement :
1. Recherche le tag actuel : `grep -r "tag:" values/`
2. Vérifie la dernière version sur Docker Hub / GitHub Container Registry pour chaque image.
3. Mets à jour le `tag:` dans le fichier `values/<service>/values.yaml` correspondant.
4. Ouvre une PR pour review avant de déployer.

> Pour automatiser ce processus, ajoute un fichier `renovate.json` à la racine du repo
> pour activer [Renovate Bot](https://docs.renovatebot.com/modules/manager/helm-values/)
> qui supporte nativement les images Docker dans les fichiers Helm values.
