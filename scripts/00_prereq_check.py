#!/usr/bin/env python3
"""Check AWS identity, region, and basic permissions before running the POC."""

import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from common import get_region, SAFE_MODE


def main():
    region = get_region()
    print(f"Region:    {region}")
    print(f"SAFE_MODE: {SAFE_MODE}")
    print()

    # 1. Check credentials
    try:
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Export AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or configure a profile.")
        sys.exit(1)
    except ClientError as e:
        print(f"ERROR: STS call failed: {e}")
        sys.exit(1)

    print(f"Account:   {identity['Account']}")
    print(f"ARN:       {identity['Arn']}")
    print(f"User ID:   {identity['UserId']}")
    print()

    # 2. Check basic service access
    checks = {
        "S3":  lambda: boto3.client("s3", region_name=region).list_buckets(),
        "EC2": lambda: boto3.client("ec2", region_name=region).describe_vpcs(MaxResults=5),
    }

    all_ok = True
    for svc, fn in checks.items():
        try:
            fn()
            print(f"  {svc}: OK")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("AccessDenied", "UnauthorizedAccess"):
                print(f"  {svc}: ACCESS DENIED - check IAM permissions")
                all_ok = False
            else:
                print(f"  {svc}: OK (non-auth error ignored: {code})")
        except Exception as e:
            print(f"  {svc}: UNKNOWN ERROR - {e}")
            all_ok = False

    print()
    if all_ok:
        print("All prerequisite checks passed.")
    else:
        print("Some checks failed. Fix permissions before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
