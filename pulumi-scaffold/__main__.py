import pulumi
import pulumi_aws as aws

#Create a new VPC that will house the private and public subnets
strongdm_vpc = aws.ec2.Vpc("strongdm_vpc",
    assign_generated_ipv6_cidr_block=False,
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    instance_tenancy="default",
    tags={
        "Name": "Strongdm VPC",
        "application": "pulumi-strongdm1",
})

#tabletodelete = aws.ec2.get_route_tables(vpc_id=strongdm_vpc)
#pulumi.export("TabletoDelete", tabletodelete)

#Create an IGW and attach it to the created VPC
strongdm_gw = aws.ec2.InternetGateway("strongdm-gw",
    vpc_id=strongdm_vpc.id,
    tags={
        "Name": "strongdm-vpc",
        "application": "pulumi-strongdm1",
})

#Create a public subnet 1
strongdm_public_subnet1 = aws.ec2.Subnet("strongdm_public_subnet1",
    assign_ipv6_address_on_creation=False,
    cidr_block="10.0.5.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=False,
    tags={
        "Name": "Strongdm Public Sub1",
        "application": "pulumi-strongdm1",
    },
    vpc_id=strongdm_vpc.id)

#Create a public subnet 2
strongdm_public_subnet2 = aws.ec2.Subnet("strongdm_public_subnet2",
    assign_ipv6_address_on_creation=False,
    cidr_block="10.0.6.0/24",
    availability_zone="us-east-1b",
    map_public_ip_on_launch=False,
    tags={
        "Name": "Strongdm Public Sub2",
        "application": "pulumi-strongdm1",
    },
    vpc_id=strongdm_vpc.id)

#Create a private subnet 1
strongdm_private_subnet1 = aws.ec2.Subnet("strongdm_private_subnet1",
    assign_ipv6_address_on_creation=False,
    cidr_block="10.0.7.0/24",
    map_public_ip_on_launch=False,
    availability_zone="us-east-1a",
    tags={ 
        "Name": "Strongdm Private Sub1",
        "application": "pulumi-strongdm1",
    },
    vpc_id=strongdm_vpc.id)

#Create a private subnet 2
strongdm_private_subnet2 = aws.ec2.Subnet("strongdm_private_subnet2",
    assign_ipv6_address_on_creation=False,
    cidr_block="10.0.8.0/24",
    map_public_ip_on_launch=False,
    availability_zone="us-east-1b",
    tags={ 
        "Name": "Strongdm Private Sub2",
        "application": "pulumi-strongdm1",
    },
    vpc_id=strongdm_vpc.id)

#Create a public route table
strongdm_pub_route_table = aws.ec2.RouteTable("strongdm_pub_route", 
    vpc_id=strongdm_vpc.id,
    tags={ 
        "Name": "Strongdm Public RTB",
        "application": "pulumi-strongdm1",
    })

#Associate the public subnet1 with the public route table
strongdm_route_table_asso1 = aws.ec2.RouteTableAssociation("strongdm_route_table_asso1",
    subnet_id=strongdm_public_subnet1.id,
    route_table_id=strongdm_pub_route_table.id)

#Associate the public subnet2 with the public route table
strongdm_route_table_asso2 = aws.ec2.RouteTableAssociation("strongdm_route_table_asso2",
    subnet_id=strongdm_public_subnet2.id,
    route_table_id=strongdm_pub_route_table.id)

#Create a private route table
strongdm_priv_route_table = aws.ec2.RouteTable("strongdm_priv_route_table", 
    vpc_id=strongdm_vpc.id,
    tags={ 
        "Name": "Strongdm Private RTB",
        "application": "pulumi-strongdm1",
    })
#Associate the private subnet 2 with the private route table1
strongdm_route_table_asso_priv1 = aws.ec2.RouteTableAssociation("strongdm_route_table_asso_priv1",
    subnet_id=strongdm_private_subnet1.id,
    route_table_id=strongdm_priv_route_table.id)

#Associate the private subnet 2 with the private route table2
strongdm_route_table_asso_priv2 = aws.ec2.RouteTableAssociation("strongdm_route_table_asso_priv2",
    subnet_id=strongdm_private_subnet2.id,
    route_table_id=strongdm_priv_route_table.id)

#Add the IGW route to the public route table
strongdm_igw_route = aws.ec2.Route("strongdm_igw_route",
    destination_cidr_block="0.0.0.0/0",
    gateway_id=strongdm_gw.id,
    route_table_id=strongdm_pub_route_table)

#Create EIP for the nat gateway
strongdm_eip = aws.ec2.Eip("strongdm_eip", tags={
    "Name": "Strongdm EIP",
    "application": "pulumi-strongdm1",
})

#Create the public nat gateway in the public subnet
strongdm_nat = aws.ec2.NatGateway("strongdm_nat",
    allocation_id=strongdm_eip.id,
    connectivity_type="public",
    subnet_id=strongdm_public_subnet1.id,
    tags={
        "Name": "Strongdm NATGW",
        "application": "pulumi-strongdm1",
})

#Add the nat gateway route to the private route table
strongdm_nat_route = aws.ec2.Route("strongdm_nat_route",
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id=strongdm_nat.id,
    route_table_id=strongdm_priv_route_table.id)

strongdm_nlb = aws.lb.LoadBalancer("strongdm-nlb",
    internal=False,
    drop_invalid_header_fields=False,
    enable_cross_zone_load_balancing=True,
    enable_deletion_protection=False,
    enable_http2=True,
    idle_timeout=60,
    load_balancer_type="network",
    name="strongdm-nlb",
    tags={
        "Name": "Strongdm NLB",
        "application": "pulumi-strongdm1",
    },
    subnet_mappings=[
    aws.lb.LoadBalancerSubnetMappingArgs(
        subnet_id=strongdm_public_subnet1.id,
    ),
    aws.lb.LoadBalancerSubnetMappingArgs(
        subnet_id=strongdm_public_subnet2.id,
    ),
])

pulumi.export("PubRTB", strongdm_pub_route_table.id)
pulumi.export("Nat", strongdm_nat.id)
pulumi.export("VPC", strongdm_vpc.id)
pulumi.export("Pubsub1", strongdm_public_subnet1.id)
pulumi.export("Pubsub2", strongdm_public_subnet2.id)
pulumi.export("Privsub1", strongdm_private_subnet1.id)
pulumi.export("Privsub2", strongdm_private_subnet2.id)
pulumi.export("NLB", strongdm_nlb.dns_name)
pulumi.export("NLBID", strongdm_nlb.id)