# Minecraft

Minecraft servers running on the [itzg/minecraft-server](https://github.com/itzg/docker-minecraft-server)
image. Everything lives in a single `minecraft` namespace; each world is a
subdirectory under [`manifests/`](manifests/).

## Worlds

### Vanilla (`vanilla`)

The "Bauhause" survival world, migrated from a Fabric/Paper 1.21.8 server on
`lab-cloud` and upgraded in place to the latest release (`26.1.2`). The world
carries no world-altering mods (only server-side performance/QoL mods on the
old host), so it runs on plain Mojang vanilla.

- `TYPE=VANILLA`, pinned `VERSION` — bump it to upgrade; Mojang's
  DataFixerUpper migrates the save on the next launch
- Image tag is `java25` because 26.1.2 is compiled for Java 25 (the older
  `java21` tag fails with `UnsupportedClassVersionError`)
- Native empty-pause (`PAUSE_WHEN_EMPTY_SECONDS`, 1.21.2+) freezes world ticking
  while nobody is online, instead of the itzg knockd autopause (which needs
  `NET_RAW`, a capability the Pod drops)
- 10Gi PVC on `cluster-nvmf`; whitelist + ops are managed via env vars

## Access

LAN-only via a MetalLB `LoadBalancer`. The `vanilla` Service pulls
`10.0.0.235` from the dedicated `minecraft-pool` (see
[`k8s/infra/configs/metallb/`](../infra/configs/metallb/)) and listens on
`10.0.0.235:25565`. External access is handled by a port-forward on the Omada
router.

## Migrating a world in

The server must not generate a fresh world before the data is in place, so load
the PVC first:

1. Apply the namespace + PVC, then run a throwaway pod that mounts the PVC and
   sleeps.
2. Stream the world in (the source `level.dat` may be `root`-owned, hence
   `chown` afterwards):

   ```bash
   ssh opc@lab-cloud 'sudo tar -C <server>/world -cf - .' \
     | kubectl -n minecraft exec -i <loader-pod> -- tar -C /data/world -xf -
   kubectl -n minecraft exec <loader-pod> -- chown -R 1000:1000 /data
   ```

3. Delete the loader pod and apply the Deployment.

Note: 26.x reorganized the save format — chunks now live under
`world/dimensions/minecraft/<dim>/region/` rather than `world/region/`.

## Observability

The Minecraft servers expose no metrics: vanilla can't load plugins/mods, so
there is no `/metrics` endpoint to scrape without adding an external exporter
sidecar.
