#!/usr/bin/env python3
"""Parse Cloud Custodian outputs and print a PASS/FAIL summary table."""

import json
import os
import sys
from tabulate import tabulate
from common import load_state, POLICIES_DIR, OUTPUTS_DIR


def load_expectations():
    path = os.path.join(POLICIES_DIR, "expectations.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def count_violations(output_dir, policy_name):
    """Read the resources.json file for a policy and count violations."""
    resources_file = os.path.join(output_dir, policy_name, "resources.json")
    if not os.path.exists(resources_file):
        return 0, "no output"
    with open(resources_file) as f:
        resources = json.load(f)
    return len(resources), "ok"


def main():
    state = load_state()
    run_id = state.get("last_run_id")
    output_dir = state.get("last_run_output_dir")

    if not run_id or not output_dir:
        print("ERROR: No run found. Execute 03_run_custodian.py first.")
        sys.exit(1)

    manifest_path = os.path.join(output_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"ERROR: Manifest not found at {manifest_path}")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    expectations = load_expectations()

    print(f"Run ID:    {manifest['run_id']}")
    print(f"Timestamp: {manifest['timestamp']}")
    print(f"Account:   {manifest['account_id']}")
    print(f"Region:    {manifest['region']}")
    print()

    rows = []
    pass_count = 0
    fail_count = 0

    for policy_name in manifest["policies_run"]:
        violations, note = count_violations(output_dir, policy_name)

        # PASS = 0 violations (policy found no offending resources)
        # FAIL = >0 violations (policy found offending resources)
        if note != "ok":
            result = "SKIP"
        elif violations > 0:
            result = "FAIL"
            fail_count += 1
        else:
            result = "PASS"
            pass_count += 1

        expected = expectations.get(policy_name, "N/A")
        match = "Y" if result == expected else ("N" if expected != "N/A" else "-")

        rows.append([policy_name, violations, result, expected, match])

    headers = ["Policy", "Violations", "Result", "Expected", "Match"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()
    print(f"Total: {pass_count} PASS, {fail_count} FAIL, {len(rows)} total")

    if fail_count >= 2 and pass_count >= 1:
        print("Validation: meets requirement (>=2 FAIL, >=1 PASS)")
    else:
        print(f"Validation: does NOT meet requirement (need >=2 FAIL and >=1 PASS, got {fail_count} FAIL and {pass_count} PASS)")


if __name__ == "__main__":
    main()
