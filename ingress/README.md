# Ingress Configuration
Ingress is done using Traefik for reverse-proxying and cert-manager for TLS.
It uses the local LAN (expecting IP `10.0.0.225`) to expose the Traefik service
as a LoadBalancer service type, which is managed by MetalLB.

### Installation Steps
```sh
# 1. Install cert-manager and MetalLB via Helm
kubectl apply -f manifests/0-metallb-ns.yaml
helm install \
  metallb oci://quay.io/metallb/chart/metallb \
  --version 0.15.2 \
  --namespace metallb-system

helm install \
  cert-manager oci://quay.io/jetstack/charts/cert-manager \
  --version v1.18.2 \
  --namespace cert-manager \
  --create-namespace \
  -f values/cert-manager.yaml

# 2. Apply the metallb & cert-manager manifests
kubectl apply -f manifests/1-metallb-pool.yaml
kubectl apply -f manifests/2-cluster-issuer.yaml

# 3. Install Traefik via Helm
helm install traefik oci://ghcr.io/traefik/helm/traefik \
	--version 37.0.0 \
	-f values/traefik.yaml
```
