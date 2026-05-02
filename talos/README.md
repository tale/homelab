# Talos

This cluster is bootstrapped with [Talos Linux](https://talos.dev/), driven
declaratively by [talhelper](https://budimanjojo.github.io/talhelper/). One
`talconfig.yaml` is the single source of truth for cluster identity, node
networking, patches, and the inline Cilium CNI manifest.

## Layout

```
talconfig.yaml          # cluster definition + nodes + global patches
talenv.yaml             # versions: TALOS_VERSION, CILIUM_VERSION, schematic ID
talsecret.sops.yaml     # PKI + bootstrap tokens (sops-encrypted)
patches/
  shared.yaml           # kubelet, network, install, ntp, sysctls
  openebs.yaml          # PSA exemption + hugepages + node label
  tailscale.sops.yaml   # ExtensionServiceConfig (TS_AUTHKEY, routes)
nodes/
  node-1.yaml           # interfaces, addresses, VIP per node
  node-2.yaml
  node-3.yaml
cilium/
  values.yaml           # Helm values for Cilium 1.18
  patch.yaml            # `inlineManifests` header
  manifest.gen.yaml     # generated, gitignored
clusterconfig/          # generated machineconfigs + talosconfig (gitignored)
```

Tasks live under [`.mise/tasks/talos/`](../.mise/tasks/talos/) and are run with
`mise run talos:<task>`.

## Day-to-day

```bash
mise run talos:gen                                       # render Cilium + machineconfigs
mise run talos:render-cilium                             # just the Cilium step

# Talos lifecycle goes through talhelper directly; pipe to bash to execute:
talhelper gencommand apply --node node-1 | bash          # normal apply
talhelper gencommand apply --node node-1 \
  --extra-flags --insecure | bash                        # first-time / maintenance mode
talhelper gencommand bootstrap --node node-1 | bash      # one-shot etcd bootstrap
talhelper gencommand upgrade --node node-2 | bash        # Talos OS upgrade
talhelper gencommand upgrade-k8s --node node-1 | bash    # Kubernetes upgrade
talhelper gencommand reset --node node-3 | bash          # wipe to maintenance mode

rm -rf clusterconfig cilium/manifest.gen.yaml            # clean
```

`talos:gen` always re-renders `cilium/manifest.gen.yaml` first (it depends on
`talos:render-cilium`), so bumping `CILIUM_VERSION` in `talenv.yaml` and
re-running is enough to roll the CNI.

## Versions & secrets

- Talos / Cilium / installer schematic ID live in `talenv.yaml` and are
  interpolated into `talconfig.yaml` via `${VAR}`.
- `talsecret.sops.yaml` is the canonical secret bundle (cluster CA, etcd CA,
  k8s CA, k8s aggregator CA, service-account key, bootstrap tokens). Never
  regenerate against a live cluster. To create a fresh one for a new cluster:
  `talhelper gensecret > talsecret.gen.yaml && sops -e -i talsecret.gen.yaml`.
