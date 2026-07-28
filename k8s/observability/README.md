# Observability

Centralized metrics, logging, and alerting stack for the cluster.

### Operators

- **VMOperator** (victoria-metrics-k8s-stack): Manages VMSingle, vmagent, vmalert, VMAlertmanager, node-exporter, kube-state-metrics.
- **Grafana Operator**: Manages Grafana instance, datasources, dashboards, and folders via CRDs.

Scrape config comes from two places, deliberately:

- **Chart-rendered `ServiceMonitor`/`PodMonitor`**, converted to their VM
  equivalents by the operator's prometheus converter. Preferred wherever the
  chart supports it, so a chart upgrade carries its own scrape config — port,
  label and auth changes included — instead of silently breaking a hand-written
  CR. Only the `servicemonitors` and `podmonitors` CRDs are installed
  (`infra/controllers/prometheus-operator-crds/`); nothing runs
  prometheus-operator itself.
- **Hand-written VM-native CRs** (`VMServiceScrape`, `VMPodScrape`,
  `VMStaticScrape`) for targets no chart covers: see the table below.

Alerting rules are always hand-written `VMRule`s — the `PrometheusRule` CRD is
not installed.

### Components

- **VMSingle**: Long-term metrics storage (90d retention, 150Gi).
- **vmagent**: Lightweight metrics scraper, writes directly to VMSingle. Drops
  apiserver/kubelet histogram buckets globally — see `helmrelease.yaml`.
- **vmalert**: Evaluates alerting rules against VMSingle.
- **VMAlertmanager**: Pushover notifications, tiered by severity.
- **VictoriaLogs**: Centralized log storage (90d retention, 50Gi), managed via VLSingle CR.
- **victoria-logs-collector**: Fluent Bit DaemonSet that ships pod logs to VictoriaLogs.
- **Grafana**: Dashboards for metrics and logs, exposed at `grafana.tale.me` with OIDC via Pocket ID. Backed by PostgreSQL (CNPG).

### Data Flow

```
Pods → victoria-logs-collector (DaemonSet) → VictoriaLogs → Grafana
Targets → vmagent → VMSingle → Grafana
VMSingle → vmalert → VMAlertmanager → Pushover
```

### Alerting

The chart's `defaultRules` are **disabled**. kube-prometheus' ruleset assumes a
multi-tenant production fleet and produced 79 simultaneous alerts on three
nodes. Every rule now lives in `manifests/vmrules.yaml`, in three tiers:

| Group | Severity | Delivery |
|---|---|---|
| `homelab-page` | `critical` | Pushover priority 1, immediate, never muted |
| `homelab-notify` | `warning` | Pushover priority -1, batched hourly, muted 23:00–08:00 |
| `homelab-watchdog` | `none` | Always firing, currently inert (see below) |

Anything without a `critical` or `warning` severity routes to `blackhole`.

Two inhibition rules keep a single root cause from fanning out: a node going
down suppresses every warning cluster-wide, and a `critical` suppresses the
matching `warning` for the same alertname and namespace.

The watchdog fires permanently but routes to `blackhole` for now, so it does
nothing. Pointing it at an external ping endpoint is what would make silence
trustworthy: if the cluster, vmalert or Alertmanager dies, the pings stop and
the external service notifies. Until that is wired, a dead monitoring stack
is indistinguishable from a healthy cluster.

### Scrape Targets

Chart-managed targets are enabled through a values flag in the app's own
HelmRelease. Hand-written CRs stay colocated with their app/infra directory.

| Target | Type | Location |
|---|---|---|
| node-exporter | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| kube-state-metrics | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| kubelet / cAdvisor | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| kube-apiserver | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| CoreDNS | Built-in (k8s-stack) | `observability/helmrelease.yaml` |
| cert-manager | Chart ServiceMonitor | `infra/controllers/cert-manager/helmrelease.yaml` |
| MetalLB | Chart ServiceMonitor | `infra/controllers/metallb/helmrelease.yaml` |
| Grafana Operator | Chart ServiceMonitor | `infra/controllers/grafana-operator/helmrelease.yaml` |
| CNPG Operator | Chart PodMonitor | `infra/controllers/cloudnative-pg/helmrelease.yaml` |
| CNPG Postgres | Cluster `enablePodMonitor` | `infra/configs/cloudnative-pg/cluster.yaml` |
| Authentik | Chart ServiceMonitor | `authentik/helmrelease.yaml` |
| Forgejo | Chart ServiceMonitor | `forgejo/helmrelease.yaml` |
| Cilium Agent | VMServiceScrape | `infra/configs/cilium/` |
| Cilium Operator | VMServiceScrape | `infra/configs/cilium/` |
| Cilium Envoy | VMServiceScrape | `infra/configs/cilium/` |
| Hubble | VMServiceScrape | `infra/configs/cilium/` |
| Envoy Gateway | VMServiceScrape | `infra/configs/envoy/` |
| OpenEBS IO Engine | VMServiceScrape | `infra/configs/openebs/` |
| Blocky DNS | VMServiceScrape | `blocky/manifests/` |
| NUT exporter | VMStaticScrape | `observability/manifests/nut-scrape.yaml` |

