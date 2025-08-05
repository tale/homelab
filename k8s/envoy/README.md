# Envoy Gateway
[Envoy Gateway](https://gateway.envoyproxy.io/) is a cloud-native proxy for
Kubernetes. It is built on top of Envoy proxy and designed to take advantage of
the new Kubernetes [Gateway API](https://gateway-api.sigs.k8s.io/). It's the
future of Kubernetes networking and is a great alternative to Ingress. I use
it because its a lot more flexible than something like Nginx Ingress or Traefik,
and it simplifies the work with TLS and DNS using cert-manager and ExternalDNS.

### Why expose Envoy?
Lots of people who make a Kubernetes cluster tend to use something like
[STRRL/cloudflare-tunnel-ingress-controller](https://github.com/STRRL/cloudflare-tunnel-ingress-controller)
which opens private tunnels to prevent the need for port forwarding. This is
great, but Cloudflare tunnels have arbitrary restrictions on the kind of traffic
they can serve without requiring the client to have Cloudflare WARP installed.
I can kind of get the same safety using proxied Cloudflare DNS records which
allows me to use my IP on A records while keeping it hidden from the public.

### Setup
- MetalLB is used to provide a LoadBalancer IP for the cluster.
- Envoy Gateway is deployed using Helm and configured to use MetalLB.
- `cert-manager` and ExternalDNS are deployed for TLS and DNS management.
- A simple fallback page is available for unconfigured endpoints.
