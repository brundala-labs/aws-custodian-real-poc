"""Pydantic models for the CoreStack integration mock."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class PolicyOut(BaseModel):
    policy_id: str
    name: str
    source: str
    severity: str
    category: str
    resource_types: str
    description: str


class RunOut(BaseModel):
    run_id: str
    timestamp: str
    account_id: str
    region: str


class FindingOut(BaseModel):
    finding_id: int
    run_id: str
    policy_id: str
    policy_name: str
    source: str
    status: str
    violations_count: int
    severity: str
    category: str
    resource_types: str
    last_evaluated: str


class ResourceOut(BaseModel):
    resource_key: str
    policy_id: str
    run_id: str
    raw_id: str
    type: str
    region: str
    account_id: str
    tags_json: str


class EvidenceOut(BaseModel):
    policy_id: str
    run_id: str
    evidence_json: str


class SummaryOut(BaseModel):
    total_policies: int
    passing: int
    failing: int
    last_evaluated: Optional[str]
    by_source: dict
    by_severity: dict


class IngestResult(BaseModel):
    status: str
    run_id: str
    policies_ingested: int
    findings_ingested: int
    resources_ingested: int
