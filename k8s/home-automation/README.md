# Home automation

One Flux Kustomization per package, all in the `home-automation` namespace:

| Package | Path | Contents |
| --- | --- | --- |
| `home-automation` | `.` | the namespace and the `bjw-s` HelmRepository |
| `home-assistant` | `home-assistant/` | the hub |
| `eufy-security-ws` | `eufy-security-ws/` | the Eufy locks |
| `scrypted` | `scrypted/` | the Ring camera |
| `samba` | `samba/` | the SMB share |

The shared resources sit at the directory root rather than in a subdirectory.
The root `kustomization.yaml` lists only them, and kustomize includes only what
a kustomization lists — the app subdirectories beneath it are not swept in. That
holds only because the file exists; a Kustomization pointing at a path *without*
one absorbs everything below it recursively.

The four app packages `dependsOn` the `home-automation` Kustomization, which is
named for the namespace rather than the directory.

The namespace carries `kustomize.toolkit.fluxcd.io/prune: disabled`. Deleting a
namespace cascades to everything inside it, and a namespace that moves between
Kustomizations is exactly when an unguarded prune would fire.

Packages are flat — `kustomization.yaml`, `helmrelease.yaml`, and at most one
`secret.sops.yaml`. Directories only appear where files are mounted as a unit,
like Home Assistant's `config/`.

