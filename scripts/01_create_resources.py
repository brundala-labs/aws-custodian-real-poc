#!/usr/bin/env python3
"""Create demo AWS resources: S3 bucket, EC2 instance, EBS volume."""

import json
import sys
import time
import boto3
from botocore.exceptions import ClientError
from common import get_region, TAGS, TAGS_LIST, SAFE_MODE, PREFIX, save_state


def get_ami_from_ssm(region):
    """Get latest Amazon Linux 2023 AMI via SSM parameter (no ec2:DescribeImages needed)."""
    ssm = boto3.client("ssm", region_name=region)
    try:
        resp = ssm.get_parameter(Name="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64")
        return resp["Parameter"]["Value"]
    except ClientError:
        pass
    # Fallback: Amazon Linux 2
    try:
        resp = ssm.get_parameter(Name="/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2")
        return resp["Parameter"]["Value"]
    except ClientError:
        return None


def get_latest_amazon_linux_ami(ec2, region):
    """Get latest Amazon Linux AMI. Try SSM first, then DescribeImages."""
    ami = get_ami_from_ssm(region)
    if ami:
        return ami
    try:
        resp = ec2.describe_images(
            Owners=["amazon"],
            Filters=[
                {"Name": "name", "Values": ["al2023-ami-2023.*-x86_64"]},
                {"Name": "state", "Values": ["available"]},
                {"Name": "architecture", "Values": ["x86_64"]},
            ],
        )
        images = sorted(resp["Images"], key=lambda x: x["CreationDate"], reverse=True)
        if images:
            return images[0]["ImageId"]
    except ClientError:
        pass
    return None


def create_s3_bucket(s3, bucket_name, region):
    """Create S3 bucket with encryption, optionally public."""
    print(f"Creating S3 bucket: {bucket_name}")

    create_args = {"Bucket": bucket_name}
    if region != "us-east-1":
        create_args["CreateBucketConfiguration"] = {"LocationConstraint": region}

    s3.create_bucket(**create_args)

    # Tag the bucket
    s3.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={"TagSet": [{"Key": k, "Value": v} for k, v in TAGS.items()]},
    )

    # Enable default encryption (SSE-S3) -> policy #2 will PASS
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}, "BucketKeyEnabled": True}
            ]
        },
    )
    print("  Default encryption (AES256) enabled.")

    # Make public if not SAFE_MODE -> policy #1 will FAIL
    if not SAFE_MODE:
        # First disable the public access block so we can set a public policy
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )
        time.sleep(2)  # allow propagation

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadDemo",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                }
            ],
        }
        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        print("  Public-read bucket policy applied (demo only).")
    else:
        print("  SAFE_MODE=true: skipping public access.")

    return bucket_name


def create_ec2_instance(ec2, prefix, region):
    """Create a t3.micro instance missing the CostCenter tag so policy #3 FAILs."""
    ami_id = get_latest_amazon_linux_ami(ec2, region)
    if not ami_id:
        print("ERROR: Could not find Amazon Linux AMI.")
        sys.exit(1)

    instance_name = f"{prefix}-demo-instance"
    # Deliberately OMIT CostCenter tag so ec2-required-tags policy fails
    tags = [t for t in TAGS_LIST] + [{"Key": "Name", "Value": instance_name}]

    print(f"Creating EC2 t3.micro: {instance_name} (AMI: {ami_id})")
    # Don't specify SubnetId — AWS uses the default VPC/subnet automatically
    # This avoids needing ec2:DescribeVpcs / ec2:DescribeSubnets permissions
    resp = ec2.run_instances(
        ImageId=ami_id,
        InstanceType="t3.micro",
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{"ResourceType": "instance", "Tags": tags}],
    )
    instance_id = resp["Instances"][0]["InstanceId"]
    az = resp["Instances"][0]["Placement"]["AvailabilityZone"]
    print(f"  Instance launched: {instance_id} in {az}")
    return instance_id, az


def create_ebs_volume(ec2, prefix, az):
    """Create an encrypted but unattached EBS volume.
    - ebs-encrypted policy -> PASS (encrypted=True)
    - ebs-unused-volumes policy -> FAIL (unattached)
    """
    vol_name = f"{prefix}-demo-volume"
    tags = [t for t in TAGS_LIST] + [{"Key": "Name", "Value": vol_name}]

    print(f"Creating encrypted EBS volume: {vol_name} in {az}")
    resp = ec2.create_volume(
        AvailabilityZone=az,
        Size=1,  # 1 GiB - minimal
        VolumeType="gp3",
        Encrypted=True,
        TagSpecifications=[{"ResourceType": "volume", "Tags": tags}],
    )
    volume_id = resp["VolumeId"]
    print(f"  Volume created: {volume_id}")
    return volume_id


def main():
    region = get_region()
    prefix = PREFIX

    print(f"Prefix: {prefix}")
    print(f"Region: {region}")
    print(f"SAFE_MODE: {SAFE_MODE}")
    print()

    s3 = boto3.client("s3", region_name=region)
    ec2 = boto3.client("ec2", region_name=region)

    bucket_name = f"{prefix}-public-bucket"
    bucket = create_s3_bucket(s3, bucket_name, region)

    instance_id, az = create_ec2_instance(ec2, prefix, region)
    volume_id = create_ebs_volume(ec2, prefix, az)

    state = {
        "prefix": prefix,
        "region": region,
        "safe_mode": SAFE_MODE,
        "bucket_name": bucket,
        "instance_id": instance_id,
        "volume_id": volume_id,
        "availability_zone": az,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    save_state(state)

    print()
    print("All resources created successfully.")
    print(f"  S3 Bucket:    {bucket}")
    print(f"  EC2 Instance: {instance_id}")
    print(f"  EBS Volume:   {volume_id}")


if __name__ == "__main__":
    main()
