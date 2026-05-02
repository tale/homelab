# Observability

Centralized metrics, logging, and alerting stack for the cluster.

### Operators

- **VMOperator** (victoria-metrics-k8s-stack): Manages VMSingle, vmagent, vmalert, VMAlertmanager, node-exporter, kube-state-metrics.
- **Grafana Operator**: Manages Grafana instance, datasources, dashboards, and folders via CRDs.

All scrape targets use **VM-native CRDs** (`VMServiceScrape`, `VMPodScrape`, `VMRule`). The prometheus-operator converter is disabled — no `monitoring.coreos.com` CRDs are installed.

### Components

- **VMSingle**: Long-term metrics storage (180d retention, 150Gi).
- **vmagent**: Lightweight metrics scraper, writes directly to VMSingle.
- **vmalert**: Evaluates alerting and recording rules against VMSingle.
- **VMAlertmanager**: Pushover notifications for critical/warning alerts.
- **VictoriaLogs**: Centralized log storage (90d retention, 50Gi), managed via VLSingle CR.
- **victoria-logs-collector**: Fluent Bit DaemonSet that ships pod logs to VictoriaLogs.
- **Grafana**: Dashboards for metrics and logs, exposed at `grafana.tale.me` with OIDC via Pocket ID. Backed by PostgreSQL (CNPG).

### Data Flow

```
Pods → victoria-logs-collector (DaemonSet) → VictoriaLogs → Grafana
Targets → vmagent → VMSingle → Grafana
VMSingle → vmalert → VMAlertmanager → Pushover
```

### Scrape Targets

All scrape configs are colocated with their respective app/infra directories.

| Target | Type | Location |
|---|---|---|
| node-exporter | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| kube-state-metrics | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| kubelet / cAdvisor | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| kube-apiserver | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| CoreDNS | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| cert-manager | VMServiceScrape | `infra/controllers/cert-manager/` |
| MetalLB | VMServiceScrape | `infra/controllers/metallb/` |
| Grafana Operator | VMServiceScrape | `infra/controllers/grafana-operator/` |
| CNPG Postgres | VMPodScrape | `infra/configs/cloudnative-pg/` |
| CNPG Operator | VMPodScrape | `infra/configs/cloudnative-pg/` |
| Hubble | VMServiceScrape | `infra/configs/cilium/` |
| Cilium Envoy | VMServiceScrape | `infra/configs/cilium/` |
| Envoy Gateway | VMServiceScrape | `infra/configs/envoy/` |
| OpenEBS IO Engine | VMServiceScrape | `infra/configs/openebs/` |
| Blocky DNS | VMServiceScrape | `blocky/manifests/` |
| Forgejo | VMServiceScrape | `forgejo/manifests/` |
| Authentik | VMServiceScrape | `authentik/manifests/` |

### Dashboards (via Grafana Operator CRDs)

Dashboards are colocated with their apps where possible.

| Dashboard | grafana.com ID | Folder | Location |
|---|---|---|---|
| VictoriaMetrics Single | 10229 | VictoriaMetrics | `observability/` |
| vmagent | 12683 | VictoriaMetrics | `observability/` |
| vmalert | 14950 | VictoriaMetrics | `observability/` |
| VictoriaLogs Single | 21599 | Logging | `observability/` |
| Alertmanager | 9578 | Alerting | `observability/` |
| Node Exporter Full | 1860 | Infrastructure | `observability/` |
| cert-manager | 20842 | Infrastructure | `observability/` |
| CloudNativePG | 20417 | Infrastructure | `observability/` |
| Kubernetes Global | 15757 | Kubernetes | `observability/` |
| Kubernetes Pods | 15760 | Kubernetes | `observability/` |
| Blocky DNS | 17996 | Applications | `blocky/` |
| Forgejo | 22363 | Applications | `forgejo/` |
| Authentik | 14837 | Applications | `authentik/` |
| Envoy Gateway | 22539 | Network | `infra/configs/envoy/` |
| Hubble Overview | 16611 | Network | `infra/configs/cilium/` |

### Secrets

| Secret | Namespace | Purpose |
|---|---|---|
| `pushover-credentials` | observability-system | Alertmanager Pushover notifications |
| `grafana-oidc` | observability-system | Grafana OIDC client credentials |
| `grafana-db-credentials` | observability-system | Grafana PostgreSQL password (cross-ns from CNPG) |
| `vmbackup-wasabi-credentials` | observability-system | VMSingle backup S3 credentials |
