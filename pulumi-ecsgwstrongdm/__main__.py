from typing import Protocol
import pulumi
import pulumi_aws as aws
from pulumi import StackReference
import os
import strongdm

gwname = "example-gateway0093412"
####The task defination number of the service has to be correct
####It increments even after you have deleted the task if the name is the same

firststack = StackReference(f"smpnet74/pulumi-scaffold/dev")

tokenreturn = firststack.get_output("NLB").apply(lambda value: create_sd_gw(value, gwname))

def create_sd_gw(url, gwname):
    api_access_key = os.getenv("SDM_API_ACCESS_KEY")
    api_secret_key = os.getenv("SDM_API_SECRET_KEY")
    client = strongdm.Client(api_access_key, api_secret_key)
    gateway = strongdm.Gateway(
        name=gwname,
        listen_address=f"{url}:5000",
    )

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

strongdm_ecs_task_execution_role = aws.iam.Role("strongdm_ecs_task_execution_role",
    assume_role_policy="{\"Version\":\"2008-10-17\",\"Statement\":[{\"Sid\":\"\",\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"ecs-tasks.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}",
    force_detach_policies=False,
    max_session_duration=3600,
    name="strongdm_ecs_task_execution_role",
    path="/",
    tags={
        "Name": "Strongdm ECS execution role",
        "application": "pulumi-strongdm1",
})
strongdm_ecstask = aws.ecs.TaskDefinition("strongdm_ecstask",
    container_definitions="[{\"cpu\":0,\"environment\":[{\"name\":\"SDM_RELAY_TOKEN\",\"value\":\"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjAsIm9yZ2FuaXphdGlvbklkIjoxNTU0LCJzdXBlcmFkbWluIjpmYWxzZSwiZW1haWwiOiJyZWxheXNAc3Ryb25nZG0uY29tIiwicm9sZSI6InJlbGF5IiwidGZhRW5hYmxlZCI6ZmFsc2UsIm5vZGVJZCI6IjYzMjZiZTE0LTBkNmUtNGU1Yi1iODZlLThiMWQ5MTQ3MzY2MSIsImF1dGhJZCI6IiIsIm1vZGUiOiIiLCJvcGVyYXRvciI6ZmFsc2V9.SjEeVR2Bcx1rIWvlFAbrzyVrWYM5H-F-OxSDvFbtqxw\"}],\"essential\":true,\"image\":\"quay.io/sdmrepo/relay\",\"logConfiguration\":{\"logDriver\":\"awslogs\",\"options\":{\"awslogs-group\":\"/ecs/strongdm_ecs_task\",\"awslogs-region\":\"us-east-1\",\"awslogs-stream-prefix\":\"ecs\"}},\"memoryReservation\":1024,\"mountPoints\":[],\"name\":\"strongdm_gw_container\",\"portMappings\":[{\"containerPort\":5000,\"hostPort\":5000,\"protocol\":\"tcp\"}],\"volumesFrom\":[]}]",
    cpu="512",
    family="strongdm_ecs_task",
    memory="1024",
    network_mode="awsvpc",
    execution_role_arn=strongdm_ecs_task_execution_role.arn,
    requires_compatibilities=["FARGATE"])

#Must create this log group otherwise the ECS task will never start.
strongdm_ecs_loggroup = aws.cloudwatch.LogGroup("strongdm_ecs_loggroup",
    name="/ecs/strongdm_ecs_task",
    retention_in_days=0)

strongdm_frontend = aws.lb.TargetGroup("strongdm-frontend",
    deregistration_delay=300,
    lambda_multi_value_headers_enabled=False,
    name="strongdm-target-group",
    port=5000,
    protocol="TCP",
    proxy_protocol_v2=False,
    slow_start=0,
    target_type="ip",
    vpc_id=firststack.get_output("VPC"),
    tags={
        "Name": "Strongdm Targetgroup",
        "application": "pulumi-strongdm1",
})

strongdm_listner = aws.lb.Listener("strongdm_listner",
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        order=1,
        target_group_arn=strongdm_frontend.id,
        type="forward",
    )],
    load_balancer_arn=firststack.get_output("NLBID"),
    protocol="TCP",
    port=5000,
    tags={
        "Name": "Strongdm Listner",
        "application": "pulumi-strongdm1",
})

strongdm_policy = aws.iam.Policy("strongdm_policy",
    description="Cloudwatch Full",
    tags={
        "Name": "Strongdm Task Policy",
        "application": "pulumi-strongdm1",
},
    policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:*"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
""")

strongdm_policy_attach = aws.iam.RolePolicyAttachment("strongdm_policy_attach",
    role=strongdm_ecs_task_execution_role.id,
    policy_arn=strongdm_policy.arn)

strongdm_ecs1 = aws.ecs.Cluster("strongdm-ecscluster",
    capacity_providers=[
        None,
        "FARGATE",
    ],
    name="strongdm-ecscluster1",
    tags={
        "Name": "Strongdm ECS Cluster",
        "application": "pulumi-strongdm1",
})

strongdm_sg = aws.ec2.SecurityGroup("strongdm_sg",
    description="2021-07-22T20:10:24.450Z",
    name="strongdm-secgroup1",
    vpc_id=firststack.get_output("VPC"),
    ingress=[aws.ec2.SecurityGroupIngressArgs(
        description="Allow Port 80",
        from_port=5000,
        to_port=5000,
        protocol="TCP",
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
        "Name": "Strongdm service security group",
        "application": "pulumi-strongdm1",
})

strongdm_service = aws.ecs.Service("strongdm-service",
    cluster=strongdm_ecs1.id,
    launch_type="FARGATE",
    deployment_maximum_percent=100,
    deployment_minimum_healthy_percent=0,
    desired_count=1,
    enable_ecs_managed_tags=True,
    enable_execute_command=False,
    health_check_grace_period_seconds=600,
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
        container_name="strongdm_gw_container",
        container_port=5000,
        target_group_arn=strongdm_frontend.arn,
    )],
    name="strongdm-service1",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        security_groups=[strongdm_sg.id],
        subnets=[firststack.get_output("Privsub1"),
        firststack.get_output("Privsub2")],
    ),
    scheduling_strategy="REPLICA",
    task_definition="strongdm_ecs_task:1",
    tags={
        "Name": "Strongdm service",
        "application": "pulumi-strongdm1",
})
#^^^^ The task definition must be incremented otherwise it will point to a inactive task