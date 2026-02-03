#!/usr/bin/env python3
"""One-shot ingestion script: reads custodian outputs and loads into SQLite."""

import os
import sys
import logging

# Add parent dir to path so integration package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from integration import store, ingest, seed_corestack

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main():
    run_dir = os.environ.get("CUSTODIAN_RUN_DIR")
    if not run_dir:
        if len(sys.argv) > 1:
            run_dir = sys.argv[1]
        else:
            print("Usage: python ingest_once.py <path_to_custodian_run_dir>")
            print("  or set CUSTODIAN_RUN_DIR environment variable")
            sys.exit(1)

    if not os.path.isdir(run_dir):
        print(f"ERROR: Directory not found: {run_dir}")
        sys.exit(1)

    print(f"Initializing database...")
    store.init_db()

    print(f"Seeding CoreStack-native policies...")
    seed_corestack.seed()

    print(f"Ingesting custodian run from: {run_dir}")
    result = ingest.ingest_run(run_dir)

    print(f"\nIngestion complete:")
    print(f"  Run ID:     {result['run_id']}")
    print(f"  Policies:   {result['policies_ingested']}")
    print(f"  Findings:   {result['findings_ingested']}")
    print(f"  Resources:  {result['resources_ingested']}")


if __name__ == "__main__":
    main()
