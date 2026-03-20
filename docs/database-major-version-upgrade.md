# CloudNativePG Major Upgrade Guide

This document describes the steps to perform a major PostgreSQL version upgrade (e.g., from v16 to v17) using CloudNativePG declaratively. 

## 1. When does this happen?
Renovate or Dependabot will automatically open a Pull Request when a new major version of the Postgres image is available (e.g., `ghcr.io/cloudnative-pg/postgresql:17.x`).
**Do not just merge the PR directly without updating the cluster name!** Bumping the major version without renaming the cluster will break the database, as the data directories are incompatible between major PostgreSQL releases.

## 2. Upgrade Steps (Declarative Method)

To upgrade the database to a new major version, we must perform a side-by-side clone of the data using CNPG's `recovery` feature.

### Step 2.1: Keep the old cluster name, but create a new helm configuration
Instead of editing the old configuration in place, you should rename the cluster to reflect the new major version. For example, change `authentik-db-16` to `authentik-db-17`.

```yaml
cluster:
  name: authentik-db-17                  # 1. Update cluster name
  instances: 1
  imageName: ghcr.io/cloudnative-pg/postgresql:17.0 # 2. Update image version

  # 3. Add the bootstrap recovery block!
  bootstrap:
    recovery:
      source: authentik-db-16           # The name of your PREVIOUS cluster
```

### Step 2.2: Apply the changes
When Helmfile applies this, CloudNativePG will automatically take a snapshot of the old cluster (`authentik-db-16`) and clone it into the new cluster (`authentik-db-17`). Thanks to Kubernetes and hard links, this process is usually entirely instantaneous and doesn't double your storage usage initially.

### Step 2.3: Update your Applications (.env)
Since the cluster name changed, the read-write service name also changes!
- Update your `.env` to point `AUTHENTIK_DB_HOST` from `authentik-db-16-rw.xxx` to `authentik-db-17-rw.xxx`.
- Restart your application pods so they connect to the new v17 database.

### Step 2.4: Verification
Log into your application and ensure all data is present and working correctly.
You can also check the CNPG cluster status:
```bash
kubectl get cluster -n <namespace>
```

### Step 2.5: Cleanup
Once you have confirmed the new `authentik-db-17` cluster works perfectly, you can safely remove the old `authentik-db-16` cluster.
- Remove the `bootstrap: recovery` block from your values.yaml (so it doesn't try to clone again if you recreate it later, though CNPG ignores it after init).
- Use `kubectl delete cluster authentik-db-16 -n <namespace>`.

## Common Pitfalls
- **Forgetting to update `.env` passwords or hosts**: The application will fail to connect if it's still looking for the `-16-rw` service.
- **Forgetting `bootstrap: recovery`**: This will spawn a completely **empty** database! Make sure to provide the `source`.
- **Custom images (like Immich)**: Make sure the new image you are referencing is the tensorchord version (`cloudnative-vectorchord`) and not the generic CNPG image if the application requires vector extensions. Let Renovate suggest the tag for `cloudnative-vectorchord`.

## Useful Links
- [CloudNativePG Major Upgrades Documentation](https://cloudnative-pg.io/documentation/current/pg_upgrade/)
- [CloudNativePG Recovery/Bootstrap](https://cloudnative-pg.io/documentation/current/bootstrap/#bootstrap-from-a-snapshot)
