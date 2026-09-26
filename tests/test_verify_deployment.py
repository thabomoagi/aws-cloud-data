import boto3
import pytest
from moto import mock_aws

from scripts.verify_deployment import REGION, VPC_NAME, find_subnets, find_vpc, main


@pytest.fixture
def ec2():
    with mock_aws():
        yield boto3.client("ec2", region_name=REGION)


def _create_vpc(ec2, cidr: str) -> str:
    return ec2.create_vpc(CidrBlock=cidr)["Vpc"]["VpcId"]


def _create_subnet(ec2, vpc_id: str, cidr: str, name: str) -> str:
    subnet_id = ec2.create_subnet(
        VpcId=vpc_id,
        CidrBlock=cidr,
        AvailabilityZone=f"{REGION}a",
    )["Subnet"]["SubnetId"]
    ec2.create_tags(Resources=[subnet_id], Tags=[{"Key": "Name", "Value": name}])

    return subnet_id


def test_find_vpc_returns_the_vpc_with_the_name_tag(ec2):
    vpc_id = _create_vpc(ec2, "10.0.0.0/16")
    ec2.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": VPC_NAME}])

    vpc = find_vpc(ec2)

    assert vpc is not None
    assert vpc["VpcId"] == vpc_id
    assert vpc["CidrBlock"] == "10.0.0.0/16"


def test_find_vpc_ignores_vpcs_without_the_name_tag(ec2):
    _create_vpc(ec2, "10.7.0.0/16")

    assert find_vpc(ec2) is None


def test_find_subnets_returns_only_subnets_of_that_vpc(ec2):
    vpc_id = _create_vpc(ec2, "10.0.0.0/16")
    public_subnet = _create_subnet(ec2, vpc_id, "10.0.1.0/24", "dev-public")
    private_subnet = _create_subnet(ec2, vpc_id, "10.0.2.0/24", "dev-private")
    other_vpc_id = _create_vpc(ec2, "10.9.0.0/16")
    _create_subnet(ec2, other_vpc_id, "10.9.1.0/24", "other-public")

    subnets = find_subnets(ec2, vpc_id)

    assert {subnet["SubnetId"] for subnet in subnets} == {public_subnet, private_subnet}
    assert {subnet["CidrBlock"] for subnet in subnets} == {"10.0.1.0/24", "10.0.2.0/24"}


@mock_aws
def test_main_reports_a_missing_deployment(capsys):
    main()

    assert "No VPC found" in capsys.readouterr().out
