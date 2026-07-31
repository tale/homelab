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

All six live in one `Homelab` folder. Six dashboards do not need a folder tree —
the folders were only ever grouping things that were always opened together.

| Dashboard | Covers |
|---|---|
| Homelab Overview | is anything wrong, and where |
| Kubernetes | workloads, capacity, restarts |
| Network | gateway, DNS, reachability, Cilium |
| Storage & Backups | pools, PVCs, OpenEBS, backup freshness |
| Postgres | CNPG traffic, replication, WAL, archiver |
| Monitoring Health | the metrics pipeline watching itself |

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

### Panel design

The look is a design system, not per-panel taste, so it is applied by the
generator rather than remembered:

- **Categorical palette** — eight fixed hues assigned in slot order, never
  cycled. Validated against Grafana's dark panel surface (`#181b1f`): worst
  adjacent CVD ΔE 8.4, worst adjacent normal-vision ΔE 19.3, all eight clear 3:1
  contrast. A panel that would need a ninth colour gets a `topk(8, …)` cap
  instead — that is why the namespace and route panels are capped.
- **Colour follows the entity, not its rank.** Panels whose series are known up
  front pin each name to a slot explicitly (28 panels). Panels whose series are
  discovered at query time — `{{node}}`, `{{namespace}}`, `{{job}}` — use
  `palette-classic-by-name` (72 panels), so a series keeps its colour when the
  set changes. Note the trade-off: by-name draws from *Grafana's* classic
  palette, not the validated one above, because there is no way to hand Grafana
  a custom palette for series it has not seen yet. Stable identity was judged
  worth more than the validated hexes; the validated palette governs the
  fixed-series panels and every status colour.
- **Status colours are reserved** — good `#0ca30c`, warning `#fab219`, serious
  `#ec835a`, critical `#d03b3b`. They mean state, never identity, and never
  double as a series colour.
- **One measure per axis.** Never two scales on one plot: bytes/s and records/s
  became separate WAL panels, and log rows and log bytes separate storage
  panels, because sharing an axis invents a relationship between them.
- **2px lines, no legend on a single series** (the title already names it),
  recessive axes, a 2px gap between stacked bands.
- **Stat tiles are 4 or 6 columns wide** and never stretch past 8 — a number
  spanning half the screen reads as a mistake. Every row band sums to exactly
  24 columns, enforced by a layout pass, so there is no ragged gutter.

Geometry and colour are both checked by script before publishing. That catches
overlaps, ragged bands and unvalidated hues — but it does not catch everything,
and a round of real screenshots turned up four things no lint would have found:
a join that invented null table rows and painted them red, a stat tile printing
its whole label set instead of a pod name, response classes coloured from the
categorical ramp so 3xx read as red and 5xx as a pale tint, and "No data" on
panels whose empty state is the *good* one. Those now have `noValue` text.

### Logs

VictoriaLogs panels have one sharp edge worth writing down: a **grouped** LogsQL
stats query only buckets over ranges up to an hour. Past that it silently
collapses to a single value, which Grafana then draws as one bar jammed against
the right edge of the panel. Ungrouped stats bucket correctly at any range.

That is why the overview carries two log panels rather than one. `Log Error Rate`
is ungrouped, so it can be a real time series over any window. `Log Errors by
Namespace` is an instant query rendered as a bar gauge, sorted and capped at
eight, because grouping is exactly what breaks the range form.

Note also that the filter is a whole-word match on `error OR panic OR fatal`, not
a structured severity level — LogsQL word-matching means it will not fire on
`errorless`, but it will happily count an application logging the word "error" in
normal operation.

### The public board

`homelab-public` is the one dashboard meant for strangers. It is linked from the
repo README and published through Grafana's public-dashboard feature, which means
anonymous visitors execute its queries against VictoriaMetrics on every page load.
Three rules follow from that, and they are written into the manifest's header:
aggregates only, cheap queries only, and no template variables (public dashboards
do not support them, and an unresolved variable renders the board empty).

Publishing is **not declarative** — the Grafana operator has no field for it, so
the share was created once through the API:

```sh
curl -u "$creds" -X POST \
  "$GRAFANA/api/dashboards/uid/homelab-public/public-dashboards" \
  -H 'Content-Type: application/json' \
  -d '{"isEnabled":true,"annotationsEnabled":false,"timeSelectionEnabled":true,"share":"public"}'
```

The returned `accessToken` is what the README links to. Rebuilding this cluster
means re-publishing and updating that link.

The image in the README is served from `https://grafana.tale.me/live/homelab.png`
by [`manifests/grafana-live-image.yaml`](manifests/grafana-live-image.yaml): an
nginx and a sidecar that re-renders the public board every five minutes. The
sidecar holds no Grafana credentials — it renders the public URL, which needs no
auth — and it validates the PNG magic bytes rather than the status code, because
the renderer will happily return HTTP 200 with a PDF, an error card, or a
truncated file.

It renders 2200x805 rather than the whole board. Grafana's grid is proportional,
so a wider render does not show more — it just produces a banner instead of a
tall block that swallows the README. 805px lands immediately above the Ingress
row header, so nothing is sliced in half; reordering the public board's rows
means re-measuring it.

One trap worth knowing: setting `AUTH_TOKEN` on the renderer so the sidecar can
call it directly also stops *Grafana* rendering, and Grafana reports it as
"no image renderer found/installed" rather than as an auth failure. Both sides
read the same secret — see `GF_RENDERING_RENDERER_TOKEN` in
[`manifests/grafana.yaml`](manifests/grafana.yaml).

The `/live/` path is a second rule on the existing HTTPRoute rather than a new
hostname, so it needs no extra certificate or DNS record. Gateway API matches the
longest prefix first, so it wins over the catch-all that sends everything else to
Grafana behind Authentik.

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
