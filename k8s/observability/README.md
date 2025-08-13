# Observability
I manage my observability using [Prometheus](https://prometheus.io/) and
[Grafana](https://grafana.com/) for viewing metrics and logs. Observability is a
key aspect of managing and maintaining a Kubernetes cluster. Thankfully we have
tools like `kube-prometheus-stack` which automatically setup Prometheus to
scrape metrics from all the Kubernetes components in a cluster.

### Setup
- Prometheus runs cluster-wide as an aggregation for all metrics.
- Grafana is deployed and exposed via Gateway for dashboards.
- VictoriaMetrics is used as a long-term storage solution for metrics.
