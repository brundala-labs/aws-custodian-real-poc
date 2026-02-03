# AWS Cloud Custodian Real POC

End-to-end demo environment for Cloud Custodian that creates real AWS resources, runs policies against them, and produces PASS/FAIL results.

## What This Creates

| Resource | Purpose | Expected Policy Result |
|---|---|---|
| S3 bucket (public-read) | Trigger public bucket detection | **FAIL** (s3-public-bucket) |
| S3 bucket (encrypted) | Verify encryption check passes | **PASS** (s3-default-encryption-enabled) |
| EC2 t3.micro (missing tags) | Missing CostCenter/Environment tags | **FAIL** (ec2-required-tags) |
| EBS 1GiB gp3 (encrypted, unattached) | Encrypted volume passes check | **PASS** (ebs-encrypted) |
| EBS 1GiB gp3 (unattached) | Unattached volume detected | **FAIL** (ebs-unused-volumes) |

Result: **3 FAIL, 2 PASS** minimum.

## Tags Applied to All Resources

```
Demo=CoreStackCustodianPOC
Owner=AgenticBricks
CreatedBy=claude
TTLHours=24
```

## Prerequisites

- Python 3.9+
- AWS credentials configured (env vars or `~/.aws/credentials`)
- IAM permissions: S3, EC2, EBS, STS (read + write for create/delete)

## Safe Mode

Set `SAFE_MODE=true` to skip making the S3 bucket public:

```bash
export SAFE_MODE=true
```

In safe mode, the s3-public-bucket policy will PASS instead of FAIL.

## Quick Start

```bash
cd aws-custodian-real-poc

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Step 0: Check AWS credentials and permissions
python scripts/00_prereq_check.py

# Step 1: Create demo AWS resources
python scripts/01_create_resources.py

# Step 2: Generate Cloud Custodian policy YAMLs
python scripts/02_generate_policies.py

# Step 3: Run Cloud Custodian against the account
python scripts/03_run_custodian.py

# Step 4: View PASS/FAIL summary
python scripts/04_summarize_results.py

# Step 99: Clean up all resources
python scripts/99_cleanup.py
```

## Project Structure

```
aws-custodian-real-poc/
  README.md
  requirements.txt
  state.json              # Tracks created resources (auto-generated)
  scripts/
    common.py             # Shared config, tags, state helpers
    00_prereq_check.py    # AWS identity and permission check
    01_create_resources.py # Creates S3, EC2, EBS resources
    02_generate_policies.py # Writes custodian YAML policies
    03_run_custodian.py   # Executes c7n and captures output
    04_summarize_results.py # Parses results, prints summary table
    99_cleanup.py         # Deletes all created resources
  policies/               # Generated YAML files (auto-generated)
  outputs/                # Custodian run outputs (auto-generated)
```

## Policies

| Policy | Resource | Filter | Severity | Expected |
|---|---|---|---|---|
| s3-public-bucket | S3 | has-statement with Principal=* | high | FAIL |
| s3-default-encryption-enabled | S3 | bucket-encryption state=false | high | PASS |
| ec2-required-tags | EC2 | CostCenter or Environment absent | medium | FAIL |
| ebs-unused-volumes | EBS | State=available | low | FAIL |
| ebs-encrypted | EBS | Encrypted=false | high | PASS |

## Estimated Cost

- EC2 t3.micro: ~$0.01/hr (free tier eligible)
- EBS gp3 1GiB: ~$0.08/mo
- S3 empty bucket: $0.00

Run cleanup promptly to keep costs near zero.

## Cleanup

Always run cleanup when done:

```bash
python scripts/99_cleanup.py
```

The cleanup script:
1. Blocks public access on the S3 bucket
2. Removes bucket policy
3. Deletes all objects and the bucket
4. Terminates the EC2 instance (waits for completion)
5. Deletes the EBS volume
