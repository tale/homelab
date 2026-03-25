# Observability

Centralized metrics, logging, and alerting stack for the cluster.

### Operators

- **VMOperator** (victoria-metrics-k8s-stack): Manages VMSingle, vmagent, vmalert, Alertmanager, node-exporter, kube-state-metrics.
- **Grafana Operator**: Manages Grafana instance, datasources, dashboards, and folders via CRDs.

### Components

- **VMSingle**: Long-term metrics storage (180d retention, 150Gi).
- **vmagent**: Lightweight metrics scraper, writes directly to VMSingle.
- **vmalert**: Evaluates alerting and recording rules against VMSingle.
- **Alertmanager**: Pushover notifications for critical/warning alerts.
- **VictoriaLogs**: Centralized log storage (90d retention, 50Gi), managed via VLogs CR.
- **victoria-logs-collector**: Fluent Bit DaemonSet that ships pod logs to VictoriaLogs.
- **Grafana**: Dashboards for metrics and logs, exposed at `grafana.tale.me` with OIDC via Pocket ID. Backed by PostgreSQL (CNPG).

### Data Flow

```
Pods → victoria-logs-collector (DaemonSet) → VictoriaLogs → Grafana
Targets → vmagent → VMSingle → Grafana
VMSingle → vmalert → Alertmanager → Pushover
```

### Dashboards (via Grafana Operator CRDs)

| Dashboard | grafana.com ID | Folder |
|---|---|---|
| VictoriaMetrics Single | 10229 | VictoriaMetrics |
| vmagent | 12683 | VictoriaMetrics |
| vmalert | 14950 | VictoriaMetrics |
| VictoriaLogs Single | 21599 | VictoriaMetrics |
| Node Exporter Full | 1860 | Infrastructure |
| cert-manager | 20842 | Infrastructure |
| Kubernetes Global | 15757 | Kubernetes |
| Kubernetes Pods | 15760 | Kubernetes |
| Blocky DNS | 18166 | Applications |
| Alertmanager | 9578 | VictoriaMetrics |
