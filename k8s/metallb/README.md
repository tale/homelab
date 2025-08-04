# MetalLB
[MetalLB](https://metallb.io/) is a load-balancer implementation for bare metal
Kubernetes clusters. It allows you to expose services with a LoadBalancer
type, which is not natively supported in bare metal environments. We can
leverage this to expose our Ingress controller (Traefik) to the outside world.
Since I use Cloudflare, I can also keep it proxied, to prevent my IP from being
exposed.

### Constraints
Since I live in an apartment and move around a lot, my homelab lives at my
parents' house. Accordingly, I have a rule that none of my stuff will get in
the way of the single ISP router that they have. This creates a few constraints:

- My parents do not pay for a static IP address, so we need Dynamic DNS.
- I cannot override the router nor break the rest of their LAN network.
- I need to keep things separated, so no router DHCP, no router DNS, etc.

### Setup
To address all of these constraints this is how I set up MetalLB and the LAN:
- The router is configured to hand out DHCP addresses from `10.0.0.2-10.0.0.100`
- The Talos nodes are configured to use `10.0.0.20x` for static LAN IPs
- MetalLB IP assignments are higher (Traefik is given `10.0.0.225`)
- Dynamic DNS is done via Cloudflare with
[timothymiller/cloudflare-ddns](https://github.com/timothymiller/cloudflare-ddns)
- `10.0.0.225` is port-forwarded on the router for Ingress traffic (port 443)
