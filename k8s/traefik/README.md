# Traefik
[Traefik](https://traefik.io) is a cloud-native reverse proxy. It's basically
just modern Nginx but comes with a few goodies like a web UI. It's been my
go-to reverse proxy for a while and it even supports the upcoming Kubernetes
Gateway API which is more flexible than Ingress.

### Why expose Traefik?
Lots of people who make a Kubernetes cluster tend to use something like
[STRRL/cloudflare-tunnel-ingress-controller](https://github.com/STRRL/cloudflare-tunnel-ingress-controller)
which opens private tunnels to prevent the need for port forwarding. This is
great, but Cloudflare tunnels have arbitrary restrictions on the kind of traffic
they can serve without requiring the client to have Cloudflare WARP installed.
I can kind of get the same safety using proxied Cloudflare DNS records which
allows me to use my IP on A records while keeping it hidden from the public.

### Setup
- Traefik is deployed using Helm but also needs `cert-manager` setup.
- A little `whoami` service is available at [lab.tale.me](https://lab.tale.me).
