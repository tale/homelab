# Cilium

[Cilium](https://cilium.io) replaces both Flannel and `kube-proxy`. Talos boots
without a CNI, so the chart is rendered into the machine config as an inline
manifest since it needs to be available before `kube-apiserver` starts.

### Files

- `values.yaml`: Chart values
- `patch.yaml`: The actual Talos patch the Helm chart is rendered into
