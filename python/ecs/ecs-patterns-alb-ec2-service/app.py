from aws_cdk import (
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ecs as ecs,
    App, CfnOutput, Duration, Stack
)
import aws_cdk.aws_ecs_patterns as ecs_patterns

app = App()
stack = Stack(app, "sample-ecs-pattern-ec2-alb")

# Create a cluster
vpc = ec2.Vpc(
    stack, "MyVpc",
    max_azs=2
)

cluster = ecs.Cluster(stack, "cluster",
    vpc=vpc,
    container_insights=True
)

provider_security_group = ec2.SecurityGroup(
    stack,
    id='asg-security-group',
    vpc=vpc,
    allow_all_outbound=True,
    security_group_name='overridden-asg-security-group'
)

auto_scaling_group = autoscaling.AutoScalingGroup(
    stack, "ASG",
    vpc=vpc,
    instance_type=ec2.InstanceType("t2.medium"),
    machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
    min_capacity=0,
    max_capacity=5,
    desired_capacity=1,
    security_group=provider_security_group
)

load_balancer_security_group = ec2.SecurityGroup(
    stack,
    id='lb-sg',
    vpc=vpc,
    allow_all_outbound=True,
    security_group_name='overridden-lb-security-group'
)

load_balancer_security_group.add_ingress_rule(
    description="inbound on port 80",
    peer=ec2.Peer.any_ipv4(),
    connection=ec2.Port(
        string_representation='all inbound on 80',
        protocol=ec2.Protocol.TCP,
        from_port=80,
        to_port=80
    )
)

provider_security_group.add_ingress_rule(
    description="connectivity from LB to ASG", 
    peer=load_balancer_security_group,
    connection=ec2.Port(
        string_representation='lb-connectivity',
        protocol=ec2.Protocol.TCP,
        from_port=32768,
        to_port=65535
        )
    )

capacity_provider = ecs.AsgCapacityProvider(
    stack, 
    "AsgCapacityProvider",
    auto_scaling_group=auto_scaling_group
)

cluster.add_asg_capacity_provider(capacity_provider)

service = ecs_patterns.ApplicationLoadBalancedEc2Service(
    stack,
    id="-service",
    cluster=cluster,
    memory_limit_mib=1024,
    task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
        image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
        environment={
            "TEST_ENVIRONMENT_VARIABLE1": "test environment variable 1 value",
            "TEST_ENVIRONMENT_VARIABLE2": "test environment variable 2 value"
        }
    ),
    desired_count=1
)

service.load_balancer.add_security_group(load_balancer_security_group)

app.synth()
