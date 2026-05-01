# Bluesky PDS

[Bluesky PDS](https://github.com/bluesky-social/pds) is a Personal Data Server
for [atproto](https://atproto.com). Self-hosting one means owning the data
behind my atproto identity and being able to use `tale.me` as a handle across
the network (Bluesky, Tangled, etc.) instead of `tale.bsky.social`.

### Setup

- Deployed via the [thompsonbear/bluesky-pds](https://artifacthub.io/packages/helm/bear/bluesky-pds)
  Helm chart — single-replica `Deployment` (PDS uses SQLite + on-disk blobs)
- 25Gi PVC on `cluster-nvmf` for `/pds`
- Reachable at `pds.tale.me` via the shared Envoy gateway, Cloudflare-proxied
- SMTP via Amazon SES (same provider as Authentik) for account verification
- The chart hard-codes its env block, so `PDS_SERVICE_HANDLE_DOMAINS=.tale.me`
  is added through Flux `postRenderers` to allow registering `*.tale.me` handles
- The apex `@tale.me` handle is verified via a `_atproto.tale.me` DNS TXT record

### Bootstrap

1. Generate the secrets and fill in `manifests/pds-secrets.sops.yaml`. The
   chart expects the keys `jwtSecret`, `adminPassword`, `plcRotationKey`,
   `emailSmtpUrl`:

   ```bash
   openssl rand -hex 16                                           # jwtSecret
   openssl rand -hex 16                                           # adminPassword
   openssl ecparam -name secp256k1 -genkey -noout -outform DER \
     | tail -c +8 | head -c 32 | xxd -p -c 32                     # plcRotationKey
   ```

   For SES, format the SMTP URL as
   `smtps://<ses-user>:<ses-pass>@email-smtp.us-east-1.amazonaws.com:465/`.

2. Encrypt and commit:

   ```bash
   sops -e -i k8s/bluesky-pds/manifests/pds-secrets.sops.yaml
   ```

3. Once Flux reconciles, sanity check:

   ```bash
   curl -fsSL https://pds.tale.me/xrpc/_health
   ```

### Claiming `@tale.me`

```bash
ADMIN_PW=$(kubectl -n bluesky-pds get secret pds-secrets \
  -o jsonpath='{.data.adminPassword}' | base64 -d)

kubectl -n bluesky-pds exec deploy/bluesky-pds -- goat pds admin account create \
  --admin-password "$ADMIN_PW" \
  --handle tale.tale.me \
  --email me@tale.me \
  --password '<choose>'
```

Copy the printed `did:plc:…`, add a Cloudflare TXT record
`_atproto.tale.me  TXT  "did=did:plc:XXXX"`, then in the Bluesky app (logged
into the new account against `https://pds.tale.me`) change the handle to
`tale.me`. Finally, request a relay crawl:

```bash
kubectl -n bluesky-pds exec deploy/bluesky-pds -- goat relay request-crawl https://bsky.network
```

### Migrating from `tale.bsky.social`

Don't recreate — follow [account migration](https://atproto.com/guides/account-migration)
with `goat account migrate` to move the existing repo + DID across. Followers
and posts come with you.
