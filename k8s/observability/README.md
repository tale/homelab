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

Everything else gets a hand-written `VMServiceScrape` or `VMStaticScrape` next to
the app it scrapes: Cilium, Envoy Gateway, OpenEBS, Blocky, and the off-cluster
NUT exporter.

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

`GrafanaDashboard` CRs, colocated with the app they cover. Community imports are
pinned to a revision so an upstream edit can't quietly rewrite the panels.

| Folder | Dashboard | Source |
|---|---|---|
| Homelab | Homelab Overview | hand-written |
| Kubernetes | Kubernetes | hand-written |
| Infrastructure | Ingress & DNS | hand-written |
| Infrastructure | Storage & Backups | hand-written |
| Infrastructure | Cilium | hand-written |
| Infrastructure | OpenEBS / Mayastor | hand-written |
| Infrastructure | Postgres | hand-written |
| Infrastructure | Node Exporter Full | grafana.com 1860 |
| Monitoring | Monitoring Health | hand-written |

Most community boards were written for clusters that look nothing like this one
and rendered mostly empty — Alertmanager assumed a gossip cluster, the Kubernetes
Views pair leaned on `windows_*` metrics and recording rules `defaultRules`
turned off, and the VictoriaMetrics quartet spent 44 panels on Kafka and
persistent queues. All were replaced by the hand-written boards above.

CloudNativePG went the same way for a subtler reason worth remembering: its
`$cluster` variable regex-extracts `cluster="..."` from series text, expecting
the Postgres cluster name, but vmagent's `cluster: homelab` external label
displaces the exporter's own to `exported_cluster`. Relabelling it back doesn't
help — external labels are applied after metric relabeling and always win. Any
import keyed on a `cluster` label meaning something other than "this Kubernetes
cluster" will fail here the same way.

Every hand-written panel is checked against live data before it lands, and the
check has to go through Grafana's `/api/ds/query`, not straight to
VictoriaMetrics — querying VM directly validates the PromQL but not the panel's
datasource reference, which is exactly how 103 broken CloudNativePG panels once
passed an audit. The bar is zero empty panels.

Node Exporter Full is the sole exception: about a dozen of its panels stay blank
for collectors Talos doesn't ship, which is the price of not maintaining 288
queries by hand.

Overview panels assume the `node` label exists on node-exporter series; see the
`prometheus-node-exporter` block in [`helmrelease.yaml`](helmrelease.yaml).
Ingress panels need the Envoy Gateway data plane scrape in
[`k8s/infra/configs/envoy/service-monitor.yaml`](../infra/configs/envoy/service-monitor.yaml).
