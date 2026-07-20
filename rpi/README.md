# Raspberry Pi Hosts (Debian, rpi-image-gen)

Bare-metal Raspberry Pi hosts built with
[rpi-image-gen](https://github.com/raspberrypi/rpi-image-gen), Raspberry Pi's own
image builder: a declarative `config.yaml` picks the device and base system, a
layer adds packages and a rootfs overlay, and the tool emits a `.img` you flash.
It wants a Debian host, so on macOS `rpi/Containerfile` is that host.

> **These are frozen appliances, deliberately.** The Pi is air-gapped (see
> below), so it can never pull an update — which is exactly why it isn't built
> on bootc or Fedora IoT. Those pay for atomic updates, A/B rollback and
> registry-delivered images, and none of that is reachable from an isolated L2
> segment. A tool that bakes a fixed image and stops is honest about what this
> box actually is. To change it, rebuild and reflash.

The other reason: rpi-image-gen owns the Pi boot partition natively. Generic
image builders don't, and on a Pi 4 — which has no UEFI, so its ROM reads the
FAT partition directly — that means hand-staging Broadcom firmware and U-Boot
into an ESP after the fact. Here it's the vendor's problem.

### Hosts

- **nut** (`nut/`): [Network UPS Tools](https://networkupstools.org/) server on
  a Raspberry Pi 4, monitoring a **CyberPower CP550SLG** over USB (`usbhid-ups`,
  pinned to CyberPower vendor id `0764`). `upsd` and `upsmon` are Debian
  packages run by systemd — no containers, nothing to pull at runtime. A
  `nut_exporter` binary baked into the image serves Prometheus metrics on
  `:9199`.

### Networking

The Pi shares the isolated 2.5G cluster switch with the Talos nodes and takes a
static **`172.31.42.5/24`** on it — same as a node's VPC interface: no DHCP, no
gateway, no DNS. That segment is a dumb L2 island with no route off it, so the
box is **air-gapped**: it never reaches a registry. The point is that UPS
shutdown coordination (the nodes' `upsmon` → this Pi's `upsd`, over
`172.31.42.5`) keeps working with the router dead and the internet gone —
same-subnet traffic only touches the switch.

Everything the Pi runs is baked in, so the air gap costs nothing: no images to
pre-load, no update daemon to starve.

### Bootstrap

**Build in CI, not on the Mac.** The `rpi image` workflow builds on a native
arm64 runner; grab `nut-img` from the run's artefacts:

```bash
gh run download -n nut-img
unxz nut.img.xz
sudo dd if=nut.img of=/dev/rdiskN bs=4m   # macOS (Ctrl-T for progress)
```

Then boot the Pi 4 — no keyboard, no firmware menus, no first-boot setup.

> **Do not run `mise run rpi:image` on macOS.** rpi-image-gen needs a privileged
> container doing mount-namespace and loop-device work, and under a macOS
> hypervisor that reliably takes the whole host down (confirmed on macOS 27, and
> no change to the image definition avoids it). The task is kept for running on
> a real Linux box, where the same build is unremarkable.

There the build tree also has to stay on the container's own filesystem: a
macOS bind mount is case-insensitive, and Debian ships colliding pairs like
`PAM.7.gz` / `pam.7.gz`, which makes dpkg fail partway through the chroot.

The `core` user gets passwordless sudo and key-only SSH; its authorized keys are
the committed `nut/authorized_keys`, wired in via `ssh.pubkey_user1`.

### On the NUT password

There isn't a secret here, deliberately. NUT's protocol makes `upsmon` LOGIN
with a password — only anonymous `LIST VAR` (what the exporter uses) is
credential-free — so the field can't be empty, but on an air-gapped L2 island
whose only peers are our own nodes it protects nothing: a secondary can watch
and nothing else. It's a committed constant (`cluster-local`) on both ends,
`nut/layer/nut.rootfs-overlay/etc/nut/upsd.users` here and
`talos/patches/nut-client.yaml` on the nodes. That's why the build needs no sops.

### Metrics

`nut_exporter` serves UPS metrics at
`http://172.31.42.5:9199/ups_metrics?ups=cyberpower` (it reads `upsd` on
`127.0.0.1:3493`, anonymous LIST VAR — no creds needed). The Pi isn't in the
cluster, but it's on the nodes' `172.31.42.0/24` switch, so wire it into the
existing VictoriaMetrics/Grafana stack (`k8s/observability/`) as a static scrape
target when ready:

```yaml
# a VMStaticScrape (or vmagent static_config) pointing at the Pi's cluster IP
- targets: ["172.31.42.5:9199"]
  labels: { job: "nut" }
  # metrics_path: /ups_metrics, params: { ups: [cyberpower] }
```

Grafana dashboard [10914](https://grafana.com/grafana/dashboards/10914) covers
`nut_exporter`. Not wired yet — this is the eventual integration.

### Layout

- `Containerfile`: the builder — rpi-image-gen, its deps, and the exporter
  binary. Setup only; no build logic.
- `nut/config.yaml`: which device (`pi4`), which base (`trixie-minbase`), which
  layer, and the user/SSH variables the library layers consume.
- `nut/layer/nut.yaml`: packages and the two hooks that install the exporter and
  enable the units.
- `nut/layer/nut.rootfs-overlay/`: files laid into the rootfs verbatim (NUT
  config, static network, udev rule, exporter unit).
- `nut/authorized_keys`: who may log in as `core`.

User creation, sudo, and SSH key installation come from rpi-image-gen's own
`device-user-admin` and `openssh-server` layers rather than anything hand-rolled
here — that's why `config.yaml` sets `device.user1*` and `ssh.*` variables.
