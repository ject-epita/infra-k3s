# Initialisation de Garage sur Synology

Une fois le conteneur démarré avec `docker-compose up -d`, il faut initialiser le layout du cluster (même pour un cluster à noeud unique) et créer les clés pour l'API S3.

## 1. Assigner le layout
Depuis le NAS (ou en exec dans le conteneur) :
```bash
# Identifier le noeud
docker exec garage /garage status

# Assigner le noeud (remplacer l'ID par celui affiché dans la commande status)
docker exec garage /garage layout assign <NODE_ID> --zone dc1 --capacity 1T

# Appliquer le layout
docker exec garage /garage layout apply --version 1
```

## 2. Créer une clé S3
```bash
docker exec garage /garage key create k3s-key
```
Notez le `Access key ID` et la `Secret key` générés.

## 3. Créer les buckets
```bash
docker exec garage /garage bucket create velero-backups
docker exec garage /garage bucket create cnpg-backups
```

## 4. Autoriser la clé sur les buckets
```bash
docker exec garage /garage bucket allow velero-backups --read --write --owner --key k3s-key
docker exec garage /garage bucket allow cnpg-backups --read --write --owner --key k3s-key
```

Vous pouvez maintenant utiliser les identifiants S3 dans la configuration de votre homelab !
