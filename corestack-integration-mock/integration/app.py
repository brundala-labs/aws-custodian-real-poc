"""FastAPI mock CoreStack REST API."""

import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import store, ingest, seed_corestack
from .models import (
    SummaryOut, FindingOut, PolicyOut, ResourceOut, EvidenceOut, IngestResult,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(
    title="CoreStack – Unified Policy Compliance API (Mock)",
    version="0.1.0",
    description="Mock integration layer that ingests Cloud Custodian outputs and exposes a unified compliance API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    store.init_db()
    seed_corestack.seed()
    log.info("Database initialized and CoreStack policies seeded.")

    # Auto-ingest if CUSTODIAN_RUN_DIR is set
    run_dir = os.environ.get("CUSTODIAN_RUN_DIR")
    if run_dir and os.path.isdir(run_dir):
        try:
            result = ingest.ingest_run(run_dir)
            log.info(f"Auto-ingested from {run_dir}: {result}")
        except Exception as e:
            log.error(f"Auto-ingest failed: {e}")


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/ingest", response_model=IngestResult)
def ingest_endpoint(path: str = Query(..., description="Path to custodian run output directory")):
    """Ingest Cloud Custodian run outputs from a local path."""
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"Directory not found: {path}")
    manifest = os.path.join(path, "manifest.json")
    if not os.path.exists(manifest):
        raise HTTPException(status_code=400, detail=f"manifest.json not found in: {path}")
    try:
        result = ingest.ingest_run(path)
        return IngestResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary", response_model=SummaryOut)
def summary_endpoint():
    """Get compliance summary KPIs."""
    conn = store.get_db()
    try:
        return SummaryOut(**store.get_summary(conn))
    finally:
        conn.close()


@app.get("/findings", response_model=list[FindingOut])
def findings_endpoint(
    source: Optional[str] = Query(None, description="Filter by source: cloudcustodian, corestack"),
    status: Optional[str] = Query(None, description="Filter by status: PASS, FAIL"),
    severity: Optional[str] = Query(None, description="Filter by severity: high, medium, low"),
):
    """List all findings with optional filters."""
    conn = store.get_db()
    try:
        rows = store.get_all_findings(conn, source=source, status=status, severity=severity)
        return [FindingOut(**r) for r in rows]
    finally:
        conn.close()


@app.get("/policies", response_model=list[PolicyOut])
def policies_endpoint():
    """List all policies."""
    conn = store.get_db()
    try:
        return [PolicyOut(**r) for r in store.get_all_policies(conn)]
    finally:
        conn.close()


@app.get("/policies/detail", response_model=PolicyOut)
def policy_detail_endpoint(policy_id: str = Query(..., description="Policy ID e.g. custodian:s3-public-bucket")):
    """Get a single policy by ID."""
    conn = store.get_db()
    try:
        p = store.get_policy(conn, policy_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"Policy not found: {policy_id}")
        return PolicyOut(**p)
    finally:
        conn.close()


@app.get("/policies/resources", response_model=list[ResourceOut])
def policy_resources_endpoint(
    policy_id: str = Query(..., description="Policy ID"),
    run_id: Optional[str] = None,
):
    """List violating resources for a policy."""
    conn = store.get_db()
    try:
        rows = store.get_policy_resources(conn, policy_id, run_id)
        return [ResourceOut(**r) for r in rows]
    finally:
        conn.close()


@app.get("/policies/evidence", response_model=list[EvidenceOut])
def policy_evidence_endpoint(
    policy_id: str = Query(..., description="Policy ID"),
    run_id: Optional[str] = None,
):
    """Get raw evidence JSON for a policy."""
    conn = store.get_db()
    try:
        rows = store.get_policy_evidence(conn, policy_id, run_id)
        return [EvidenceOut(**r) for r in rows]
    finally:
        conn.close()
