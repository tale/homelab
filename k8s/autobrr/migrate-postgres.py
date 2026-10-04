import os
import re
import shutil
import sqlite3
import subprocess
from pathlib import Path
from urllib.parse import quote


def query(sql):
    return subprocess.check_output(
        ["psql", "-X", "-At", "-v", "ON_ERROR_STOP=1", "-c", sql], text=True
    ).strip()


def convert(working_path, database_url, log_path, *, is_dry_run=False):
    command = [
        "/migration-tools/autobrrctl", "db:convert", "--sqlite-db", str(working_path),
        "--postgres-url", database_url,
    ]
    if is_dry_run:
        command.append("--dry-run")

    with log_path.open("w") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)

    output = re.sub(r"\x1b\[[0-9;]*m", "", log_path.read_text())
    if result.returncode or re.search(r"\bERR\b|failed|foreign key violations", output, re.IGNORECASE):
        raise RuntimeError(f"Conversion reported errors; inspect {log_path}.")


def copy_indexer_deprecations(snapshot_path):
    snapshot = sqlite3.connect(f"file:{snapshot_path}?mode=ro", uri=True)
    rows = snapshot.execute("SELECT * FROM indexer_deprecation")
    columns = ", ".join('"' + column[0].replace('"', '""') + '"' for column in rows.description)
    lines = []
    for row in rows:
        values = [
            "\\N" if value is None else str(value).replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")
            for value in row
        ]
        lines.append("\t".join(values) + "\n")
    snapshot.close()

    subprocess.run(
        ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-c", f"COPY indexer_deprecation ({columns}) FROM STDIN"],
        input="".join(lines), text=True, check=True, stdout=subprocess.DEVNULL,
    )


def migrate():
    os.umask(0o077)

    if query("SELECT to_regclass('public.homelab_migrations')"):
        if query("SELECT count(*) FROM homelab_migrations WHERE name = 'autobrr-sqlite-v1'") == "1":
            print("Postgres migration already completed.", flush=True)
            return
        raise RuntimeError("Unexpected migration marker table; refusing to overwrite Postgres.")

    if query("SELECT count(*) FROM pg_tables WHERE schemaname = 'public'") != "0":
        raise RuntimeError("Postgres is not empty; inspect the previous migration before retrying.")

    source_path = Path("/config/autobrr.db")
    if not source_path.is_file():
        raise RuntimeError("SQLite database is missing; refusing to start an empty Postgres database.")

    migration_path = Path("/config/postgres-migration")
    migration_path.mkdir(exist_ok=True)
    snapshot_path = migration_path / "source.db"
    if snapshot_path.exists():
        raise RuntimeError("A migration snapshot already exists; inspect it before retrying.")

    source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    snapshot = sqlite3.connect(migration_path / "source.tmp")
    source.backup(snapshot)
    source.close()
    if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("SQLite snapshot failed its integrity check.")

    ignored_tables = {"schema_migrations", "sessions", "release_cleanup_job"}
    tables = [
        row[0]
        for row in snapshot.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        if not row[0].startswith("sqlite_") and row[0] not in ignored_tables
    ]
    expected_counts = {}
    for table in tables:
        identifier = '"' + table.replace('"', '""') + '"'
        expected_counts[table] = snapshot.execute(f"SELECT count(*) FROM {identifier}").fetchone()[0]
    snapshot.close()
    (migration_path / "source.tmp").rename(snapshot_path)

    working_path = migration_path / "working.db"
    shutil.copyfile(snapshot_path, working_path)
    database_url = (
        f"postgres://{quote(os.environ['PGUSER'], safe='')}@"
        f"{os.environ['PGHOST']}:{os.environ['PGPORT']}/"
        f"{quote(os.environ['PGDATABASE'], safe='')}?sslmode={os.environ['PGSSLMODE']}"
    )
    convert(working_path, database_url, migration_path / "schema.log", is_dry_run=True)
    # The fresh schema seeds profiles that conflict with the profiles being imported.
    query("DELETE FROM release_profile_duplicate")
    convert(working_path, database_url, migration_path / "conversion.log")
    # autobrrctl v1.87.0 omits this table from its conversion list.
    copy_indexer_deprecations(snapshot_path)

    for table, expected_count in expected_counts.items():
        identifier = '"' + table.replace('"', '""') + '"'
        actual_count = int(query(f"SELECT count(*) FROM {identifier}"))
        if actual_count != expected_count:
            raise RuntimeError(f"Row count mismatch for {table}: SQLite={expected_count}, Postgres={actual_count}.")

    query("""
        BEGIN;
        DO $$
        DECLARE column_record record;
        BEGIN
            FOR column_record IN
                SELECT table_name, column_name,
                       pg_get_serial_sequence(format('%I.%I', table_schema, table_name), column_name) AS sequence_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND column_default LIKE 'nextval(%'
            LOOP
                EXECUTE format('SELECT setval(%L, COALESCE(MAX(%I), 1), MAX(%I) IS NOT NULL) FROM %I',
                    column_record.sequence_name, column_record.column_name,
                    column_record.column_name, column_record.table_name);
            END LOOP;
        END $$;
        CREATE TABLE homelab_migrations (name text PRIMARY KEY, completed_at timestamptz NOT NULL DEFAULT now());
        INSERT INTO homelab_migrations (name) VALUES ('autobrr-sqlite-v1');
        COMMIT;
    """)
    print(f"Migration verified across {len(expected_counts)} tables; SQLite snapshot retained.", flush=True)


if __name__ == "__main__":
    migrate()
