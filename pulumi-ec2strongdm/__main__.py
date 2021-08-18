import pulumi
import pulumi_aws as aws
from pulumi import StackReference
import os
import strongdm

##Remember, if the Strongdm server config is there you will not get a key
##You need to run this pulumi without a preview

firststack = StackReference(f"smpnet74/pulumi-scaffold/dev")

create_ssh = ""

api_access_key = os.getenv("SDM_API_ACCESS_KEY")
api_secret_key = os.getenv("SDM_API_SECRET_KEY")
client = strongdm.Client(api_access_key, api_secret_key)

ssh_server = strongdm.SSH(
    name="sshserver1234",
    hostname="test",
    username="ec2-user",
    port=22
)

servers = client.resources.list('')
for server in servers:
    if server.name == ssh_server.name:
        create_ssh = "foundssh"

if not create_ssh == "foundssh":
    response = client.resources.create(ssh_server, timeout=30)
 #   print("Successfully created SSH server.")
 #   print("\tName:", response.resource.name)
 #   print("\tID:", response.resource.id)
 #   print("\tPublic Key:", response.resource.public_key)


strongdm_ec2_sg = aws.ec2.SecurityGroup("strongdm_ec2_sg",
    description="2021-07-22T20:10:24.450Z",
    name="strongdm-secgroup2",
    vpc_id=firststack.get_output("VPC"),
    ingress=[aws.ec2.SecurityGroupIngressArgs(
        description="Allow Port 80",
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
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
        "Name": "Strongdm ec2 service security group",
        "application": "pulumi-strongdm1",
})

# Create an EC2 server that we'll then provision stuff onto.
# It seems that the VPC SG id needs to be in the same private sub as the LB subnet groups

key = aws.ec2.KeyPair('key', public_key=response.resource.public_key)
server = aws.ec2.Instance('server',
    instance_type='t3.medium',
    ami="ami-0dc2d3e4c0f9ebd18",
    key_name=key.key_name,
    subnet_id=firststack.get_output("Privsub2"),
    vpc_security_group_ids=[ strongdm_ec2_sg.id ],
)

#This code takes the private IP of the EC2 instance, along with the StrongDM ssh_server.name and pass them into the function
#The function loads the strongdm client and searches all the resources for a resource name that equals the ssh server name
#Once it finds it, it sets the strongdm found server hostname for the private IP address

server.private_ip.apply(lambda value: set_sship(value, ssh_server.name))

def set_sship(IP, SSHNAME):

    api_access_key = os.getenv("SDM_API_ACCESS_KEY")
    api_secret_key = os.getenv("SDM_API_SECRET_KEY")
    client = strongdm.Client(api_access_key, api_secret_key)
    
    # Load the datasource to update
    server_list = client.resources.list('')
    for server in server_list:
        if server.name == SSHNAME:
            server.hostname = IP
            update_response = client.resources.update(server, timeout=30)
