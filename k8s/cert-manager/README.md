# cert-manager
[cert-manager](https://cert-manager.io/) is a Kubernetes add-on that makes
it very easy to issue TLS certificates and includes a built-in Ingress and
Gateway API integration. It supports DNS-01 challenges which means you can
issue certificates for domains you own without needing to expose any services
to the public internet. This is great for private clusters or clusters that
are behind a reverse proxy like Traefik.

### Why not use Traefik's built-in cert resolver?
A few things. There's a lot of label plumbing that needs to be done to
configure Traefik to automatically issue certificates for Ingresses and
Gateway API resources. Also, I'm more familiar with cert-manager
and it has a lot of features that I like, such as the ability to issue
certificates for multiple domains and the ability to use different DNS
providers for different domains. It also has a built-in webhook that can
automatically renew certificates before they expire, which is a nice feature
to have.

### Setup
- The `cert-manager` chart is installed in the `cert-manager` namespace.
- SOPS loads my Cloudflare API token for my issuers.
- ClusterIssuer resources that do LetsEncrypt ACME issuance.
