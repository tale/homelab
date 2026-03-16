# Omada Controller

[Omada Controller](https://www.tp-link.com/us/omada-sdn/) is TP-Link's
software-defined networking solution for managing Omada access points,
switches, and gateways from a centralized web interface.

### Setup

- Deployed via the [mbentley/omada-controller-helm](https://github.com/mbentley/docker-omada-controller/tree/master/helm/omada-controller-helm) Helm chart
- Persistent storage for controller data
- LoadBalancer service for device discovery and adoption
