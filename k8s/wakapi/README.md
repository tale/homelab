# Wakapi

[Wakapi](https://wakapi.dev/) is a self-hosted, WakaTime-compatible backend
for tracking coding activity.

### Setup

- Deployed as a raw Kubernetes `Deployment` (no upstream Helm chart)
- PostgreSQL backed by the centralized CloudNativePG cluster
- Native OIDC login via Authentik (`security.oidc[0]` config). Local
  username/password login is left enabled so existing accounts can still sign
  in until they are linked to OIDC

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
