"""Ingest Cloud Custodian run outputs into the CoreStack compliance store."""

import json
import os
import logging

from . import store, normalize

log = logging.getLogger(__name__)


def ingest_run(run_dir: str) -> dict:
    """Read a custodian run directory and load everything into SQLite.

    Returns a summary dict with counts.
    """
    manifest_path = os.path.join(run_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"manifest.json not found in {run_dir}")

    with open(manifest_path) as f:
        manifest = json.load(f)

    run_id = manifest["run_id"]
    timestamp = manifest["timestamp"]
    account_id = manifest["account_id"]
    region = manifest["region"]

    conn = store.get_db()
    try:
        store.upsert_run(conn, run_id, timestamp, account_id, region)

        policies_ingested = 0
        findings_ingested = 0
        resources_ingested = 0

        for policy_name in manifest.get("policies_run", []):
            policy_dir = os.path.join(run_dir, policy_name)

            # Read metadata for policy details
            metadata_path = os.path.join(policy_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                log.warning(f"No metadata.json for policy {policy_name}, skipping")
                continue

            with open(metadata_path) as f:
                metadata = json.load(f)

            policy_meta = metadata.get("policy", {})
            policy_id = normalize.make_policy_id(policy_name)
            severity = normalize.extract_severity(policy_meta)
            category = normalize.extract_category(policy_meta)
            resource_type_raw = policy_meta.get("resource", "unknown")
            resource_type = normalize.detect_resource_type(resource_type_raw)
            description = policy_meta.get("description", "")

            store.upsert_policy(
                conn, policy_id, policy_name, "cloudcustodian",
                severity, category, resource_type, description,
            )
            policies_ingested += 1

            # Read resources (violations)
            resources_path = os.path.join(policy_dir, "resources.json")
            resources = []
            if os.path.exists(resources_path):
                with open(resources_path) as f:
                    resources = json.load(f)

            violations_count = len(resources)
            status = normalize.determine_status(violations_count)

            store.upsert_finding(conn, run_id, policy_id, status, violations_count, timestamp)
            findings_ingested += 1

            # Store individual resources
            for res in resources:
                raw_id = normalize.extract_raw_id(res, resource_type_raw)
                resource_key = normalize.make_resource_key(account_id, region, resource_type, raw_id)
                tags_json = normalize.extract_tags_json(res)

                store.upsert_resource(
                    conn, resource_key, policy_id, run_id, raw_id,
                    resource_type, region, account_id, tags_json,
                )
                resources_ingested += 1

            # Store evidence (full raw output)
            store.upsert_evidence(conn, policy_id, run_id, json.dumps(resources, default=str))

        conn.commit()
        log.info(f"Ingested run {run_id}: {policies_ingested} policies, "
                 f"{findings_ingested} findings, {resources_ingested} resources")

        return {
            "status": "ok",
            "run_id": run_id,
            "policies_ingested": policies_ingested,
            "findings_ingested": findings_ingested,
            "resources_ingested": resources_ingested,
        }
    finally:
        conn.close()
