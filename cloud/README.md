# Cloud Deployment
> Using the cloud for a homelab? *I know, such a cardinal sin*.

In practicality, there are a few services that I need to run which either have
functional reliability requirements or need fast network access. For these
services, I have provisioned a 4 core 24GB RAM ARM server on Oracle Cloud (OCI).

### Deployments
- **Traefik**: Reverse proxy for production and homelab-cloud services
- **Pocket ID & Tinyauth**: OIDC/identity provider and forward-auth service
- **AC Server Manager**: Web UI to manage an Assetto Corsa racing server
- **Wakapi**: Self-hosted WakaTime upstream for tracking coding activity

### Deployment Tools
Since this server also runs bare-metal production workloads for important APIs
that I host, I cannot use Kubernetes to manage the deployments. Therefore, I've
had to compromise and use [Podman](https://podman.io/) to run containers
instead. This allows me to run containers without needing a full Kubernetes
cluster, while still providing a level of isolation and management.

- [**ansible**](https://www.ansible.com/): Configuration management
- [**sops**](https://github.com/getsops/sops): Secrets management
- [**age**](https://github.com/FiloSottile/age): File encryption
- [**just**](https://github.com/casey/just): Task runner