The hand-written entries are not oversights: `gateway-helm` and `openebs` ship
no ServiceMonitor, Blocky is raw manifests with no chart, Cilium's manifest is
applied by Talos before any CRD exists, and the NUT exporter is off-cluster so
nothing can discover it.

### Dashboards (via Grafana Operator CRDs)

Imported by grafana.com ID at a **pinned revision**. `grafanaCom.id` alone tracks
whatever the author publishes next, which silently changes panels under you; the
pin makes an upgrade a deliberate bump. Dashboards stay colocated with their apps.

| Dashboard | ID | Rev | Folder | Location |
|---|---|---|---|---|
| Homelab Overview | — | — | Homelab | `observability/manifests/grafana-overview.yaml` |
| Cilium | — | — | Infrastructure | `observability/manifests/grafana-cilium.yaml` |
| OpenEBS / Mayastor | — | — | Infrastructure | `observability/manifests/grafana-openebs.yaml` |
| VictoriaMetrics Single | 10229 | 56 | VictoriaMetrics | `observability/` |
| vmagent | 12683 | 40 | VictoriaMetrics | `observability/` |
| vmalert | 14950 | 21 | VictoriaMetrics | `observability/` |
| VictoriaLogs Single | 22084 | 11 | Infrastructure | `observability/` |
| Alertmanager | 9578 | 4 | Alerting | `observability/` |
| Node Exporter Full | 1860 | 45 | Infrastructure | `observability/` |
| cert-manager | 20842 | 3 | Infrastructure | `observability/` |
| CloudNativePG | 20417 | 4 | Infrastructure | `observability/` |
| NUT UPS | 19308 | 4 | Infrastructure | `observability/` |
| Kubernetes Global | 15757 | 43 | Kubernetes | `observability/` |
| Kubernetes Pods | 15760 | 39 | Kubernetes | `observability/` |
| Blocky DNS | 17996 | 15 | Applications | `blocky/` |

Three dashboards are hand-written. **Homelab Overview** — 21 panels, every query
verified against live data — because no community dashboard knows which six
things matter here (nodes, capacity, OpenEBS pools, Postgres backups, the UPS,
and whether the monitoring stack itself is keeping up). **OpenEBS / Mayastor**
and **Cilium** because the community boards for both target metric schemas that
no longer exist.

Four imports were removed rather than repaired:

| Removed | Why |
|---|---|
| Envoy Gateway (22539) | unpublished from grafana.com — returns HTTP 404 |
| Forgejo (22363) | unpublished from grafana.com — returns HTTP 404 |
| Authentik (14837) | targets an older authentik metric schema; 21 of 24 metrics absent |
| Hubble (13542) | written for Cilium v1.8; metric names long since renamed |

Panels that stay blank on purpose: `alertmanager_cluster_*` (single replica, no
gossip), `windows_container_*` (no Windows nodes), `kube_ingress_info` and
`kube_hpa_labels` (no Ingress or HPA objects — this cluster uses Gateway API),
`node_hwmon_fan_*` and `node_power_supply_*` (hardware does not report them), and
the apiserver latency quantiles whose `_bucket` series vmagent drops.

### Secrets

| Secret | Namespace | Purpose |
|---|---|---|
| `pushover-credentials` | observability-system | Alertmanager Pushover notifications |
| `grafana-oidc` | observability-system | Grafana OIDC client credentials |
| `grafana-db-credentials` | observability-system | Grafana PostgreSQL password (cross-ns from CNPG) |
| `vmbackup-wasabi-credentials` | observability-system | VMSingle backup S3 credentials |
