# Cloud Custodian POC — Project Document

**Project**: AWS Cloud Custodian Real POC
**Date**: February 2, 2026
**AWS Account**: 864387741092 (corestackpocuser)
**Region**: us-east-1
**Run ID**: run-1770090475

---

## 1. Objective

Build an end-to-end AWS demo environment for Cloud Custodian where some policies **FAIL** and some **PASS** after execution, demonstrating real policy-as-code compliance scanning against live AWS resources.

---

## 2. Step-by-Step Execution Log

### Step 1: Project Scaffolding

Created the project directory structure:

```
aws-custodian-real-poc/
├── README.md
├── requirements.txt
├── scripts/
│   ├── __init__.py
│   ├── common.py
│   ├── 00_prereq_check.py
│   ├── 01_create_resources.py
│   ├── 02_generate_policies.py
│   ├── 03_run_custodian.py
│   ├── 04_summarize_results.py
│   └── 99_cleanup.py
├── policies/           (auto-generated)
├── outputs/            (auto-generated)
└── state.json          (auto-generated)
```

**Dependencies** (`requirements.txt`):
- `boto3>=1.28.0` — AWS SDK
- `c7n>=0.9.30` — Cloud Custodian
- `tabulate>=0.9.0` — Summary table formatting

---

### Step 2: First AWS Account Attempt (devnivian — Account 799139198202)

**Credentials used**: IAM user `devnivian`

**What happened**:
1. Ran prerequisite check — STS identity confirmed, S3 access OK
2. Created S3 bucket `cscc-poc-1770086089-public-bucket` successfully with:
   - AES256 default encryption
   - Public-read bucket policy (Principal: *)
3. EC2 instance creation **failed** — user lacked `ec2:DescribeVpcs` permission
4. Investigation revealed `devnivian` only had:
   - `AmazonS3FullAccess`
   - `IAMFullAccess`
   - `IAMUserChangePassword`
   - **No EC2 permissions at all**

**Remediation**:
- Updated `01_create_resources.py` to skip VPC/subnet lookup (let AWS use defaults)
- Added SSM parameter fallback for AMI lookup
- Still failed — `ec2:RunInstances`, `ec2:CreateVolume`, `ssm:GetParameter`, `ec2:DescribeImages` all denied

**Decision**: Switch to a different AWS account with proper permissions.

---

### Step 3: Cleanup of devnivian Account

Before switching accounts, cleaned up all resources:

1. **Deleted POC bucket**: `cscc-poc-1770086089-public-bucket`
2. **Deleted 7 pre-existing S3 buckets** (per user request):
   - `geisinger-cardiology-bronze-96qclt` (13 objects)
   - `geisinger-cardiology-databricks-root-96qclt` (empty)
   - `geisinger-cardiology-delta-96qclt` (164 objects)
   - `geisinger-cardiology-scripts-96qclt` (empty)
   - `geisinger-demo-rajesh-bronze` (13 objects + 27 versions)
   - `geisinger-demo-rajesh-delta` (empty)
   - `geisinger-demo-rajesh-scripts` (5 objects + 10 versions)
3. **Deleted 3 IAM roles** (per user request):
   - `geisinger-cardiology-databricks-cross-account-role`
   - `geisinger-cardiology-databricks-instance-profile-role`
   - `geisinger-cardiology-demo-databricks-s3-role`
4. **Deleted 2 orphaned IAM policies**:
   - `geisinger-cardiology-demo-s3-access-policy`
   - `s3fullaccess`
5. **Final verification**: Account confirmed clean — 0 S3 buckets, 0 custom IAM roles, 0 custom policies, 0 instance profiles. Only the `devnivian` user remained.

---

### Step 4: New AWS Account Setup (corestackpocuser — Account 864387741092)

**Credentials provided**: IAM user `corestackpocuser`

**Initial permission check**:
- STS identity: confirmed (account 864387741092)
- S3: **DENIED**
- EC2: **DENIED**
- IAM: **DENIED** (permissions boundary in place)

