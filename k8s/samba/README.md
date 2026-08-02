# Samba

An SMB file share backed by a 500Gi `cluster-nvmf` PVC, exposed on the LAN at
`10.0.0.230` via MetalLB. Runs in the `home-automation` namespace — the
directory name and the namespace deliberately differ.

### Backups

The `smb-store` `ReplicationSource` backs this volume up with restic, keeping 7
daily / 5 weekly / 6 monthly.

This replaced a nightly `s5cmd sync` to `s3://tale-home/smb-backup/`. That job
ran without `--delete`, making it an additive mirror with no history: a file
corrupted in place overwrote the good copy on the next run with no earlier
version to fall back to. restic gives point-in-time recovery instead, at the
cost of being opaque — recovering one file means restoring a snapshot first,
where the mirror could be browsed directly in the bucket. The old objects under
`smb-backup/` are untouched and can be deleted once the restic repository has a
few days of history.

`copyMethod: Direct` is deliberate. The default `Snapshot` clones the PVC at its
*requested* size, and a 500Gi clone lands on all three Mayastor pools, which have
roughly 988Gi free each. `Direct` reads the live volume instead and allocates
nothing. The tradeoff is that a file being written while the mover runs can be
captured torn — acceptable here because this is a document share with no
transactional store, and unacceptable for anything database-shaped.

Because the PVC is `ReadWriteOnce` and already attached to the Samba pod, the
mover schedules onto that same node.

Only ~66Gi of the 500Gi is in use, so neither job is expensive.

#### Bootstrap

The Kustomization will not build without the repository secret:

```bash
cat > k8s/samba/manifests/restic-credentials.sops.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: smb-store-restic
  namespace: home-automation
stringData:
  RESTIC_REPOSITORY: s3:https://s3.wasabisys.com/tale-home/volsync/smb-store
  RESTIC_PASSWORD: $(openssl rand -base64 32)
  AWS_ACCESS_KEY_ID: $(kubectl -n cnpg-system get secret cnpg-wasabi-credentials \
    -o jsonpath='{.data.ACCESS_KEY_ID}' | base64 -d)
  AWS_SECRET_ACCESS_KEY: $(kubectl -n cnpg-system get secret cnpg-wasabi-credentials \
    -o jsonpath='{.data.ACCESS_SECRET_KEY}' | base64 -d)
EOF

sops -e -i k8s/samba/manifests/restic-credentials.sops.yaml
```

The first sync moves ~66Gi and will take considerably longer than the nightly
runs that follow. Verify before trusting it:

```bash
kubectl -n home-automation get replicationsource smb-store \
  -o custom-columns=NAME:.metadata.name,LAST:.status.lastSyncTime,DUR:.status.lastSyncDuration
```
