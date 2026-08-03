# Backup credentials

Every backup in the cluster shares one set of Backblaze B2 credentials, held in
`credentials.sops.yaml` as the `volsync-b2` secret in `flux-system`. Despite the
name it also serves CloudNativePG's barman archive, not only VolSync.

It lives under `infra-controllers` rather than `infra-configs` because
`infra-configs` substitutes *from* it. A secret cannot be a substitution source
for the Kustomization that creates it, and `infra-configs` already depends on
`infra-controllers`, so applying it a layer earlier breaks the cycle.

Both the `apps` ResourceSet and the `infra-configs` Kustomization in
[`k8s/flux.yaml`](../../../flux.yaml) carry a `postBuild.substituteFrom`
pointing at that secret. Flux substitutes the values into the built manifests at
apply time, so a consumer's own credentials file holds nothing sensitive and is
committed as plain YAML:

```yaml
stringData:
  RESTIC_REPOSITORY: s3:https://${B2_ENDPOINT}/${B2_BUCKET}/volsync/smb-store
  RESTIC_PASSWORD: ${RESTIC_PASSWORD}
  AWS_ACCESS_KEY_ID: ${B2_KEY_ID}
  AWS_SECRET_ACCESS_KEY: ${B2_APP_KEY}
```

The repository path is the only value that differs per source. One bucket with a
unique path per PVC is VolSync's documented layout; sharing a single path between
sources would make their `forget`/`prune` runs contend for the same lock.

CloudNativePG uses the same bucket under `cnpg/`, with its own
`cnpg-b2-credentials` secret populated the same way. Its `externalClusters`
recovery source and its `backup` destination both point at `serverName:
central-postgres-r1` — they must name the same server, or a rebuild recovers
from an archive that was never written.

B2 is reached over its S3-compatible endpoint rather than restic's native `b2:`
backend, which restic's own documentation recommends against. That also means the
secret shape is provider-agnostic — moving providers is a change to
`B2_ENDPOINT` and the keys.

Server-side encryption is deliberately off. restic encrypts client-side, so the
bucket only ever receives ciphertext and SSE would encrypt what is already
encrypted.

> One `RESTIC_PASSWORD` now covers every repository. The age key in
> `~/.config/sops/age/keys.txt` is the root of trust for all backups in this
> cluster — a copy belongs somewhere independent of both the cluster and the
> laptop.

### Bucket setup

The bucket needs a lifecycle rule of **keep only the last version**. B2 defaults
to retaining every version, which means restic's `prune` deletes objects while B2
keeps and bills for the prior versions indefinitely. Object Lock must stay off;
it makes `prune` fail.

The application key should be scoped to this bucket alone rather than being an
account master key.

### Adding a backup

1. Add a `ReplicationSource` to the app, and include
   `components: - ../components/volsync-defaults` in its kustomization for the
   shared `copyMethod`, prune interval, and retention.
2. Add a `restic-credentials.yaml` alongside it — copy an existing one and change
   the secret name, namespace, and repository path. No SOPS involved.

### Rotating the B2 key

```bash
sops k8s/infra/configs/volsync/credentials.sops.yaml   # edit B2_KEY_ID / B2_APP_KEY
flux reconcile kustomization infra-configs
```

Then reconcile the app Kustomizations, or wait an hour for the interval. Rotating
`RESTIC_PASSWORD` is a different operation entirely — it does not re-encrypt
existing snapshots, so the old repositories become unreadable. Treat it as
starting fresh repositories, not as a rotation.