**Remediation steps** (performed by user in AWS Console):
1. Attached `AmazonS3FullAccess` policy → S3 now OK
2. Attached `AmazonEC2FullAccess` policy → EC2 still denied (permissions boundary blocking)
3. Removed permissions boundary → All permissions OK

**Final permission verification**:
| Service | Permission | Status |
|---|---|---|
| S3 | ListBuckets | OK |
| EC2 | DescribeVpcs | OK |
| EC2 | RunInstances | OK |
| EC2 | CreateVolume | OK |

---

### Step 5: Prerequisite Check (00_prereq_check.py)

```
Region:    us-east-1
SAFE_MODE: False

Account:   864387741092
ARN:       arn:aws:iam::864387741092:user/corestackpocuser
User ID:   AIDA4SQMGGWSF2NONCOG5

  S3: OK
  EC2: OK

All prerequisite checks passed.
```

---

### Step 6: Resource Creation (01_create_resources.py)

**Prefix**: `cscc-poc-1770090351`

**Tags applied to all resources**:
```
Demo=CoreStackCustodianPOC
Owner=AgenticBricks
CreatedBy=claude
TTLHours=24
```

**Resources created**:

| Resource | ID | Details |
|---|---|---|
| S3 Bucket | `cscc-poc-1770090351-public-bucket` | AES256 encryption enabled, public-read bucket policy with `Principal: *` |
| EC2 Instance | `i-097633a6d9b657baf` | t3.micro, AMI ami-024ee5112d03921e2 (AL2023), us-east-1c, **deliberately missing CostCenter and Environment tags** |
| EBS Volume | `vol-0b274ce64fa2f2296` | 1 GiB gp3, encrypted=true, KMS key `8f4128dd-5833-49a7-bab0-8e8bdd7d88ea`, **unattached** |

State saved to `state.json`.

---

### Step 7: Policy Generation (02_generate_policies.py)

Generated 5 Cloud Custodian policy YAML files in `policies/`:

| # | File | Policy Name | Resource | Filter Logic | Expected Result |
|---|---|---|---|---|---|
| 1 | `s3-public-bucket.yml` | s3-public-bucket | S3 | `has-statement` with `Effect: Allow, Principal: *` | **FAIL** |
| 2 | `s3-default-encryption.yml` | s3-default-encryption-enabled | S3 | `bucket-encryption state: false` (finds unencrypted) | **PASS** |
| 3 | `ec2-required-tags.yml` | ec2-required-tags | EC2 | `tag:CostCenter: absent` OR `tag:Environment: absent` | **FAIL** |
| 4 | `ebs-unused-volumes.yml` | ebs-unused-volumes | EBS | `State: available` (unattached) | **FAIL** |
| 5 | `ebs-encrypted.yml` | ebs-encrypted | EBS | `Encrypted: false` (finds unencrypted) | **PASS** |

Also generated `expectations.json` mapping policy names to expected outcomes.

**Policy validation**: All 5 policies validated successfully with `custodian validate`.

> **Note**: Initial policy generation used dict-style tags (`{"severity": "high"}`), which Cloud Custodian rejected. Fixed to array-style tags (`["severity:high"]`).

---

### Step 8: Cloud Custodian Execution (03_run_custodian.py)

**Run ID**: `run-1770090475`
**Timestamp**: 2026-02-03T03:48:03Z
**Cloud Custodian version**: 0.9.45

All 5 policies executed successfully:

```
Running policy: ebs-encrypted ... OK
Running policy: ebs-unused-volumes ... OK
Running policy: ec2-required-tags ... OK
Running policy: s3-default-encryption-enabled ... OK
Running policy: s3-public-bucket ... OK
```

**Output structure**:
```
outputs/run-1770090475/
├── manifest.json
├── ebs-encrypted/
│   ├── resources.json      (1 violation)
│   ├── metadata.json
│   └── custodian-run.log
├── ebs-unused-volumes/
│   ├── resources.json      (1 violation)
│   ├── metadata.json
│   └── custodian-run.log
├── ec2-required-tags/
│   ├── resources.json      (1 violation)
│   ├── metadata.json
│   └── custodian-run.log
├── s3-default-encryption-enabled/
│   ├── resources.json      (0 violations)
│   ├── metadata.json
│   └── custodian-run.log
└── s3-public-bucket/
    ├── resources.json      (1 violation)
    ├── metadata.json
    └── custodian-run.log
```

