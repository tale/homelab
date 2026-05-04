# Tranquil PDS

[Tranquil PDS](https://tangled.org/tranquil.farm/tranquil-pds) is a Rust
re-implementation of an [atproto](https://atproto.com) Personal Data Server.
This deployment exists to migrate `tale.me` (and any other `*.tale.me`
accounts) off [bluesky-pds](../bluesky-pds/README.md) without losing the DID
or the canonical `pds.tale.me` hostname.

### Setup

- Image: `atcr.io/tranquil.farm/tranquil-pds` (no auth required for pulls)
- Single-replica `Deployment` + `Service`, blobs on a 25Gi `cluster-nvmf` PVC
- Repos go in the shared `central-postgres` CNPG cluster (`tranquil_pds` DB,
  `app` owner — same pattern as forgejo / authentik)
- SMTP via Amazon SES (same provider as bluesky-pds + authentik), configured
  through `[email.smarthost]` in `config.toml` plus
  `MAIL_SMARTHOST_USERNAME` / `MAIL_SMARTHOST_PASSWORD` env vars
- `user_handle_domains = ["tale.me"]` keeps the `*.tale.me` handle behaviour
  we had with bluesky-pds (no per-handle TXT record needed)

### Hostname strategy: always `pds.tale.me`

The end state is that this PDS lives at `https://pds.tale.me`, exactly where
bluesky-pds is today. The trick is that tranquil-pds's `[server].hostname`
config controls **what URL gets baked into each DID's PLC `serviceEndpoint`**,
which is independent of the DNS name(s) you actually expose the pod on.

So:

- `config.toml` pins `hostname = "pds.tale.me"` from day one. Every account
  created or migrated onto this PDS gets its PLC `serviceEndpoint` set to
  `https://pds.tale.me` — even though `pds.tale.me` initially still points
  at bluesky-pds.
- The HTTPRoute starts with the **temporary** hostname `tranquil.tale.me`
  so we can reach the new PDS during the migration without conflicting with
  bluesky-pds's existing claim on `pds.tale.me`.
- At cutover, `tranquil.tale.me` is swapped for `pds.tale.me` in this
  HTTPRoute in the same PR that removes bluesky-pds. After Flux reconciles
  there's no PLC update needed for any migrated account — they were already
  pointing at `pds.tale.me`, the DNS just now resolves to tranquil.

### Bootstrap

1. Generate the secrets and fill in
   `manifests/tranquil-pds-secrets.sops.yaml`:

   ```bash
   openssl rand -base64 48   # JWT_SECRET
   openssl rand -base64 48   # DPOP_SECRET
   openssl rand -base64 48   # MASTER_KEY
   ```

   Grab the CNPG-managed `app` password (same one forgejo/authentik use):

   ```bash
   kubectl -n cnpg-system get secret central-postgres-app \
     -o jsonpath='{.data.password}' | base64 -d
   ```

   Then assemble `DATABASE_URL` as
   `postgresql://app:<password>@central-postgres-rw.cnpg-system.svc.cluster.local:5432/tranquil_pds?sslmode=require`.

   For SES, copy `MAIL_SMARTHOST_USERNAME` / `MAIL_SMARTHOST_PASSWORD` from
   the SES SMTP credentials already used by bluesky-pds.

2. Encrypt and commit:

   ```bash
   sops -e -i k8s/tranquil-pds/manifests/tranquil-pds-secrets.sops.yaml
   ```

3. Once Flux reconciles, sanity check (note the temp hostname):

   ```bash
   curl -fsSL https://tranquil.tale.me/xrpc/_health
   ```

### Account migration (bluesky-pds → tranquil-pds)

Both PDSes are deliberately running at the same time:

- `pds.tale.me` → bluesky-pds (current home of the `tale.me` DID)
- `tranquil.tale.me` → tranquil-pds (target, but advertises `pds.tale.me`
  in PLC ops it signs)

Follow the standard atproto
[account migration](https://atproto.com/guides/account-migration) flow with
`goat account migrate`, pointing the new account at `https://tranquil.tale.me`.
The DID stays the same; PLC just gets updated to point `serviceEndpoint` at
`https://pds.tale.me` (because that's what tranquil-pds reports for itself).

While the swap below has not happened yet, the migrated DID will appear
"broken" to the rest of the network: PLC says `pds.tale.me` but that DNS
record still serves bluesky-pds where the account is now deactivated. Keep
the window short.

### Cutover

In a single PR:

1. Edit [`manifests/tranquil-pds-http-route.yaml`](manifests/tranquil-pds-http-route.yaml)
   so `hostnames` is `[pds.tale.me]` (drop `tranquil.tale.me`, or keep both
   briefly as belt-and-suspenders).
2. Remove `bluesky-pds/flux.yaml` from [`k8s/kustomization.yaml`](../kustomization.yaml).
3. Delete the `k8s/bluesky-pds/` directory.

Once Flux reconciles, `pds.tale.me` resolves to tranquil-pds, every migrated
DID's `serviceEndpoint` matches reality, and the migration is done. No PLC
operations required at this stage.
