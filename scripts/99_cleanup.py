#!/usr/bin/env python3
"""Clean up all AWS resources created by this POC."""

import sys
import time
import boto3
from botocore.exceptions import ClientError
from common import load_state, save_state


def delete_s3_bucket(s3, bucket_name):
    """Remove public access, delete all objects, then delete the bucket."""
    print(f"Cleaning up S3 bucket: {bucket_name}")

    try:
        # 1. Block public access first
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        print("  Public access blocked.")
    except ClientError:
        pass

    try:
        # 2. Remove bucket policy
        s3.delete_bucket_policy(Bucket=bucket_name)
        print("  Bucket policy removed.")
    except ClientError:
        pass

    try:
        # 3. Delete all objects (should be empty, but just in case)
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name):
            if "Contents" in page:
                objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                s3.delete_objects(Bucket=bucket_name, Delete={"Objects": objects})
                print(f"  Deleted {len(objects)} objects.")

        # 4. Delete all object versions (if versioning was enabled)
        paginator = s3.get_paginator("list_object_versions")
        for page in paginator.paginate(Bucket=bucket_name):
            versions = []
            for v in page.get("Versions", []):
                versions.append({"Key": v["Key"], "VersionId": v["VersionId"]})
            for v in page.get("DeleteMarkers", []):
                versions.append({"Key": v["Key"], "VersionId": v["VersionId"]})
            if versions:
                s3.delete_objects(Bucket=bucket_name, Delete={"Objects": versions})
    except ClientError:
        pass

    try:
        s3.delete_bucket(Bucket=bucket_name)
        print(f"  Bucket {bucket_name} deleted.")
    except ClientError as e:
        print(f"  ERROR deleting bucket: {e}")


def terminate_ec2_instance(ec2, instance_id):
    """Terminate the EC2 instance."""
    print(f"Terminating EC2 instance: {instance_id}")
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        print(f"  Termination initiated for {instance_id}.")
        # Wait briefly for termination to begin
        waiter = ec2.get_waiter("instance_terminated")
        print("  Waiting for termination (up to 2 min)...")
        waiter.wait(InstanceIds=[instance_id], WaiterConfig={"Delay": 10, "MaxAttempts": 12})
        print(f"  Instance {instance_id} terminated.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "InvalidInstanceID.NotFound":
            print(f"  Instance {instance_id} already gone.")
        else:
            print(f"  ERROR: {e}")


def delete_ebs_volume(ec2, volume_id):
    """Delete the EBS volume."""
    print(f"Deleting EBS volume: {volume_id}")
    try:
        ec2.delete_volume(VolumeId=volume_id)
        print(f"  Volume {volume_id} deleted.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "InvalidVolume.NotFound":
            print(f"  Volume {volume_id} already gone.")
        else:
            print(f"  ERROR: {e}")


def main():
    state = load_state()
    if not state:
        print("No state.json found. Nothing to clean up.")
        sys.exit(0)

    region = state.get("region", "us-east-1")
    print(f"Region: {region}")
    print(f"Prefix: {state.get('prefix', 'unknown')}")
    print()

    s3 = boto3.client("s3", region_name=region)
    ec2 = boto3.client("ec2", region_name=region)

    # Terminate EC2 first (takes longest)
    if state.get("instance_id"):
        terminate_ec2_instance(ec2, state["instance_id"])

    # Delete EBS volume
    if state.get("volume_id"):
        delete_ebs_volume(ec2, state["volume_id"])

    # Delete S3 bucket
    if state.get("bucket_name"):
        delete_s3_bucket(s3, state["bucket_name"])

    # Clear state
    state["cleaned_up"] = True
    save_state(state)

    print()
    print("Cleanup complete. All demo resources removed.")


if __name__ == "__main__":
    main()
