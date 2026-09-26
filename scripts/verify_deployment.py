import boto3

# Matches the Name tag that terraform/modules/vpc puts on the VPC.
VPC_NAME = "dev-vpc"
REGION = "af-south-1"


def find_vpc(ec2) -> dict | None:
    response = ec2.describe_vpcs(
        Filters=[{"Name": "tag:Name", "Values": [VPC_NAME]}]
    )
    vpcs = response["Vpcs"]

    return vpcs[0] if vpcs else None


def find_subnets(ec2, vpc_id: str) -> list[dict]:
    response = ec2.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )

    return response["Subnets"]


def main() -> None:
    ec2 = boto3.client("ec2", region_name=REGION)

    print(f"Checking for VPC named '{VPC_NAME}'...\n")

    vpc = find_vpc(ec2)

    if vpc is None:
        print("No VPC found. Deployment may have failed or not been applied yet.")
        return

    vpc_id = vpc["VpcId"]
    print(f"VPC found: {vpc_id}")
    print(f"CIDR block: {vpc['CidrBlock']}")
    print(f"State: {vpc['State']}\n")

    subnets = find_subnets(ec2, vpc_id)
    print(f"Found {len(subnets)} subnet(s) in this VPC:\n")

    for subnet in subnets:
        name_tag = "No Name tag"
        for tag in subnet.get("Tags", []):
            if tag["Key"] == "Name":
                name_tag = tag["Value"]

        print(f"- {name_tag} | {subnet['CidrBlock']} | AZ: {subnet['AvailabilityZone']}")


if __name__ == "__main__":
    main()