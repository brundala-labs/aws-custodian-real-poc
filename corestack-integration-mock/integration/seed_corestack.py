"""Seed fake CoreStack-native policies for unified demo."""

import logging
from . import store

log = logging.getLogger(__name__)

CORESTACK_POLICIES = [
    {
        "policy_id": "corestack:iam-mfa-enabled",
        "name": "IAM MFA Enabled for Console Users",
        "source": "corestack",
        "severity": "high",
        "category": "security",
        "resource_types": "iam-user",
        "description": "Ensure all IAM users with console access have MFA enabled.",
        "status": "FAIL",
        "violations_count": 2,
    },
    {
        "policy_id": "corestack:cost-budget-alert",
        "name": "Monthly Budget Alert Configured",
        "source": "corestack",
        "severity": "medium",
        "category": "cost",
        "resource_types": "aws-account",
        "description": "Verify that AWS Budgets alert is configured for the account.",
        "status": "PASS",
        "violations_count": 0,
    },
    {
        "policy_id": "corestack:cloudtrail-enabled",
        "name": "CloudTrail Logging Enabled",
        "source": "corestack",
        "severity": "high",
        "category": "security",
        "resource_types": "cloudtrail",
        "description": "Ensure CloudTrail is enabled in all regions for audit logging.",
        "status": "FAIL",
        "violations_count": 1,
    },
]


def seed(run_id: str = "corestack-baseline", account_id: str = "864387741092",
         region: str = "us-east-1", timestamp: str = "2026-02-03T00:00:00Z"):
    """Insert fake CoreStack-native policies and findings."""
    conn = store.get_db()
    try:
        store.upsert_run(conn, run_id, timestamp, account_id, region)

        for p in CORESTACK_POLICIES:
            store.upsert_policy(
                conn, p["policy_id"], p["name"], p["source"],
                p["severity"], p["category"], p["resource_types"], p["description"],
            )
            store.upsert_finding(
                conn, run_id, p["policy_id"], p["status"],
                p["violations_count"], timestamp,
            )
            # Seed placeholder evidence
            if p["violations_count"] > 0:
                evidence = f'[{{"note": "Simulated finding from CoreStack native policy: {p["name"]}"}}]'
            else:
                evidence = "[]"
            store.upsert_evidence(conn, p["policy_id"], run_id, evidence)

        conn.commit()
        log.info(f"Seeded {len(CORESTACK_POLICIES)} CoreStack-native policies")
    finally:
        conn.close()
