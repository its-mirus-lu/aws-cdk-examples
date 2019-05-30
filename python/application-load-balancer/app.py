#!/usr/bin/env python3
from aws_cdk import (
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    cdk,
)


class LoadBalancerStack(cdk.Stack):
    def __init__(self, app: cdk.App, id: str) -> None:
        super().__init__(app, id)

        vpc = ec2.Vpc(self, "VPC")

        asg = autoscaling.AutoScalingGroup(
            self,
            "ASG",
            vpc=vpc,
            instance_type=ec2.InstanceTypePair(
                ec2.InstanceClass.Burstable2, ec2.InstanceSize.Micro
            ),
            machine_image=ec2.AmazonLinuxImage(),
        )

        lb = elbv2.ApplicationLoadBalancer(self, "LB", vpc=vpc, internet_facing=True)

        listener = lb.add_listener("Listener", port=80)
        listener.add_targets("Target", port=80, targets=[asg])
        listener.connections.allow_default_port_from_any_ipv4("Open to the world")

        asg.scale_on_request_count("AModestLoad", target_requests_per_second=1)


app = cdk.App()
LoadBalancerStack(app, "LoadBalancerStack")
app.run()
