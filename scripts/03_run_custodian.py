#!/usr/bin/env python3
"""Run Cloud Custodian policies and capture outputs."""

import json
import os
import subprocess
import sys
import time
import glob
import boto3
from common import load_state, get_region, POLICIES_DIR, OUTPUTS_DIR


def main():
    state = load_state()
    region = state.get("region", get_region())

    # Resolve account id
    sts = boto3.client("sts", region_name=region)
    account_id = sts.get_caller_identity()["Account"]

    run_id = f"run-{int(time.time())}"
    run_output_dir = os.path.join(OUTPUTS_DIR, run_id)
    os.makedirs(run_output_dir, exist_ok=True)

    policy_files = sorted(glob.glob(os.path.join(POLICIES_DIR, "*.yml")))
    if not policy_files:
        print("ERROR: No policy YAML files found in policies/. Run 02_generate_policies.py first.")
        sys.exit(1)

    print(f"Run ID:     {run_id}")
    print(f"Account:    {account_id}")
    print(f"Region:     {region}")
    print(f"Policies:   {len(policy_files)}")
    print(f"Output dir: {run_output_dir}")
    print()

    results = []

    for pf in policy_files:
        # Read the actual policy name from the YAML (custodian uses this for output dirs)
        import yaml
        with open(pf) as _f:
            pdata = yaml.safe_load(_f)
        pname = pdata["policies"][0]["name"]
        print(f"Running policy: {pname} ... ", end="", flush=True)

        # Find custodian executable in the same venv as this script
        venv_bin = os.path.dirname(sys.executable)
        custodian_bin = os.path.join(venv_bin, "custodian")

        cmd = [
            custodian_bin,
            "run", "-s", run_output_dir, pf,
            "--region", region,
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=os.environ.copy())

        if proc.returncode != 0:
            print(f"ERROR (rc={proc.returncode})")
            if proc.stderr:
                print(f"  stderr: {proc.stderr[:500]}")
            results.append({"policy_file": pf, "name": pname, "status": "error", "returncode": proc.returncode})
        else:
            print("OK")
            results.append({"policy_file": pf, "name": pname, "status": "ok", "returncode": 0})

    # Write manifest
    manifest = {
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "account_id": account_id,
        "region": region,
        "policies_run": [r["name"] for r in results],
        "output_dir": run_output_dir,
        "results": results,
    }

    manifest_path = os.path.join(run_output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Also save run_id in state for the summarizer
    state["last_run_id"] = run_id
    state["last_run_output_dir"] = run_output_dir
    from common import save_state
    save_state(state)

    print(f"\nAll policies executed. Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
