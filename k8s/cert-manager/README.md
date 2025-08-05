# cert-manager
[cert-manager](https://cert-manager.io/) is a Kubernetes add-on that makes
it very easy to issue TLS certificates and includes a built-in Gateway API
integration. It supports DNS-01 challenges which means you can issue
certificates for domains you own without needing to expose any services to the
public internet. This is great for private clusters or clusters that
are behind a reverse proxy like Envoy Gateway.

### Setup
- The `cert-manager` chart is installed in the `cert-manager` namespace.
- SOPS loads my Cloudflare API token for my issuers.
- ClusterIssuer resources that do LetsEncrypt ACME issuance.
