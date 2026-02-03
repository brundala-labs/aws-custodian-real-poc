# CoreStack Integration Mock – Unified Policy Compliance Dashboard

Mock CoreStack integration that ingests **real Cloud Custodian outputs** and presents them alongside seeded CoreStack-native policies in a unified compliance dashboard.

## Architecture

```
Cloud Custodian Outputs ──> Ingestion ──> SQLite ──> FastAPI REST API
                                                         │
                                              Streamlit Dashboard
```

## What's Included

| Component | Purpose |
|---|---|
| `integration/ingest.py` | Reads custodian `manifest.json` + `resources.json` per policy |
| `integration/normalize.py` | Maps custodian output to CoreStack compliance model |
| `integration/store.py` | SQLite schema (policies, runs, findings, resources, evidence) |
| `integration/seed_corestack.py` | Seeds 3 fake CoreStack-native policies for unified demo |
| `integration/app.py` | FastAPI with endpoints: `/ingest`, `/summary`, `/findings`, `/policies` |
| `ui/streamlit_app.py` | Dashboard with KPIs, filters, drill-down, evidence viewer |

## Seeded CoreStack Policies (Fake)

| Policy | Severity | Status |
|---|---|---|
| IAM MFA Enabled for Console Users | high | FAIL (2 violations) |
| Monthly Budget Alert Configured | medium | PASS |
| CloudTrail Logging Enabled | high | FAIL (1 violation) |

Combined with 5 real Cloud Custodian policies = **8 total policies** in the unified view.

## Prerequisites

- Python 3.9+
- Cloud Custodian run outputs from `aws-custodian-real-poc/outputs/<run_id>/`

## Quick Start

```bash
cd corestack-integration-mock

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Point to your custodian run outputs
export CUSTODIAN_RUN_DIR=/path/to/aws-custodian-real-poc/outputs/run-1770090475

# Option A: One-shot ingest (no server needed)
python scripts/ingest_once.py

# Option B: Start API server (auto-ingests on startup)
bash scripts/run_api.sh
# In another terminal:
bash scripts/run_ui.sh
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/ingest?path=...` | Ingest custodian run from local path |
| GET | `/summary` | KPIs: total, passing, failing, last evaluated |
| GET | `/findings?source=&status=&severity=` | Filtered findings list |
| GET | `/policies` | All policies |
| GET | `/policies/{id}` | Single policy detail |
| GET | `/policies/{id}/resources` | Violating resources for a policy |
| GET | `/policies/{id}/evidence` | Raw evidence JSON |

API docs: http://localhost:8080/docs

## Dashboard Features

- **KPI Cards**: Total Policies, Passing, Failing, Last Evaluated
- **Filters**: Source (All/Cloud Custodian/CoreStack), Status, Severity
- **Findings Table**: Policy name, source badge, status, violations, category, resource type
- **Drill-Down**: Select a policy to view violating resources and raw evidence JSON
- **Re-Ingest Button**: Re-load custodian outputs without restarting

## 10-Minute Seller Demo Script

### 1. Show Real Custodian Outputs (1 min)
```bash
ls ../outputs/run-*/
cat ../outputs/run-*/manifest.json
```
"These are real Cloud Custodian scan results from a live AWS account."

### 2. Start the Platform (1 min)
```bash
# Terminal 1
export CUSTODIAN_RUN_DIR=../outputs/run-1770090475
bash scripts/run_api.sh

# Terminal 2
bash scripts/run_ui.sh
```

### 3. Show Unified Dashboard (3 min)
Open http://localhost:8501
- Point out KPI cards: "8 total policies, X passing, Y failing"
- "Notice both Cloud Custodian and CoreStack policies in one view"
- Filter by Source = "cloudcustodian" → "These came from real AWS scans"
- Filter by Source = "corestack" → "These are CoreStack-native governance policies"

### 4. Drill Into a Failing Policy (3 min)
- Select "s3-public-bucket" from drill-down
- Show violating resource: the actual S3 bucket name and ARN
- Expand "Raw Evidence JSON" → "This is the exact AWS API response Cloud Custodian captured"
- "You can see the bucket policy with Principal: * — a real security finding"

### 5. Show Severity Filtering (2 min)
- Filter by Severity = "high" → "Focus on critical issues first"
- "CoreStack normalizes findings from multiple tools into one severity model"
- Click Re-Ingest → "As new scans run, the dashboard updates in real time"

## Project Structure

```
corestack-integration-mock/
├── README.md
├── requirements.txt
├── corestack.db            (auto-generated)
├── integration/
│   ├── app.py              (FastAPI server)
│   ├── ingest.py           (custodian output reader)
│   ├── models.py           (Pydantic schemas)
│   ├── normalize.py        (normalization rules)
│   ├── seed_corestack.py   (fake native policies)
│   └── store.py            (SQLite CRUD)
├── ui/
│   └── streamlit_app.py    (dashboard)
└── scripts/
    ├── ingest_once.py      (CLI ingestion)
    ├── run_api.sh          (start API)
    └── run_ui.sh           (start UI)
```
