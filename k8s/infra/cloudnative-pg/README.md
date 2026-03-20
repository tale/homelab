# CloudNativePG

Centralized PostgreSQL cluster managed by the
[CloudNativePG](https://cloudnative-pg.io/) operator. Provides a shared
database for applications that need PostgreSQL (Forgejo, Grafana, Home
Assistant, Blocky).

### Setup

- The CNPG operator runs in `cnpg-system` and manages PostgreSQL `Cluster` CRDs.
- A 2-instance cluster (`central-postgres`) provides HA with automatic failover.
- Storage is backed by OpenEBS replicated NVMe (`cluster-nvmf`).
- Prometheus monitoring and a Grafana dashboard are enabled by default.
- Each application gets its own database and role via `postInitApplicationSQL`.

### Connecting

Applications connect via the read-write service:
```
central-postgres-rw.cnpg-system.svc.cluster.local:5432
```

Credentials for the `app` superuser are stored in:
```
central-postgres-app (Secret in cnpg-system)
```
