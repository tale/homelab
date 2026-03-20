# Observability

Centralized metrics and logging stack for the cluster.

### Components

- **Prometheus** (kube-prometheus-stack): Cluster-wide metrics scraping with 24h local retention.
- **VictoriaMetrics**: Long-term metrics storage (180d retention, 200Gi).
- **VictoriaLogs**: Centralized log storage (90d retention, 50Gi).
- **victoria-logs-collector**: Fluent Bit-based log collector (DaemonSet) that ships pod logs to VictoriaLogs.
- **Grafana**: Dashboards for metrics and logs, exposed at `grafana.tale.me` with OIDC.

### Data Flow

```
Pods → victoria-logs-collector (DaemonSet) → VictoriaLogs → Grafana
Prometheus → remote write → VictoriaMetrics → Grafana
```
