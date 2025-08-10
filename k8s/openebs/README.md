# OpenEBS
[OpenEBS](https://openebs.io/) is a cloud-native storage solution for
Kubernetes. It provides persistent storage for applications running in a
cluster. Better for my homelab, it allows replicated storage across nodes
which fits in perfectly with my lab since I've put 2TB NVMe SSDs into each one.
OpenEBS' replication system, known as Mayastor, is built in Rust and natively
utilizes NVMF (NVMe over TCP/IP) for high performance.

### Setup
- Patches are made to Talos to support OpenEBS (see `talos/patches/openebs.yaml`)
- Each node operates a "DiskPool" which is replicated by Mayastor
- We define a StorageClass called `cluster-nvmf` for use anywhere
