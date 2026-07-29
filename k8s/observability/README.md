# Observability

Metrics, logs, and alerting for the cluster. VictoriaMetrics for storage,
Grafana for dashboards, and Pushover for anything that actually needs me.

### Setup

- **VMSingle** for metrics — 90d retention on 150Gi, backed up to Wasabi
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

Every dashboard is a hand-written `GrafanaDashboard` CR. There are no community
imports left.

| Folder | Dashboard | Covers |
|---|---|---|
| Homelab | Homelab Overview | is anything wrong, and where |
| Kubernetes | Kubernetes | workloads, capacity, restarts |
| Infrastructure | Network | gateway, DNS, reachability, Cilium |
| Infrastructure | Storage & Backups | pools, PVCs, OpenEBS, backup freshness |
| Infrastructure | Postgres | CNPG traffic, replication, WAL, archiver |
| Monitoring | Monitoring Health | the metrics pipeline watching itself |

The imports all went the same way: written for clusters that look nothing like
this one, and mostly empty. Alertmanager assumed a gossip cluster, the Kubernetes
Views pair leaned on `windows_*` metrics and recording rules `defaultRules`
turned off, the VictoriaMetrics quartet spent 44 panels on Kafka and persistent
queues, and Node Exporter Full wanted collectors Talos does not ship.

Two failure modes are worth remembering, because both produced a dashboard that
looked fine in review and rendered blank in the browser:

- **Datasource references.** The operator rewrites an import's panels to
  `{"uid": "<datasourceName>"}`. If the datasource has a generated UUID instead
  of a matching `uid`, every panel silently resolves to nothing. The `uid`
  fields in [`manifests/grafana-datasources.yaml`](manifests/grafana-datasources.yaml)
  are load-bearing for this reason.
- **The `cluster` label.** vmagent stamps `cluster: homelab` as an external
  label, which displaces any exporter that publishes its own `cluster` to
  `exported_cluster`. CloudNativePG's board keyed its `$cluster` variable on it
  and resolved to `homelab`. Relabelling it back does not work — external labels
  are applied after metric relabeling and always win.

Panels are validated against live data before they land, and the check has to go
through Grafana's `/api/ds/query` rather than straight to VictoriaMetrics:
querying VM directly validates the PromQL but not the panel's datasource
reference, which is exactly how 103 broken CloudNativePG panels once passed an
audit. The bar is zero empty panels.

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
