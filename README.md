# Tale Homelab (Talos Mini-cluster)
This repository contains all of the necessary configuration files for my own
homelab mini-cluster built on top of [Talos Linux](https://www.talos.dev/). For
the hardware specifics see the [Hardware](#hardware) section below. With the
actual cluster software, I was aiming to have a very simple setup that is
secure by default, easy to manage, and optionally immutable. Talos Linux
checked all of those boxes and includes tons of extra goodies for homelabbers.

## Deployments
> All deployments are accessible by running `just k <deployment>`, where
> `<deployment>` is the name of the deployment directory (ie. `just k metallb`).
> I use dependency-based Justfiles (similar to Make) to manage the lifecycle of
> Helm installations, Kubernetes YAML, and SOPS secrets.

- General
	- [**MetalLB**](./k8s/metallb/README.md): Load balancer for the cluster
	- [**Envoy Gateway**](./k8s/envoy/README.md): Gateway for the cluster
	- [**cert-manager**](./k8s/cert-manager/README.md): TLS certificate issuer

### Deployment Tools
Because Talos is a Kubernetes distribution, all of the cluster deployments are
written in Kubernetes YAML. To make life easier, I use various different tools
to manage secrets and cluster configuration (installed using
[Mise](https://mise.jdx.dev/)). The tools I use are:
- [**talosctl**](https://www.talos.dev/v1.10/reference/cli/): Talos control
- [**sops**](https://github.com/getsops/sops): Secrets management
- [**age**](https://github.com/FiloSottile/age): File encryption
- [**just**](https://github.com/casey/just): Task runner

### Hardware
My goals for a homelab are to have a small, quiet, and power-efficient cluster
that is still capable of running a variety of workloads. I just created this
cluster, but eventually it'll be all rackmounted and fancy. The hardware I chose
is as follows:

- **3x Dell OptiPlex Micro 7050**
	- Intel Core i7-7700T
	- 32GB DDR4 RAM @ 2400MHz
	- 240GB SATA SSD (for Talos)
	- 2TB NVMe SSD (replicated storage)
	- 1x 1GbE built-in NIC (LAN and WAN access)
	- 1x 2.5GbE M.2 A-Key NIC (intra-cluster communication)
- **1x UGREEN 2.5GbE Switch**
	- 5x 2.5GbE RJ45 ports
	- 1x 10GbE SFP+ port
- **Planned but not yet purchased:**
	- 1x Generic UPS with `usbhid-ups` support
	- 1x Raspberry Pi 4B
		- Runs a NUT server to monitor the UPS and signal the cluster
		- Runs a tunnelable Tailscale node for LAN recovery access
		- Possibly PiKVM for remote KVM access (if needed)
