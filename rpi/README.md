# Raspberry Pi Network UPS Tools (NUT) Device

The Raspberry Pi 4 in the cluster is used as a NUT server, monitoring the UPS
over USB and is responsible for signaling the Talos cluster to shut down safely.
It's built with [rpi-image-gen](https://github.com/raspberrypi/rpi-image-gen),
an officially supported tool to produce a bootable Pi image.

The Pi is intentionally a **minimal, static appliance**. Dealing with power loss is
critical and the best way to control the behavior of the Pi is to keep it as
minimal and static as possible.

It can never pull an update, which is why this isn't bootc or Fedora IoT — those
pay for atomic updates and registry-delivered images, none of which it can
reach. rpi-image-gen also owns the Pi boot partition natively; the Pi 4 has no
UEFI, so anything else means hand-staging Broadcom firmware and U-Boot into an
ESP. To change the box, rebuild and reflash.

### Networking

Static `172.31.42.5/24` on the 2.5G cluster switch, alongside the Talos nodes'
VPC interfaces. What makes shutdown survive an outage isn't isolation, it's that
the path is **same-subnet** — Pi ↔ node traffic crosses only that switch, so the
router at `10.0.0.1` can be dead and `upsmon` → `upsd` still works. The two
things that actually matter: static addressing (no DHCP to depend on) and that
switch being on the UPS. The LAN switch deliberately is not; UPS runtime is a
budget, and only the shutdown path needs to survive.

Management access is therefore a separate, expendable concern. The nodes are
dual-homed and forward, so the Pi carries one route to the LAN via the VIP —
management only, no default route, so it still can't reach the internet.

> ⚠️ **This needs a static route on the router**, which lives outside this repo:
>
> ```
> 172.31.42.0/24 via 10.0.0.201
> ```
>
> Without it nothing on the LAN can reach the Pi. Set it on the router so every
> client benefits, or on one machine to test. Untested against Cilium — if it
> mangles transit traffic across nodes, the fallback is a USB ethernet adapter on
> the LAN, or a spare port on the 2.5G switch with your machine at
> `172.31.42.99/24` (the only option that works with every node down).

SSH is key-only as `core`, from `authorized_keys`. The account has no password,
so an HDMI console can't rescue a bad image — set `device.user1passhash` if you
want that break-glass path.

### Bootstrap

```bash
gh run download -n nut-img
unzstd nut.img.zst
sudo dd if=nut.img of=/dev/rdiskN bs=4m   # macOS (Ctrl-T for progress)
```

### Layout

- `Containerfile`: the builder — rpi-image-gen, its deps, the exporter binary.
- `config.yaml`: device (`rpi4`), base (`trixie-minbase`), and the user/SSH
  variables consumed by rpi-image-gen's `device-user-admin` and `openssh-server`
  layers, which is why there's no hand-rolled user or key setup here.
- `layer/nut.yaml`: packages, plus hooks to install the exporter and enable it.
- `layer/nut.rootfs-overlay/`: files laid into the rootfs verbatim.
