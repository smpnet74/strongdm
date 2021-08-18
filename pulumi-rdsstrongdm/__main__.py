import pulumi
import pulumi_aws as aws
from pulumi import StackReference
import os
import strongdm

firststack = StackReference(f"smpnet74/pulumi-scaffold/dev")

strongdm_rds_subgroup = aws.rds.SubnetGroup("strongdm_rds_subgroup",
    subnet_ids=[
        firststack.get_output("Privsub1"),
        firststack.get_output("Privsub2")
    ],
    tags={
        "Name": "Strongdm rds subgroup",
        "application": "pulumi-strongdm1",
})

strongdm_rds_sg = aws.ec2.SecurityGroup("strongdm_rds_sg",
    description="2021-07-22T20:10:24.450Z",
    name="strongdm_rds_sg",
    vpc_id=firststack.get_output("VPC"),
    ingress=[aws.ec2.SecurityGroupIngressArgs(
        description="Allow Port 5432",
        from_port=5432,
        to_port=5432,
        protocol="TCP",
        cidr_blocks=["10.0.0.0/16"],
        ipv6_cidr_blocks=["::/0"],
    )],
    egress=[aws.ec2.SecurityGroupEgressArgs(
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
        ipv6_cidr_blocks=["::/0"],
    )],
    revoke_rules_on_delete=False,
    tags={
        "Name": "Strongdm rds security group",
        "application": "pulumi-strongdm1",
})

strongdm_rds_postgres = aws.rds.Instance("strongdm_rds_postgres",
    db_subnet_group_name=strongdm_rds_subgroup.id,
    vpc_security_group_ids=[strongdm_rds_sg.id],
    multi_az=False,
    auto_minor_version_upgrade=True,
    copy_tags_to_snapshot=True,
    delete_automated_backups=True,
    identifier="strongdm-db1",
    instance_class="db.t3.medium",
    allocated_storage=20,
    max_allocated_storage=1000,
    monitoring_interval=0,
    engine="postgres",
    engine_version="13.3",
    username=pg_username,
    password=pg_password,
    performance_insights_enabled=True,
    publicly_accessible=False,
    skip_final_snapshot=True,
    storage_encrypted=True,
    tags={
        "Name": "Strongdm test postgres DB",
        "application": "pulumi-strongdm1",
})

pg_username = "postgres"
pg_password = "postgres"
db_name = "postgres"

create_rds = ""

tokenreturn = strongdm_rds_postgres.hostname.apply(lambda value: create_rds(value, pg_username, pg_password, db_name))

def create_sd_gw(hostname, username, passowrd, dbname,):
    api_access_key = os.getenv("SDM_API_ACCESS_KEY")
    api_secret_key = os.getenv("SDM_API_SECRET_KEY")
    client = strongdm.Client(api_access_key, api_secret_key)
    
    rdsserver = strongdm.resource(
        name=gwname,
        listen_address=f"{url}:5000",
    )
'''
    create_gateway = ""
    
    nodes = client.nodes.list('')
    for node in nodes:
        if node.name == gateway.name:
            create_gateway = "foundgateway"
    
    if not create_gateway == "foundgateway":
        node_response = client.nodes.create(gateway, timeout=30)
        print("Successfully created gateway.")
        print("\tID:", node_response.node.id)
        print("\tToken:", node_response.token)
'''









api_access_key = os.getenv("SDM_API_ACCESS_KEY")
api_secret_key = os.getenv("SDM_API_SECRET_KEY")
client = strongdm.Client(api_access_key, api_secret_key)

rds_server = strongdm.resources(
    name=db_name,
    hostname="test",
    port=22
)

rdss = client.resources.list('')
for rds in rdss:
    if rds.name == db_name.name:
        create_ssh = "foundssh"

if not create_ssh == "foundssh":
    response = client.resources.create(ssh_server, timeout=30)
 #   print("Successfully created SSH server.")
 #   print("\tName:", response.resource.name)
 #   print("\tID:", response.resource.id)
 #   print("\tPublic Key:", response.resource.public_key)