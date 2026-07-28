# Raspberry Pi UPS Appliance

Since this cluster's UPS supports USB monitoring, a Raspberry Pi 4 is used to
run a NUT server and signal the Talos cluster to shut down gracefully during a
power loss event. The Pi is a minimal, fully static appliance, built with
[rpi-image-gen](https://github.com/raspberrypi/rpi-image-gen) and only sets up
SSH, NUT, and a small exporter for metrics.

> If you would like to run your own NUT server, you can modify everything inside
> of the `config.yaml` file and build your own image to match your own setup.

## Requirements

- Raspberry Pi 4B (2GB+)
- USB connectivity to a UPS with support for NUT (Network UPS Tools)
- Ethernet connectivity to the same subnet as clients that need signaling

## Configuration

`config.yaml` is the only file you should need to touch. It carries all of the
variables that are needed to correctly configure the appliance. Since the Pi is
fully offline, configuration changes require a build and re-flash of the image.

See [the config](./config.yaml) for a full example, but this is the minimum
required configuration to get a working appliance:

```yaml
device:
  hostname: nut
  user1: core

ssh:
  pubkey_user1: ssh-ed25519 AAAA... you@host

nut:
  ups_name: myups          # what clients address as myups@<host>
  driver: usbhid-ups       # https://networkupstools.org/stable-hcl.html
  vendorid: "0764"
  monitor_password: "..."
  net_address: 10.0.0.5/24 # Leaving this empty will use DHCP
```

## Building

Use the [workflow](../.github/workflows/rpi-image.yaml). It fires on any push
touching `rpi/`, and the image lands as a build artifact:

```bash
gh workflow run "RPi Image"
gh run watch
```

To build locally, you'll need a Linux host with Podman or Docker installed:

```bash
docker build -t rpi-image-gen -f rpi/Containerfile rpi
docker run --rm --privileged -v "$PWD/rpi:/rpi" rpi-image-gen \
  sh -c 'rpi-image-gen build -S /rpi -c /rpi/config.yaml \
    && cp /build/work/deploy-*/*.img.zst /rpi/'
```

## Flashing

Grab the artifact from the most recent successful run and unpack it. The file
inside is named after `image.name` in `config.yaml`:

```bash
gh run download -n nut-img
unzstd nut.img.zst
```

Identify the card carefully — `dd` will happily overwrite the wrong disk.

```bash
# macOS. Note the r in rdisk4, the raw device is an order of magnitude faster.
diskutil list                                # find it, eg /dev/disk4
diskutil unmountDisk /dev/disk4
sudo dd if=nut.img of=/dev/rdisk4 bs=4m
diskutil eject /dev/disk4
```

```bash
# Linux
lsblk                                        # find it, eg /dev/sdb
sudo umount /dev/sdb?*                       # if anything automounted
sudo dd if=nut.img of=/dev/sdb bs=4M conv=fsync status=progress
sync
```

The appliance has no default route unless you gave it one, so reach it from the
same subnet:

```bash
ssh core@10.0.0.5
upsc myups              # UPS variables, confirms the driver bound
curl -s localhost:9199/ups_metrics | head
```

If `upsc` reports `Error: Connection failure`, the driver did not attach. Check
`journalctl -u nut-server` and confirm `nut.vendorid` matches `lsusb`.
