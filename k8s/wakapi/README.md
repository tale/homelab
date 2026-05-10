# Wakapi

[Wakapi](https://wakapi.dev/) is a self-hosted, WakaTime-compatible backend
for tracking coding activity. Migrated from the Oracle cloud podman deployment
(see `cloud/wakapi/`) to the homelab cluster.

### Setup

- Deployed as a raw Kubernetes `Deployment` (no upstream Helm chart)
- PostgreSQL backed by the centralized CloudNativePG cluster
- Native OIDC login via Authentik (`security.oidc[0]` config). Local
  username/password login is left enabled so existing migrated accounts can
  still sign in until they are linked to OIDC

### Authentik setup

Create an OAuth2/OIDC provider and Application in Authentik:

- Application slug: `wakapi`
- Redirect URI: `https://wakatime.tale.me/oidc/authentik/callback`
- Scopes: `openid`, `profile`, `email`

Then update [`manifests/wakapi-oidc.sops.yaml`](manifests/wakapi-oidc.sops.yaml)
with the issued `client-id` and `client-secret`:

```sh
sops k8s/wakapi/manifests/wakapi-oidc.sops.yaml
```

### Migrating data from the Oracle SQLite instance

The legacy `wakapi` SQLite DB (`/var/lib/wakapi/wakatime.db` on `oracle`) can be
imported into the new Postgres database using wakapi's built-in
[`dbmigrate.go`](https://github.com/muety/wakapi/blob/master/scripts/dbmigrate.go)
script. Roughly:

1. `kubectl port-forward -n cnpg-system svc/central-postgres-rw 5432:5432`
2. `scp opc@lab-cloud.heron-mahi.ts.net:/var/lib/wakapi/wakatime.db /tmp/`
3. Clone wakapi at the matching version and run
   `go run scripts/dbmigrate.go -config migrate.yml` with `source` set to the
   SQLite file and `target` to the local-forwarded Postgres `wakapi` database.
