# Cilium
[Cilium](https://cilium.io) is a cloud-native CNI for Kubernetes built on eBPF.
Honestly, it's just my preferred choice of CNI for Kubernetes clusters because
it is capable of replacing `kube-proxy` and has Hubble, an observability tool
that provides insights into the network traffic in the cluster and can visualize
routes through the Hubble UI.

### Setup
Cilium is actually setup through Talos by rendering the Helm chart and applying
it into the `patch.yaml` file. This patch adds the Cilium definitions as inline
manifests for Talos to apply at boot time. The `talos/` directory contains the
script that invokes the Helm chart rendering and then includes the generated
patch file into the machine configuration.

Once setup, we also have our Hubble UI which is forwarded using the Envoy proxy
and is protected being OIDC authentication through a gateway SecurityPolicy.
