#!/usr/bin/env bash
set -e

# Load config from .env if it exists to get MASTER_IP, SSH_USER, etc.
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Configuration with defaults
MASTER_IP=${KUBE_MASTER_IP:?"KUBE_MASTER_IP is not set"}
SSH_USER=${SSH_USER:?"SSH_USER is not set"}
REMOTE_PATH=${REMOTE_KUBECONFIG_PATH:?"REMOTE_KUBECONFIG_PATH is not set"}

echo "Fetching kubeconfig from $SSH_USER@$MASTER_IP:$REMOTE_PATH..."

# Fetch the file securely into the local repo
scp "$SSH_USER@$MASTER_IP:$REMOTE_PATH" kubeconfig

# Fix the IP in the kubeconfig if it's set to localhost/127.0.0.1 (common in k3s/kubeadm)
sed -i "s/127.0.0.1/$MASTER_IP/g" kubeconfig
sed -i "s/localhost/$MASTER_IP/g" kubeconfig

# Ensure the local config has correct tight permissions (required by kubectl)
chmod 600 kubeconfig

if command -v direnv >/dev/null 2>&1; then
    direnv reload
fi

echo "Done! Kubeconfig saved to ./kubeconfig"