[Home Assistant](https://home-assistant.io) is a nice home automation platform.
I prefer it over something like Homebridge because its a lot more mature,
stable, and useful, while still supporting the HomeKit integrations that we
use in our home.

Three workloads share the `home-automation` namespace, which is deliberately
labelled `pod-security.kubernetes.io/enforce: privileged` — all three need host
networking, and HomeKit is unusable without it. Pairing depends on mDNS, and
mDNS does not survive a hop out of the pod network.

- **home-assistant** — the hub, published at `home.tale.me` through the Envoy
  gateway, and an mDNS HomeKit bridge for everything it knows about.
- **eufy-security-ws** — the Eufy locks, reached over a websocket.
- **scrypted** — the Ring camera, bridged to HomeKit with Secure Video.

### Two paths to HomeKit

The Eufy locks go through Home Assistant, which re-exports them on its own
HomeKit bridge. The Ring camera does not: HomeKit Secure Video needs real
transcoding and a native camera accessory, which Home Assistant's bridge cannot
provide, so Scrypted pairs with Apple Home directly as a second accessory.

Two bridges in the Home app is the cost of that split, and it is the right
trade. Routing the camera through Home Assistant gives up HKSV entirely.

The locks are published in `mode: accessory` on their own ports rather than
through the bridge. A lock command travels to Eufy's cloud and back before the
state confirms, which routinely outlives HomeKit's patience — the unlock
succeeds and the Home app reports a timeout anyway. Home Assistant warns about
exactly this on every start, and accessory mode is its recommended answer: a
slow device on a shared bridge degrades everything behind that bridge.

They stay in `include_entities` rather than an `include_domains: [lock]`
because `eufy_security` marks its locks `entity_category: diagnostic`, and the
HomeKit component skips categorised entities unless they are named explicitly.

### Eufy locks

`eufy-security-client` reaches the newer locks (C33 and relatives) over Eufy's
own MQTT broker rather than the legacy P2P path — that is what "the lock needs
MQTT" refers to. It is internal to the client and faces Eufy's cloud, not us.
There is no broker to run in the cluster, and no `mqtt:` integration in Home
Assistant's config.

This used to require `ghcr.io/tale/eufy-security-ws:mqtt-lock`, a local build of
`eufy-security-ws` against a fork carrying nick-pape's `SecurityMQTTService`
work. Upstream `eufy-security-client` 3.8.0 landed C33 (T85L0) support, and
`eufy-security-ws` 3.1.0 ships client 4.1.0, so the fork and its Dockerfile are
gone.

Home Assistant talks to it through the
[eufy_security](https://github.com/fuatakgun/eufy_security) custom component at
`ws://eufy-security-ws:3000`.

### Custom components

Neither custom component here is in Home Assistant core, and both normally
arrive via HACS — a UI install onto a volume, exactly the kind of state that
gets lost. Instead the init container installs each from a pinned git tag into
`/config/custom_components`, recording the tag in a `.installed_version` marker
beside the component. A start where the marker already matches does no network
I/O at all, so a GitHub outage cannot stop Home Assistant from booting.

| Component | Repository | Version env |
| --- | --- | --- |
| `eufy_security` | `fuatakgun/eufy_security` | `EUFY_SECURITY_TAG` |
| `tuya_local` | `make-all/tuya-local` | `TUYA_LOCAL_TAG` |

`tuya_local` is held at `2026.4.1` deliberately. Every release from `2026.5.0`
onward, master included, ships `except TypeError, ValueError:` in
`helpers/device_config.py` — Python 2 syntax that raises `SyntaxError` on
import, so the integration cannot load at all. `2026.4.1` is the newest tag
that compiles and it still has the cloud/QR setup step. Verify a newer tag
imports before bumping:

```sh
curl -sL https://github.com/make-all/tuya-local/archive/refs/tags/<tag>.tar.gz \
  | tar xz -C /tmp && python3 -m compileall -q /tmp/tuya-local-<tag>/custom_components/tuya_local
```

The tag is passed whole rather than assembled, because the two projects
disagree about the leading `v`. Adding a third is one `install_component` line
plus an env var.

`tuya_local` drives the bulbs directly over the LAN. The alternative, the core
`tuya` integration, round-trips every command through Tuya's cloud and depends
on an IoT Platform trial subscription that needs periodic manual renewal — the
integration dies silently when it lapses.

Setup uses the component's cloud step, which shows a QR code to scan from the
Smart Life app and returns each device's local key. No Tuya IoT developer
project is involved, and the cloud is touched only during that handshake;
control afterwards is local. The keys land in Home Assistant's config entries
under `.storage` rather than in SOPS — they are recoverable by rescanning, and
the volume is backed up either way.

Because devices are addressed by IP, the bulbs need reserved DHCP leases, and
Home Assistant needs a route into whichever VLAN they sit on.

### Configuration

`config/configuration.yaml` is committed and mounted read-only from a generated
ConfigMap. Home Assistant never writes to that file, so nothing fights over it.

The workload is the `bjw-s` `app-template` chart rather than hand-written
manifests. `kustomizeconfig.yaml` teaches kustomize to rewrite the generated
ConfigMap's hashed name into `persistence.config.name` in the HelmRelease
values, so the config stays a normal file in git and an edit to it still rolls
the pod — the property the name hash gives a plain Deployment.

What stays on the PVC is what Home Assistant owns: `.storage/` (entity registry,
config entries, and the HomeKit pairing keys), plus `automations.yaml`,
`scenes.yaml`, and `scripts.yaml` so the UI editors still work. The init
container creates those three empty if missing — a fresh volume has none, and
`!include` on a missing file is a startup failure.

`recorder` points at the `home_assistant` database on the shared CNPG cluster
rather than the default SQLite file, so history rides along with Postgres' own
barman archive and is not part of the volume backup at all. That URL is the only
thing in `ha-db-secret.sops.yaml`.

`trusted_proxies` covers the pod CIDR and the node subnet. The gateway reaches a
host-networked pod, so the observed source address is one or the other depending
on the path.

Scrypted's own configuration — its Ring plugin, its HomeKit plugin, their
credentials — lives entirely in `/server/volume` and is set up through its UI.
That is not declarative and cannot be made so without vendoring plugin state. It
is backed up instead.

### Backups

Three `ReplicationSource`s, staggered nightly, generated with everything else
by the `volsync-backups` ResourceSet in
[`k8s/infra/configs/volsync/`](../infra/configs/volsync/).

| Source | PVC | Schedule | What is in it |
| --- | --- | --- | --- |
| `home-assistant` | `home-assistant-data` | 03:15 | `.storage/`, HomeKit pairings, UI automations |
| `eufy-security-ws` | `eufy-ws-data` | 03:30 | Eufy session tokens and trusted-device state |
| `scrypted` | `scrypted-data` | 03:45 | Scrypted plugins, Ring auth, HKSV pairing |

`copyMethod: Snapshot` is the ResourceSet default, so the movers read a
snapshot rather than the live volume. All three are small, and all three are
database-shaped enough to care about a torn read.

Losing any of these volumes means re-pairing in the Home app, since the HomeKit
accessory keys live in them. That is the whole reason they are backed up.

The Samba share in this same namespace is backed up by the same ResourceSet,
with `copyMethod: Direct`; it is unrelated to home automation beyond sharing a
namespace.

### Restoring

A restore is a `ReplicationDestination` against the same repository — read the
repository layout in the [volsync README](../infra/controllers/volsync/) before
improvising one mid-outage. The order that matters: restore the volume, let the
pod start, then check that the Home app still shows the bridge as paired before
touching anything there. Re-pairing is recoverable; deleting the bridge from the
Home app and losing every automation that references its accessories is not.