---

### Step 9: Results Summary (04_summarize_results.py)

```
+-------------------------------+--------------+----------+------------+---------+
| Policy                        |   Violations | Result   | Expected   | Match   |
+===============================+==============+==========+============+=========+
| ebs-encrypted                 |            1 | FAIL     | PASS       | N       |
+-------------------------------+--------------+----------+------------+---------+
| ebs-unused-volumes            |            1 | FAIL     | FAIL       | Y       |
+-------------------------------+--------------+----------+------------+---------+
| ec2-required-tags             |            1 | FAIL     | FAIL       | Y       |
+-------------------------------+--------------+----------+------------+---------+
| s3-default-encryption-enabled |            0 | PASS     | PASS       | Y       |
+-------------------------------+--------------+----------+------------+---------+
| s3-public-bucket              |            1 | FAIL     | FAIL       | Y       |
+-------------------------------+--------------+----------+------------+---------+

Total: 1 PASS, 4 FAIL, 5 total
Validation: meets requirement (>=2 FAIL, >=1 PASS)
```

**Results**: 4 FAIL, 1 PASS — **meets the requirement** (>=2 FAIL, >=1 PASS).

**Detailed findings**:

| Policy | Violations | Violating Resource | Why |
|---|---|---|---|
| **s3-public-bucket** | 1 | `cscc-poc-1770090351-public-bucket` | Bucket policy has `Principal: *` allowing public GetObject |
| **ec2-required-tags** | 1 | `i-097633a6d9b657baf` | Missing `CostCenter` and `Environment` tags (matched via `c7n:MatchedFilters`) |
| **ebs-unused-volumes** | 1 | `vol-0b274ce64fa2f2296` | Volume `State: available` (unattached, as designed) |
| **ebs-encrypted** | 1 | `vol-0ad97b39fe3e2a5a0` | EC2 root volume (8GiB) was auto-created unencrypted by AWS — unexpected but valid finding |
| **s3-default-encryption-enabled** | 0 | — | Bucket has AES256 encryption enabled — no violations found |

> **Note on ebs-encrypted**: This policy was expected to PASS but found 1 violation. The violating volume (`vol-0ad97b39fe3e2a5a0`) was the EC2 instance's root volume, automatically created by AWS without encryption. Our intentionally created EBS volume (`vol-0b274ce64fa2f2296`) was encrypted as planned. This is a legitimate real-world finding — EC2 root volumes are unencrypted by default unless the account has EBS encryption by default enabled.

---

### Step 10: Cleanup (99_cleanup.py)

All resources deleted successfully:

```
Region: us-east-1
Prefix: cscc-poc-1770090351

Terminating EC2 instance: i-097633a6d9b657baf
  Termination initiated for i-097633a6d9b657baf.
  Waiting for termination (up to 2 min)...
  Instance i-097633a6d9b657baf terminated.
Deleting EBS volume: vol-0b274ce64fa2f2296
  Volume vol-0b274ce64fa2f2296 deleted.
Cleaning up S3 bucket: cscc-poc-1770090351-public-bucket
  Public access blocked.
  Bucket policy removed.
  Bucket cscc-poc-1770090351-public-bucket deleted.

Cleanup complete. All demo resources removed.
```

**Cleanup order**:
1. EC2 instance terminated (waited for completion)
2. EBS volume deleted
3. S3 bucket: public access blocked → policy removed → bucket deleted

---

## 3. Issues Encountered & Resolutions

