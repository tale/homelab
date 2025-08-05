# Blocky
[Blocky](https://github.com/0xERR0R/blocky) is an advanced DNS proxy similar
to Pi-hole or AdGuard Home, but with a focus on performance and flexibility.
It also supports high-availability setups with multiple instances, allowing
more than 1 point of failure especially when concerning something important like
DNS resolution.

### Why not use Pi-hole or AdGuard Home?
This is designed to be cloud-native and to run in a containerized environment.
It's also much more lightweight since it only exports metrics and a query log
which I eventually plan to connect to a Grafana dashboard.

### Setup
- Redis in-memory cache for DNS caching and sharing between instances
- (Future) PostgreSQL for persistent storage of query logs
- Blocky is setup to run on each node and export metrics to Prometheus
