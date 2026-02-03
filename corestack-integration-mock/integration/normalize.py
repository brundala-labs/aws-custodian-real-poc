"""Normalization rules: Cloud Custodian output -> CoreStack compliance model."""

import json
import re


def slug(name: str) -> str:
    """Convert policy name to a URL-safe slug."""
    return re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")


def make_policy_id(policy_name: str) -> str:
    return f"custodian:{slug(policy_name)}"


def extract_severity(policy_meta: dict) -> str:
    """Extract severity from custodian policy tags list like ['severity:high']."""
    tags = policy_meta.get("tags", [])
    if isinstance(tags, list):
        for t in tags:
            if isinstance(t, str) and t.startswith("severity:"):
                return t.split(":", 1)[1].lower()
    return "medium"


def extract_category(policy_meta: dict) -> str:
    tags = policy_meta.get("tags", [])
    if isinstance(tags, list):
        for t in tags:
            if isinstance(t, str) and t.startswith("category:"):
                return t.split(":", 1)[1].lower()
    return "general"


def determine_status(violations_count: int) -> str:
    return "PASS" if violations_count == 0 else "FAIL"


def make_resource_key(account_id: str, region: str, resource_type: str, raw_id: str) -> str:
    return f"aws:{account_id}:{region}:{resource_type}:{raw_id}"


def detect_resource_type(policy_resource: str) -> str:
    """Map custodian resource type to a human-readable AWS type."""
    mapping = {
        "s3": "s3-bucket",
        "ec2": "ec2-instance",
        "ebs": "ebs-volume",
        "rds": "rds-instance",
        "iam-user": "iam-user",
        "iam-role": "iam-role",
        "security-group": "ec2-security-group",
        "elb": "elb",
        "alb": "alb",
    }
    return mapping.get(policy_resource, policy_resource)


def extract_raw_id(resource: dict, resource_type: str) -> str:
    """Pull the primary identifier from a custodian resource blob."""
    # S3
    if "Name" in resource and resource_type == "s3":
        return resource["Name"]
    # EC2
    if "InstanceId" in resource:
        return resource["InstanceId"]
    # EBS
    if "VolumeId" in resource:
        return resource["VolumeId"]
    # Fallback
    for key in ("ResourceId", "Id", "Arn"):
        if key in resource:
            return resource[key]
    return "unknown"


def extract_tags_json(resource: dict) -> str:
    """Extract tags from a custodian resource as JSON string."""
    tags = resource.get("Tags", [])
    if isinstance(tags, list):
        tag_dict = {t["Key"]: t["Value"] for t in tags if "Key" in t and "Value" in t}
        return json.dumps(tag_dict)
    return "{}"
