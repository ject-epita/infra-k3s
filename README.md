# Infra K3s pour la JECT

## Description
- VM Debian
- Firewall Hetzner qui n'autorise que :
  - HTTP/S (tcp/80, tcp/443, udp/443)
  - SSH (tcp/22)
  - Tailscale (udp/41641)
  - ICMP
- Le firewall bloque tout le reste, notamment 6443 (API K3s)
- On utilise Tailscale pour accéder au cluster
- K3s installé avec config.yaml (voir ci-dessous)
- Pas de base de donnée ETCD (consommation importante de RAM+CPU)

## Déployer le node de zéro
1. Créer un Debian, se ssh
2. apt update et upgrade
3. Installer Tailscale :

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
```
4. Dans Tailscale:
- Disable key expiry
- Mettre les tags corrects
5. Activer IPV6 forwarding
```bash
echo "net.ipv6.conf.all.forwarding = 1" | sudo tee -a /etc/sysctl.d/99-kubernetes.conf
sudo sysctl -p /etc/sysctl.d/99-kubernetes.conf
```
6. Installer la config K3s (`config.yaml`):

```bash
mkdir -p /etc/rancher/k3s/
nano /etc/rancher/k3s/config.yaml
```
7. Installer K3s:

```bash
curl -sfL https://get.k3s.io | sh -
```
8. Installer argo-cd

```bash
# Créer le namespace
kubectl create namespace argocd

# Installer ArgoCD (dernière version stable)
kubectl apply --server-side -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Attendre que tout soit prêt
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
``` 
9. Récupérer le MDP Admin

```bash
# Récupérer le mot de passe (il change à chaque fois)
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```
10. Appliquer la config : 

```bash
# Cela va déployer l'App-of-Apps ArgoCD
# Ca indique à ArgoCD ou trouver le repo, 
# et quels fichiers appliquer, ainsi que les options de synchro
kubectl apply --server-side -f apps/argocd/root.yaml
```

## SealedSecrets

::info:: Adapter la méthode en fonction de la situation
Options :
- Restaurer l'ancienne clef privée utilisée pour chiffrer les secrets
- Utiliser la nouvelle clef créée par SealedSecrets pour rechiffrer tout les secrets du repo