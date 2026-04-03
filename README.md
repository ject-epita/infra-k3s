# Titicloud Kubernetes Infrastructure

## Servarr Authentication Quirk
When using ForwardAuth (Authentik) with Prowlarr, Sonarr, or Radarr, environment variables (e.g., `PROWLARR__AUTH__METHOD`) may be ignored if a `config.xml` file already exists. 

To ensure ForwardAuth works correctly, an **init container** is used to patch the `config.xml` file at startup:
- Sets `AuthenticationMethod` to `External`.
- Sets `AuthenticationRequired` to `DisabledForLocalAddresses`.

**IMPORTANT NOTE FOR FRESH INSTALLS**: 
The `initContainer` runs *before* the application starts. On the very first run, `config.xml` does not exist yet, so the patch cannot be applied. The application will start and create a default `config.xml` with Basic Auth. 
**You MUST restart the pod once (`kubectl rollout restart deployment <app> -n media`) after the initial deployment** so the `initContainer` can run again and successfully patch the now-existing config file.

Refer to `values/media/*.yaml.gotmpl` for implementation details.

## Renovate — Convention de versioning pour les images linuxserver

### Problème
Les images `lscr.io/linuxserver/*` ont leurs tags sur Docker Hub/GHCR,
mais leurs changelogs sont sur GitHub (`github.com/linuxserver/docker-*`).
`datasource=github-releases` trouve les changelogs mais rate les vrais tags.
`datasource=docker` trouve les bons tags mais n'a pas de changelogs.

### Solution
On utilise `datasource=docker` + `changelogUrl` inline pour combiner les deux.

### Pattern à utiliser
```yaml
# renovate: datasource=docker depName=lscr.io/linuxserver/<app> changelogUrl=https://github.com/linuxserver/docker-<app>
repository: lscr.io/linuxserver/<app>
tag: "<version>"
```

### Exemples
```yaml
# Radarr
# renovate: datasource=docker depName=lscr.io/linuxserver/radarr changelogUrl=https://github.com/linuxserver/docker-radarr
repository: lscr.io/linuxserver/radarr
tag: "5.20.2"

# Sonarr
# renovate: datasource=docker depName=lscr.io/linuxserver/sonarr changelogUrl=https://github.com/linuxserver/docker-sonarr
repository: lscr.io/linuxserver/sonarr
tag: "4.0.14"

# Prowlarr
# renovate: datasource=docker depName=lscr.io/linuxserver/prowlarr changelogUrl=https://github.com/linuxserver/docker-prowlarr
repository: lscr.io/linuxserver/prowlarr
tag: "2.3.0"

# qBittorrent
# renovate: datasource=docker depName=lscr.io/linuxserver/qbittorrent changelogUrl=https://github.com/linuxserver/docker-qbittorrent
repository: lscr.io/linuxserver/qbittorrent
tag: "5.0.4"
```

### Notes
- `changelogUrl` est capturé par le customManager regex dans `renovate.json`
- Ne pas utiliser `datasource=github-releases` pour les images linuxserver :
  les tags GitHub upstream (ex: `6.1.2.9463`) ne correspondent pas aux tags
  Docker linuxserver (ex: `5.20.2`), ce qui bloque les PRs Renovate.