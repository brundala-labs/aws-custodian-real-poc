"""SQLite schema and CRUD operations."""

import json
import os
import sqlite3
from typing import Optional

DB_PATH = os.environ.get("CORESTACK_DB", os.path.join(os.path.dirname(__file__), "..", "corestack.db"))


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS policies (
            policy_id   TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            source      TEXT NOT NULL DEFAULT 'cloudcustodian',
            severity    TEXT NOT NULL DEFAULT 'medium',
            category    TEXT NOT NULL DEFAULT 'general',
            resource_types TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS runs (
            run_id      TEXT PRIMARY KEY,
            timestamp   TEXT NOT NULL,
            account_id  TEXT NOT NULL,
            region      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS findings (
            finding_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id          TEXT NOT NULL,
            policy_id       TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'UNKNOWN',
            violations_count INTEGER NOT NULL DEFAULT 0,
            last_evaluated  TEXT NOT NULL,
            UNIQUE(run_id, policy_id),
            FOREIGN KEY (run_id) REFERENCES runs(run_id),
            FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
        );

        CREATE TABLE IF NOT EXISTS resources (
            resource_key TEXT NOT NULL,
            policy_id    TEXT NOT NULL,
            run_id       TEXT NOT NULL,
            raw_id       TEXT NOT NULL,
            type         TEXT NOT NULL,
            region       TEXT NOT NULL,
            account_id   TEXT NOT NULL,
            tags_json    TEXT NOT NULL DEFAULT '{}',
            PRIMARY KEY (resource_key, policy_id, run_id),
            FOREIGN KEY (run_id) REFERENCES runs(run_id),
            FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
        );

        CREATE TABLE IF NOT EXISTS evidence (
            policy_id     TEXT NOT NULL,
            run_id        TEXT NOT NULL,
            evidence_json TEXT NOT NULL DEFAULT '[]',
            PRIMARY KEY (policy_id, run_id),
            FOREIGN KEY (run_id) REFERENCES runs(run_id),
            FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
        );
    """)
    conn.commit()
    conn.close()


# ── Upserts ──────────────────────────────────────────────────────────────────

def upsert_policy(conn, policy_id, name, source, severity, category, resource_types, description):
    conn.execute("""
        INSERT INTO policies (policy_id, name, source, severity, category, resource_types, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(policy_id) DO UPDATE SET
            name=excluded.name, source=excluded.source, severity=excluded.severity,
            category=excluded.category, resource_types=excluded.resource_types,
            description=excluded.description
    """, (policy_id, name, source, severity, category, resource_types, description))


def upsert_run(conn, run_id, timestamp, account_id, region):
    conn.execute("""
        INSERT INTO runs (run_id, timestamp, account_id, region)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            timestamp=excluded.timestamp, account_id=excluded.account_id, region=excluded.region
    """, (run_id, timestamp, account_id, region))


def upsert_finding(conn, run_id, policy_id, status, violations_count, last_evaluated):
    conn.execute("""
        INSERT INTO findings (run_id, policy_id, status, violations_count, last_evaluated)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(run_id, policy_id) DO UPDATE SET
            status=excluded.status, violations_count=excluded.violations_count,
            last_evaluated=excluded.last_evaluated
    """, (run_id, policy_id, status, violations_count, last_evaluated))


def upsert_resource(conn, resource_key, policy_id, run_id, raw_id, rtype, region, account_id, tags_json):
    conn.execute("""
        INSERT INTO resources (resource_key, policy_id, run_id, raw_id, type, region, account_id, tags_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(resource_key, policy_id, run_id) DO UPDATE SET
            raw_id=excluded.raw_id, type=excluded.type, region=excluded.region,
            account_id=excluded.account_id, tags_json=excluded.tags_json
    """, (resource_key, policy_id, run_id, raw_id, rtype, region, account_id, tags_json))


def upsert_evidence(conn, policy_id, run_id, evidence_json):
    conn.execute("""
        INSERT INTO evidence (policy_id, run_id, evidence_json)
        VALUES (?, ?, ?)
        ON CONFLICT(policy_id, run_id) DO UPDATE SET evidence_json=excluded.evidence_json
    """, (policy_id, run_id, evidence_json))


# ── Queries ──────────────────────────────────────────────────────────────────

def get_summary(conn) -> dict:
    row = conn.execute("""
        SELECT
            COUNT(DISTINCT p.policy_id) AS total,
            SUM(CASE WHEN f.status='PASS' THEN 1 ELSE 0 END) AS passing,
            SUM(CASE WHEN f.status='FAIL' THEN 1 ELSE 0 END) AS failing,
            MAX(f.last_evaluated) AS last_evaluated
        FROM policies p
        LEFT JOIN findings f ON p.policy_id = f.policy_id
    """).fetchone()

    by_source = {}
    for r in conn.execute("""
        SELECT p.source, f.status, COUNT(*) AS cnt
        FROM policies p LEFT JOIN findings f ON p.policy_id = f.policy_id
        GROUP BY p.source, f.status
    """):
        src = r["source"]
        if src not in by_source:
            by_source[src] = {}
        by_source[src][r["status"] or "NO_DATA"] = r["cnt"]

    by_severity = {}
    for r in conn.execute("""
        SELECT p.severity, f.status, COUNT(*) AS cnt
        FROM policies p LEFT JOIN findings f ON p.policy_id = f.policy_id
        GROUP BY p.severity, f.status
    """):
        sev = r["severity"]
        if sev not in by_severity:
            by_severity[sev] = {}
        by_severity[sev][r["status"] or "NO_DATA"] = r["cnt"]

    return {
        "total_policies": row["total"] or 0,
        "passing": row["passing"] or 0,
        "failing": row["failing"] or 0,
        "last_evaluated": row["last_evaluated"],
        "by_source": by_source,
        "by_severity": by_severity,
    }


def get_all_findings(conn, source: Optional[str] = None, status: Optional[str] = None,
                     severity: Optional[str] = None) -> list[dict]:
    query = """
        SELECT f.finding_id, f.run_id, f.policy_id, p.name AS policy_name, p.source,
               f.status, f.violations_count, p.severity, p.category, p.resource_types,
               f.last_evaluated
        FROM findings f JOIN policies p ON f.policy_id = p.policy_id
        WHERE 1=1
    """
    params = []
    if source:
        query += " AND p.source = ?"
        params.append(source)
    if status:
        query += " AND f.status = ?"
        params.append(status)
    if severity:
        query += " AND p.severity = ?"
        params.append(severity)
    query += " ORDER BY f.status DESC, p.severity, p.name"
    return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_all_policies(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM policies ORDER BY source, name").fetchall()]


def get_policy(conn, policy_id: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM policies WHERE policy_id = ?", (policy_id,)).fetchone()
    return dict(row) if row else None


def get_policy_resources(conn, policy_id: str, run_id: Optional[str] = None) -> list[dict]:
    if run_id:
        rows = conn.execute(
            "SELECT * FROM resources WHERE policy_id = ? AND run_id = ?", (policy_id, run_id)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM resources WHERE policy_id = ?", (policy_id,)).fetchall()
    return [dict(r) for r in rows]


def get_policy_evidence(conn, policy_id: str, run_id: Optional[str] = None) -> list[dict]:
    if run_id:
        rows = conn.execute(
            "SELECT * FROM evidence WHERE policy_id = ? AND run_id = ?", (policy_id, run_id)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM evidence WHERE policy_id = ?", (policy_id,)).fetchall()
    return [dict(r) for r in rows]
