#!/usr/bin/env python3
"""Generate Cloud Custodian policy YAML files."""

import os
import yaml
from common import load_state, POLICIES_DIR, SAFE_MODE


POLICIES = [
    {
        "filename": "s3-public-bucket.yml",
        "policy": {
            "policies": [
                {
                    "name": "s3-public-bucket",
                    "description": "Detect S3 buckets with public access via bucket policy",
                    "resource": "s3",
                    "filters": [
                        {"type": "has-statement", "statements": [{"Effect": "Allow", "Principal": "*"}]},
                    ],
                    "tags": ["severity:high", "owner:AgenticBricks", "category:security"],
                }
            ]
        },
        "expected": "FAIL" if not SAFE_MODE else "PASS",
    },
    {
        "filename": "s3-default-encryption.yml",
        "policy": {
            "policies": [
                {
                    "name": "s3-default-encryption-enabled",
                    "description": "Verify S3 buckets have default encryption enabled",
                    "resource": "s3",
                    "filters": [
                        {
                            "type": "bucket-encryption",
                            "state": False,
                        },
                    ],
                    "tags": ["severity:high", "owner:AgenticBricks", "category:security"],
                }
            ]
        },
        # This filter finds buckets WITHOUT encryption -> our bucket HAS encryption -> not matched -> PASS
        "expected": "PASS",
    },
    {
        "filename": "ec2-required-tags.yml",
        "policy": {
            "policies": [
                {
                    "name": "ec2-required-tags",
                    "description": "EC2 instances must have CostCenter and Environment tags",
                    "resource": "ec2",
                    "filters": [
                        {
                            "or": [
                                {"tag:CostCenter": "absent"},
                                {"tag:Environment": "absent"},
                            ]
                        },
                    ],
                    "tags": ["severity:medium", "owner:AgenticBricks", "category:governance"],
                }
            ]
        },
        "expected": "FAIL",
    },
    {
        "filename": "ebs-unused-volumes.yml",
        "policy": {
            "policies": [
                {
                    "name": "ebs-unused-volumes",
                    "description": "Find EBS volumes that are not attached to any instance",
                    "resource": "ebs",
                    "filters": [
                        {"State": "available"},
                    ],
                    "tags": ["severity:low", "owner:AgenticBricks", "category:cost"],
                }
            ]
        },
        "expected": "FAIL",
    },
    {
        "filename": "ebs-encrypted.yml",
        "policy": {
            "policies": [
                {
                    "name": "ebs-encrypted",
                    "description": "Find EBS volumes that are NOT encrypted",
                    "resource": "ebs",
                    "filters": [
                        {"Encrypted": False},
                    ],
                    "tags": ["severity:high", "owner:AgenticBricks", "category:security"],
                }
            ]
        },
        # Finds unencrypted volumes. Our volume IS encrypted -> not matched -> PASS
        "expected": "PASS",
    },
]


def main():
    state = load_state()
    if not state:
        print("WARNING: state.json not found. Run 01_create_resources.py first.")

    os.makedirs(POLICIES_DIR, exist_ok=True)

    print(f"Generating {len(POLICIES)} policy files in {POLICIES_DIR}/")
    print()

    for p in POLICIES:
        filepath = os.path.join(POLICIES_DIR, p["filename"])
        with open(filepath, "w") as f:
            yaml.dump(p["policy"], f, default_flow_style=False, sort_keys=False)
        print(f"  {p['filename']:40s}  expected: {p['expected']}")

    # Write expectations manifest for the summarizer
    import json
    expectations = {p["policy"]["policies"][0]["name"]: p["expected"] for p in POLICIES}
    manifest_path = os.path.join(POLICIES_DIR, "expectations.json")
    with open(manifest_path, "w") as f:
        json.dump(expectations, f, indent=2)
    print(f"\n  expectations.json written.")
    print("\nAll policies generated.")


if __name__ == "__main__":
    main()
