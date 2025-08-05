# Talos
This cluster is bootstrapped using [Talos](https://talos.dev/), an immutable OS
designed to run Kubernetes in a secure and easy way. In order to automate as
much of the process as possible, `talosctl` allows us to generate the machine
configurations given some well known snippets. We can then apply those by
running a comand like `talos apply-config --nodes <ip> --file config.gen.yaml`.

### Setup
The `secrets.sops.yaml` includes all PKI and token secrets used by the cluster.
The `patches/` contains the configuration snippets for our machines, including
a Tailscale extension configuration for Talos and node-specific config such as
interfaces and IP addresses. When generating a configuration, the Cilium Helm
template is also rendered and brought in-tree as part of the Talos bootup.

### Generating the configuration
To generate and apply a configuration, you can use the following commands:
```bash
just t gen-node-config <node-id> # node-1, node-2, node-3
talos apply-config --nodes <ip> --file config.gen.yaml

# Optionally if making reboot required changes
talos upgrade-k8s --nodes <ip>
```
