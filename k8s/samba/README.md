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

Only ~66Gi of the 500Gi is in use, so the job is not expensive.

Credentials come from the shared `volsync-b2` secret — see
[`k8s/infra/configs/volsync/`](../infra/configs/volsync/).

The first sync moves ~66Gi and will take considerably longer than the nightly
runs that follow. Verify before trusting it:

```bash
kubectl -n home-automation get replicationsource smb-store \
  -o custom-columns=NAME:.metadata.name,LAST:.status.lastSyncTime,DUR:.status.lastSyncDuration
```
