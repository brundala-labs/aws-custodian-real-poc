"""Shared utilities for the Cloud Custodian POC scripts."""

import json
import os
import time

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "state.json")
POLICIES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policies")
OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")

PREFIX = f"cscc-poc-{int(time.time())}"

TAGS = {
    "Demo": "CoreStackCustodianPOC",
    "Owner": "AgenticBricks",
    "CreatedBy": "claude",
    "TTLHours": "24",
}

TAGS_LIST = [{"Key": k, "Value": v} for k, v in TAGS.items()]

DEFAULT_REGION = "us-east-1"

SAFE_MODE = os.environ.get("SAFE_MODE", "false").lower() == "true"


def get_region():
    return os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", DEFAULT_REGION))


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"State saved to {STATE_FILE}")


def get_prefix(state=None):
    """Return the prefix, loading from state if available."""
    if state and "prefix" in state:
        return state["prefix"]
    return PREFIX
