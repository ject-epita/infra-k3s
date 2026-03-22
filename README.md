# titiCloud

Helmfile repo for the Thivillon homelab — single-node k3s on an Intel NUC (13th gen i5), Synology NAS as NFS + Garage, no GitOps, no MetalLB.

## Summary

- [Architecture overview](#architecture-overview)
- [Prerequisites — what must exist before `helmfile apply`](#prerequisites--what-must-exist-before-helmfile-apply)
  - [On the NUC host (Debian)](#on-the-nuc-host-debian)
  - [On the Synology NAS](#on-the-synology-nas)
  - [Cluster-internal resources (created by Helmfile)](#cluster-internal-resources-created-by-helmfile)
- [Non-standard configuration quirks](#non-standard-configuration-quirks)
  - [Precisions about quirks](#precisions-about-quirks)
    - [Pod and Service CIDR](#pod-and-service-cidr)
    - [Proxy hops](#proxy-hops)
- [Deployment](#deployment)
- [Updating dependencies](#updating-dependencies)
- [CI / CD](#ci--cd)
  - [Required GitHub secrets](#required-github-secrets)
  - [Optional GitHub variables](#optional-github-variables)
  - [Tailscale setup](#tailscale-setup)
  - [Target node prerequisites](#target-node-prerequisites)
- [Secret management](#secret-management)
- [Migrating from Docker Compose to k3s](#migrating-from-docker-compose-to-k3s)
  - [Key conceptual differences](#key-conceptual-differences)
  - [Migration approach](#migration-approach)
  - [Copying data into PVCs](#copying-data-into-pvcs)
  - [Useful tools](#useful-tools)
  - [Service-specific notes](#service-specific-notes)

## Architecture overview

```
NUC (k3s)
  ├── Traefik (built-in)  — HTTPS ingress, Let's Encrypt ACME
  ├── Authentik           — SSO / forward auth
  ├── Immich              — photo library
  ├── Affine + N8N        — productivity
  ├── Vaultwarden         — passwords
  ├── Jellyfin            — media server (Intel iGPU hardware transcode)
  ├── Seerr               — media request portal
  ├── Radarr / Sonarr / Prowlarr / qBittorrent — *arr stack (VPN via gluetun)
  └── Velero              — backups to Garage (NAS)

Synology NAS
  ├── NFS /volume1/media  — shared media-data-pvc (1Ti)
  ├── NFS /volume1/cache  — Immich thumbnail cache
  ├── Garage              — velero-backups + cnpg-backups
  └── CloudNativePG clusters write WAL to Garage via Barman
```

## Prerequisites — what must exist before `helmfile apply`

### On the NUC host (Debian)
- k3s installed: 
```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --cluster-init \
  --bind-address=100.68.81.91 \
  --advertise-address=100.68.81.91 \
  --node-ip=100.68.81.91,fd7a:115c:a1e0::8735:515b \
  --node-external-ip=192.168.1.212,2a01:e0a:469:f0a1::74c \
  --tls-san=100.68.81.91 \
  --tls-san=fd7a:115c:a1e0::8735:515b \
  --tls-san=deb13-k3s \
  --tls-san=deb13-k3s.van-saury.ts.net \
  --cluster-cidr=10.42.0.0/16,fd00:42::/56 \
  --service-cidr=10.43.0.0/16,fd00:43::/108 \
  --flannel-iface=eth0 \
  --flannel-ipv6-masq \
  --disable=servicelb" sh -
  ```
- `kubectl`, `helm`, `helmfile` available in PATH
- Intel GPU drivers present: `apt install intel-media-va-driver-non-free vainfo`
- Verify `/dev/dri/renderD128` exists; confirm group IDs match values in `values/jellyfin/values.yaml`
  ```bash
  stat -c "%g %n" /dev/dri/renderD128  # should be 105 (render) on Debian
  stat -c "%g %n" /dev/dri/card0       # should be 44 (video)
  ```

### On the Synology NAS
- NFS share `/volume1/media` exported and accessible from NUC
- NFS share `/volume1/cache` exported and accessible from NUC
- Deploy Garage as a single-node app on your Synology NAS using the provided configuration in the `nas/` directory.
  - Customise the variables in `nas/.env` (from `nas/.env.example`).
  - Deploy with `docker-compose up -d`.
  - Follow the instructions in `nas/README.md` to initialize the cluster and create the required buckets (`velero-backups`, `cnpg-backups`).
  - Garage API will be accessible on the NAS IP at port `3900`.
- Provide the generated S3 credentials (Access Key and Secret Key) in your top-level `.env`.

### Cluster-internal resources (created by Helmfile)
Helmfile creates all namespaces automatically. The CNPG operator must be running before CNPG cluster releases are deployed — the `helmfile.yaml` order enforces this.

## Non-standard configuration quirks

| Config | Default assumed | What to change if different |
|---|---|---|
| Pod CIDR | `10.42.0.0/16` | `FIREWALL_OUTBOUND_SUBNETS` in `values/qbittorrent/values.yaml` |
| Service CIDR | `10.43.0.0/16` | Same as above |
| render group GID | `105` (Debian) | `supplementalGroups` in `values/jellyfin/values.yaml` |
| video group GID | `44` | Same as above |
| Garage port | `3900` | `endpointURL` in all `values/*-db/values.yaml` and `values/velero/values.yaml` |
| NFS media path | `/volume1/media` | `NFS_MEDIA_PATH` in `.env` |
| N8N proxy hops | `1` | `N8N_PROXY_HOPS` in `values/n8n/values.yaml` |

### Precisions about quirks
#### Pod and Service CIDR
Having those setup allows communication with pods and services in the cluster. The gluetun service redirects everything from VPNed services to the VPN by default, so the pod CIDR and service CIDR must be set to not be sent to the VPN server.

#### Proxy hops
If you put Cloudflare as a proxy in front of the k3s cluster, there will be 2 reverse proxies: Cloudflare and Traefik. In this case, you need to set `N8N_PROXY_HOPS` to `2`, and check for other services configuration as well. By not properly setting this, you risk having logs about IPs that are completely wrong (referencing either the Kubernetes Traefik instance, Cloudflare's servers, or forged IPs from malicious clients).

## Deployment

```bash
# 1. Copy and fill in all variables
cp .env.example .env
$EDITOR .env

# 2. Create Garage buckets (see Prerequisites above)

# 3. Deploy everything in order
helmfile --environment homelab apply

# 4. (First run only) Bootstrap Authentik admin user via the browser at https://auth.DOMAIN/if/flow/initial-setup/
```

## Updating dependencies

Helm chart versions and Docker image tags are managed by **Renovate Bot** (`renovate.json`). Renovate opens PRs automatically when new versions are available, covering:
- All `releases/*/` Helmfile release files (chart versions)
- All `values/*/values.yaml` files (Docker image tags)

To enable Renovate, install the [Renovate GitHub App](https://github.com/apps/renovate) on this repository.

For manual updates:
```bash
# Check current image tags
grep -r "tag:" values/

# Update a specific tag, then apply
helmfile --environment homelab apply --selector name=radarr
```

## CI / CD

Two GitHub Actions workflows automate validation and deployment:

| Workflow | Trigger | What it does |
|---|---|---|
| **Validate PR** | Pull request → `master` | YAML lint (`yamllint --strict`) + `helmfile lint` |
| **Deploy** | Push to `master` | Connects via Tailscale, SSHs into the target node, pulls the repo and runs `helmfile apply` |

### Required GitHub secrets

| Secret | Description | How to generate |
|---|---|---|
| `TS_OAUTH_CLIENT_ID` | Tailscale OAuth client ID | Tailscale admin console → Settings → OAuth clients → _Generate_ |
| `TS_OAUTH_SECRET` | Tailscale OAuth client secret | Same as above |
| `SSH_PRIVATE_KEY` | SSH private key (ed25519 recommended) for the deploy user on the target node | `ssh-keygen -t ed25519 -f deploy_key -N ""` — add `deploy_key.pub` to the node's `~/.ssh/authorized_keys`, then store the private key as a secret and delete the local copy |

### Optional GitHub variables

These have sensible defaults and only need to be set if your setup differs.

| Variable | Default | Description |
|---|---|---|
| `DEPLOY_NODE` | `deb13-k3s` | Tailscale hostname (MagicDNS) of the deploy target |
| `DEPLOY_USER` | `deploy` | SSH user on the target node |
| `DEPLOY_PATH` | `~/titicloud` | Path to the cloned repo on the target node |

### Tailscale setup

1. In the [Tailscale admin console](https://login.tailscale.com/admin/settings/oauth), create an **OAuth client** with the tag `tag:ci` (or whichever tag you use in the workflow).
2. Make sure the `tag:ci` tag exists in your [Tailscale ACLs](https://login.tailscale.com/admin/acls) and is allowed to reach the deploy node over SSH (port 22).
3. The target node must already be a member of your tailnet.

### Target node prerequisites

- The repo must be cloned at `DEPLOY_PATH` with the correct remote (HTTPS or SSH).
- A valid `.env` file must exist in that directory (see [Deployment](#deployment)).
- `helm`, `helmfile`, and `kubectl` must be available in the deploy user's `PATH`.

## Secret management

All secrets are injected via `.env` using Helmfile's `requiredEnv`. The `.env` file is gitignored — **never commit it**. For a shared team setup, consider migrating to [External Secrets Operator](https://external-secrets.io/) or [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets).

---

## Migrating from Docker Compose to k3s

This guide is intentionally high-level. Its goal is to give you the mental model and tools to migrate your data safely, not to provide copy-paste commands.

### Key conceptual differences

| Docker Compose | k3s / Kubernetes |
|---|---|
| Volumes are host-path directories | Volumes are PersistentVolumeClaims (PVCs) backed by a StorageClass |
| `ports:` binds directly to host | Services + Ingress route traffic through Traefik |
| `.env` file consumed by Compose | `.env` consumed by Helmfile; secrets become k8s Secrets |
| `depends_on:` | Helmfile ordering + Kubernetes readiness probes |
| Single host, simple networking | Pod-to-pod via `<service>.<namespace>.svc.cluster.local` |

### Migration approach

The safest strategy is **parallel run, then cut over**:

1. **Keep Docker Compose running** until k3s is verified stable.
2. **Stop the Compose service** → copy its data directory to the target PVC → **start the k8s workload**.
3. **Verify** the workload is healthy before proceeding to the next service.
4. **Remove** the Compose service once the k8s version is confirmed working.

### Copying data into PVCs

PVCs backed by `local-config` (SSD) or `nfs-media` (NAS) are directories on the node or NAS. The simplest method is to use a temporary pod that mounts the PVC:

```bash
# Find the actual path of a local-config PVC
kubectl get pv $(kubectl get pvc radarr-config -n media -o jsonpath='{.spec.volumeName}') \
  -o jsonpath='{.spec.local.path}'

# Or use kubectl cp via a temporary pod
kubectl run -n media tmp-shell --rm -it --image=alpine \
  --overrides='{"spec":{"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"radarr-config"}}],"containers":[{"name":"tmp","image":"alpine","command":["sh"],"volumeMounts":[{"name":"data","mountPath":"/data"}]}]}}'
# Then from another terminal:
kubectl cp ./radarr-config-backup/ media/tmp-shell:/data/
```

For NFS-backed PVCs (media library), copy directly on the NAS since both Compose and k3s will access the same NFS share. Point your Compose `volumes:` and your PVC to the same NFS path.

### Useful tools

| Tool | Purpose |
|---|---|
| [`kubectl cp`](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_cp/) | Copy files to/from pods |
| [`k9s`](https://k9scli.io/) | Interactive cluster browser (watch pods, logs, exec) |
| [`stern`](https://github.com/stern/stern) | Multi-pod log tailing |
| [`velero`](https://velero.io/) | Backup/restore PVCs (already deployed in this setup) |
| [`kubectx` / `kubens`](https://github.com/ahmetb/kubectx) | Quick context/namespace switching |

### Service-specific notes

- **Databases (Authentik, Immich, Affine, N8N)**: Export from the Compose Postgres container with `pg_dump`, then import into the CNPG cluster via a psql pod. See [CNPG documentation on import](https://cloudnative-pg.io/documentation/current/database_import/).
- **Vaultwarden**: Copy the `/data` directory (contains `db.sqlite3` and attachments) into the k8s PVC. Stop Compose first to avoid a partial copy.
- **Immich**: Copy the library and thumbnails directories. The ML model cache (`machine-learning/cache`) does **not** need to be copied — it will be re-downloaded automatically.
- **Jellyfin**: Copy config and metadata. The media files stay on the NAS NFS share and are shared between Compose (if still running) and k8s via the same NFS path.
- ***arr stack (Radarr/Sonarr/Prowlarr)**: Copy `/config` directories. Update the download client and indexer URLs to point to internal k8s service names after migration (e.g. `http://qbittorrent.media.svc.cluster.local:8080`).
