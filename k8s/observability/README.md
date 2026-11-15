# Observability

Metrics, logs, and alerting for the cluster. VictoriaMetrics for storage,
Grafana for dashboards, and Pushover for anything that actually needs me.

### Setup

- **VMSingle** for metrics — 90d retention on 150Gi, deliberately not backed up:
  metrics are derived and self-regenerating, so losing them costs history rather
  than capability
- **vmagent** scrapes everything and writes straight to VMSingle
- **vmalert** + **VMAlertmanager** evaluate rules and deliver to Pushover
- **VictoriaLogs** for logs — 90d on 50Gi, fed by a Fluent Bit DaemonSet
- **Grafana** at `grafana.tale.me`, OIDC through Authentik, Postgres from CNPG
- Both operators (VictoriaMetrics, Grafana) are installed as infra controllers

### Scrape config

Charts that ship a `ServiceMonitor` or `PodMonitor` are preferred — the operator
converts them, so a chart upgrade carries its own scrape config along. Turn it on
with a values flag in the app's own HelmRelease.

Everything else gets a hand-written `VMServiceScrape`, `VMPodScrape`,
`VMStaticScrape` or `VMProbe` next to the app it scrapes: Cilium, Envoy Gateway
(control plane and data plane), OpenEBS, Blocky, Flux, the blackbox probes, and
the off-cluster NUT exporter. See the scrape-dependencies table below for the
ones a dashboard would break without.

Alert rules are always hand-written `VMRule`s in
[`manifests/vmrules.yaml`](manifests/vmrules.yaml); the `PrometheusRule` CRD
isn't installed.

### Alerting

kube-prometheus' `defaultRules` are off — they assume a production fleet and
bury three nodes in noise. Rules are split across three groups:

| Group | Severity | Delivery |
|---|---|---|
| `homelab-page` | `critical` | Pushover priority 1, never muted |
| `homelab-notify` | `warning` | Pushover priority -1, batched hourly, muted 23:00–08:00 |
| `homelab-watchdog` | `none` | always firing, routed to blackhole |

Anything else routes to blackhole. Inhibition rules keep one dead node from
fanning out into every warning in the cluster.

The watchdog does nothing until it points at an external ping endpoint. Until
then a dead monitoring stack looks exactly like a healthy cluster.

### Dashboards

The six provisioned dashboards live in the `Homelab` folder. The overview is
Grafana's home page; every five minutes, `grafana-navigation` stars dashboards
tagged `homelab` for active organization users. Personal stars are preserved.

| Dashboard | Default view |
|---|---|
| Homelab Overview | Alerts, reconciliation, reachability and node capacity |
| Kubernetes | Workload readiness, restarts, resource use and node requests |
| Network | Gateway errors, DNS activity, endpoint checks and packet drops |
| Storage & Backups | Pool/PVC capacity and current backup sources |
| Postgres | Availability, replication, backups and database sizes |
| Monitoring Health | Failed scrapes, ingestion, capacity and Pushover failures |

Troubleshooting charts are in collapsed rows. Cardinality analysis is in its
own collapsed row because it scans all current metric series. Current status
uses instant queries; historical charts retain deleted resources within the
selected time range. Historical top-k charts select their series at the end of
that range. Resource rankings use current tables.

HTTP probes run inside the cluster and follow redirects; a successful SSO
redirect does not establish application health. Blocky reporting counts metrics
targets, not successful DNS queries. Backup timestamps and mover results do not
verify that a restore will succeed.

The existing kube-state-metrics deployment watches VolSync ReplicationSources
and exports their current identity, last successful sync and next scheduled
sync. The backup table and VolSync summaries use this inventory to exclude
removed sources and restore destinations. No additional exporter is deployed.

Grafana is pinned to 13.3.1, which supports organization admins managing other
users' stars. The navigation job uses the operator-managed admin credentials;
it does not write directly to Grafana's database. Explore remains available.
Unused Drilldown apps, snapshots, public dashboards and Grafana-managed
alerting are disabled; vmalert and Alertmanager handle alert delivery.

### Dashboard validation

- Validate JSON and render `kubectl kustomize k8s/observability`.
- Validate changed queries through Grafana's `/api/ds/query`, including nested
  panels in collapsed rows. Check current results and the selected time range.
- Check labels, units and source availability, not just query success. A missing
  exporter must not become a healthy zero. Empty exception tables use explicit
  messages only when their source is reporting.
- Test exception tables with matching problems, no problems and unavailable
  telemetry. Empty-state rows must disappear when any real result is present.
- Counter event totals use `increase_prometheus` so replacing an exporter does
  not count an existing lifetime total as new events.
- Check table joins and empty states in Grafana. Fields named `Value #A` depend
  on query references; null field text does not replace an absent data frame.
- Render the pinned Helm chart when changing kube-state-metrics configuration.
  Validate custom-resource metrics against actual resources before deployment.

Datasource UIDs in
[`manifests/grafana-datasources.yaml`](manifests/grafana-datasources.yaml) must
match their names: the operator rewrites dashboard datasource references to
those UIDs. vmagent's external `cluster: homelab` label displaces exporter
`cluster` labels to `exported_cluster`; scope queries accordingly.

### Logs

Use Explore with VictoriaLogs for log investigation. Log volume alone does not
identify a failure. Grouped LogsQL stats queries over ranges longer than an hour
can collapse to one bucket; use ungrouped stats for longer trends and instant
grouped stats for totals. Text searches such as `error OR panic OR fatal` match
words rather than structured severity.

### Scrape dependencies

Several dashboards need scrape config that does not come from a chart:

| Signal | Where | Why it exists |
|---|---|---|
| `node` label on node-exporter | [`helmrelease.yaml`](helmrelease.yaml) | node-exporter was the only node-scoped job without one, so its series joined nothing |
| Envoy Gateway data plane | [`../infra/configs/envoy/service-monitor.yaml`](../infra/configs/envoy/service-monitor.yaml) | only the control plane was scraped; all HTTP ingress traffic was invisible |
| Flux | [`manifests/flux-scrape.yaml`](manifests/flux-scrape.yaml) | nothing watched the thing that runs the cluster |
| Reachability | [`manifests/blackbox.yaml`](manifests/blackbox.yaml) | every other signal is measured from inside |

The Envoy and Flux scrapes both use keep-lists or `labeldrop` rather than
collecting everything — Envoy publishes thousands of stats per listener, and
Flux's `revision` label churns a new series on every commit.