| # | Issue | Resolution |
|---|---|---|
| 1 | `devnivian` user lacked EC2 permissions | Switched to `corestackpocuser` on account 864387741092 |
| 2 | `corestackpocuser` had no policies attached | User attached `AmazonS3FullAccess` + `AmazonEC2FullAccess` via Console |
| 3 | Permissions boundary blocked EC2 even after policy attachment | User removed permissions boundary via Console |
| 4 | `ec2:DescribeVpcs` not available on first account | Refactored code to skip VPC/subnet lookup, let AWS auto-assign |
| 5 | `ssm:GetParameter` and `ec2:DescribeImages` both denied | Added dual fallback: SSM → DescribeImages → fail gracefully |
| 6 | Cloud Custodian rejected dict-style `tags` in policy YAML | Fixed to array-style: `["severity:high", "owner:AgenticBricks"]` |
| 7 | Custodian `resources.json` not written (first run attempt) | Was using `python -m c7n.commands` which ran silently; switched to `custodian` CLI binary |
| 8 | Policy names in manifest didn't match output directory names | Fixed runner to read actual policy name from YAML instead of using filename |
| 9 | `ebs-encrypted` unexpectedly FAIL | EC2 root volume auto-created unencrypted — legitimate finding, not a bug |

---

## 4. Architecture & Design Decisions

### Resource Design (Intentional FAIL/PASS)

```
S3 Bucket ─────┬── Public policy (Principal:*) ──── s3-public-bucket → FAIL
               └── AES256 encryption enabled ────── s3-default-encryption → PASS

EC2 Instance ──── Missing CostCenter/Environment ── ec2-required-tags → FAIL

EBS Volume ────┬── Encrypted=true ────────────────── ebs-encrypted → PASS (for this volume)
               └── State=available (unattached) ──── ebs-unused-volumes → FAIL
```

### Tags Convention

All resources tagged with:
```
Demo=CoreStackCustodianPOC
Owner=AgenticBricks
CreatedBy=claude
TTLHours=24
```

### Naming Convention

All resource names use prefix: `cscc-poc-{unix_timestamp}-`

### State Management

`state.json` tracks all created resource IDs for deterministic cleanup. Updated after each step.

---

## 5. Cost Impact

| Resource | Duration Active | Estimated Cost |
|---|---|---|
| EC2 t3.micro | ~5 minutes | ~$0.001 |
| EBS gp3 1GiB | ~5 minutes | ~$0.00 |
| S3 empty bucket | ~5 minutes | $0.00 |
| API calls | ~50 calls | $0.00 |
| **Total** | | **< $0.01** |

All resources cleaned up. No ongoing charges.

---

## 6. Files Delivered

| File | Lines | Purpose |
|---|---|---|
| `README.md` | 124 | Setup, run, and cleanup documentation |
| `requirements.txt` | 3 | Python dependencies |
| `scripts/common.py` | 48 | Shared configuration and state management |
| `scripts/00_prereq_check.py` | 63 | AWS identity and permission validation |
| `scripts/01_create_resources.py` | 197 | S3, EC2, EBS resource creation |
| `scripts/02_generate_policies.py` | 135 | Custodian YAML policy generation |
| `scripts/03_run_custodian.py` | 94 | Custodian execution and output capture |
| `scripts/04_summarize_results.py` | 89 | Results parsing and summary table |
| `scripts/99_cleanup.py` | 134 | Safe resource deletion |
| `policies/s3-public-bucket.yml` | 13 | S3 public access detection |
| `policies/s3-default-encryption.yml` | 11 | S3 encryption verification |
| `policies/ec2-required-tags.yml` | 12 | EC2 tag compliance |
| `policies/ebs-unused-volumes.yml` | 10 | Unused EBS detection |
| `policies/ebs-encrypted.yml` | 10 | EBS encryption verification |
| `policies/expectations.json` | 7 | Expected outcomes mapping |
| `state.json` | 13 | Resource tracking (post-cleanup) |
| `outputs/run-1770090475/` | 16 files | Full Custodian execution output |

---

## 7. How to Re-Run

```bash
cd aws-custodian-real-poc
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
export AWS_DEFAULT_REGION=us-east-1

python scripts/00_prereq_check.py
python scripts/01_create_resources.py
python scripts/02_generate_policies.py
python scripts/03_run_custodian.py
python scripts/04_summarize_results.py

# When done:
python scripts/99_cleanup.py
```

Set `export SAFE_MODE=true` before running to skip making the S3 bucket public.
