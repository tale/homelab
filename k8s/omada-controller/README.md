# Omada Controller

[Omada Controller](https://www.tp-link.com/us/omada-sdn/) is TP-Link's
software-defined networking solution for managing Omada access points,
switches, and gateways from a centralized web interface.

### Setup

- Deployed via the [mbentley/omada-controller-helm](https://github.com/mbentley/docker-omada-controller/tree/master/helm/omada-controller-helm) Helm chart
- Persistent storage for controller data
- LoadBalancer service for device discovery and adoption
- MongoDB runs as a separate `Deployment` rather than the bundled instance, so
  `mongo.external=true` and the controller connects over `eap.mongod.uri`

### Backups

Omada splits its state in two. Site and device configuration live in MongoDB;
the controller's own volume holds the keystore that adopted devices trust.
Losing the keystore means re-adopting every AP, switch, and gateway by hand, so
both are backed up on separate schedules.

MongoDB gets a logical `mongodump` into a small dedicated PVC rather than a
volume snapshot. A crash-consistent copy of a running WiredTiger store usually
replays, but unlike SQLite that is not a guarantee the storage engine makes —
so dump it properly and let VolSync back up the archive. The dump writes to a
`.tmp` name and moves on success; dumping straight onto the final name would let
a failed run replace a good archive with a truncated one, which VolSync would
then faithfully back up.

The controller volume holds ~146M, of which ~140M is re-downloadable device
firmware. restic dedupes it after the first run, so excluding it would cost more
complexity than it saves in space.

Schedules stagger across the 02:00 hour — dump at 02:00, MongoDB sync at 02:30,
controller volume at 02:45 — so a slow `mongodump` never overlaps its own sync.
`copyMethod`, retention, and prune interval come from the shared
`components/volsync-defaults`.

#### Auto Backup

Enable Auto Backup in the UI under `Settings` > `Maintenance` > `Backup`. This
cannot be automated: `omada.properties` only covers ports, the Mongo URI, and
JVM heap, and the Omada Open API (v5.12+) exposes sites, devices, clients, and
SSIDs but has no maintenance or backup endpoints. It is controller state stored
in MongoDB, reachable only through the UI or the undocumented v2 web API.

It writes `.cfg` files to `/opt/tplink/EAPController/data/autobackup`, inside
the volume the `omada-controller-data` `ReplicationSource` already covers, so no
extra plumbing is needed. Worth enabling even alongside the `mongodump`, because
the two restore into different situations: the dump restores into an identical
controller, while the `.cfg` is the only officially supported path into a fresh
one.

Credentials come from the shared `volsync-b2` secret — see
[`k8s/infra/controllers/volsync/`](../infra/controllers/volsync/). `manifests/restic-credentials.yaml`
holds only the repository paths; the endpoint, bucket, keys, and password are
substituted by Flux at apply time.

The two sources use separate repository paths so their prunes never contend for
the same restic lock.

Verify the first runs:

```bash
kubectl -n default create job --from=cronjob/omada-mongodb-dump omada-dump-test

kubectl -n default get replicationsource omada-mongodb omada-controller-data \
  -o custom-columns=NAME:.metadata.name,LAST:.status.lastSyncTime,DUR:.status.lastSyncDuration
```
