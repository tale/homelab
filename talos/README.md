# Talos Cluster

The workhorse of my homelab is a 3-node Talos cluster running on bare-metal. See
[the main README](../README.md#hardware) for hardware specs. Each node runs as a
Kubernetes control-plane and worker, allowing for maximum availability.

To make managing the [Talos](https://talos.dev) config easier, I use
[talhelper](https://budimanjojo.github.io/talhelper/) to generate the configs
and manage other concerns like SOPS and extensions. See `talconfig.yaml` for the
cluster definition and `talenv.yaml` for fixed variables.

## Day-to-day

```bash
mise run talos:gen     # render Cilium + machineconfigs
mise run talos:clean   # drop everything generated

# Talos lifecycle goes through talhelper; `--node` takes a hostname or IP from
# talconfig.yaml and defaults to every node. Pipe to bash to execute:
talhelper gencommand apply --node talos-pk9-lp1 | bash
talhelper gencommand apply --node talos-pk9-lp1 \
  --extra-flags --insecure | bash                            # maintenance mode
talhelper gencommand bootstrap --node talos-pk9-lp1 | bash   # one-shot etcd bootstrap
talhelper gencommand upgrade --node talos-z4f-vra | bash     # Talos OS upgrade
talhelper gencommand upgrade-k8s --node talos-pk9-lp1 | bash # Kubernetes upgrade
talhelper gencommand reset --node talos-74p-1fd | bash       # wipe to maintenance mode
```

Rolling the CNI takes more than a `CILIUM_VERSION` bump: Talos only ever
_creates_ missing resources from `inlineManifests` — it never updates or deletes
them. The config has to go out to every control-plane node (they must all be
identical) followed by `upgrade-k8s`, which is what actually re-applies the
manifests.
