<!--BEGIN STABILITY BANNER-->
---

![Stability: Stable](https://img.shields.io/badge/stability-Stable-success.svg?style=for-the-badge)

> **This is a stable example. It should successfully build out of the box**
>
> This example is built on Construct Libraries marked "Stable" and does not have any infrastructure prerequisites to build.
---
<!--END STABILITY BANNER-->

# ECS Application-Load-Balanced EC2 Service

This sample project demonstrates how to define an ECS service that is served by an application load-balancer (ALB) via the CDK [ApplicationLoadBalancedEc2Service construct](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ecs_patterns.ApplicationLoadBalancedEc2Service.html).

The [ApplicationLoadBalancedEc2Service construct](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ecs_patterns.ApplicationLoadBalancedEc2Service.html) abstracts the deployment of an EC2-backed ECS service and its ALB and additionally an AWS Lambda function that is triggered by 'terminate' lifecycle events on the ECS cluster's auto-scaling group.  The Lambda function handles graceful draining of nodes by waiting for tasks on the nodes to complete before sending the 'CONTINUE' lifecycle signal to terminate the node.

This example also demonstrates how to configure an autoscaling group (ASG) for an ECS cluster and the security groups (SG) that need to be defined to properly route traffic from the ALB. 

## Lifecycle Handler Logic

The [ApplicationLoadBalancedEc2Service construct](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ecs_patterns.ApplicationLoadBalancedEc2Service.html) abstracts the deployment of a Lambda function that manages the graceful draining of nodes on terminate events from the ASG. The logic of the Lambda function can be viewed from the synthesized CDK, but is included below for your reference:

```
import boto3, json, os, time

ecs = boto3.client('ecs')
autoscaling = boto3.client('autoscaling')

def lambda_handler(event, context):

    print(json.dumps(event))
    cluster = os.environ['CLUSTER']
    snsTopicArn = event['Records'][0]['Sns']['TopicArn']
    lifecycle_event = json.loads(event['Records'][0]['Sns']['Message'])
    instance_id = lifecycle_event.get('EC2InstanceId')
    if not instance_id:
        print('Got event without EC2InstanceId: %s', json.dumps(event))
        return

    instance_arn = container_instance_arn(cluster, instance_id), instance_arn))

    if not instance_arn:
        return

    task_arns = container_instance_task_arns(cluster, instance_arn)

    if task_arns:
        print('Instance ARN %s has task ARNs %s' % (instance_arn, ', '.join(task_arns)))

    while has_tasks(cluster, instance_arn, task_arns):
        time.sleep(10)

    try:
        print('Terminating instance %s' % instance_id)
        autoscaling.complete_lifecycle_action(
            LifecycleActionResult='CONTINUE',
            **pick(lifecycle_event, 'LifecycleHookName', 'LifecycleActionToken', 'AutoScalingGroupName'))
    except Exception as e:
        # Lifecycle action may have already completed.
        print(str(e))


def container_instance_arn(cluster, instance_id):
    """Turn an instance ID into a container instance ARN."""
    arns = ecs.list_container_instances(cluster=cluster, filter='ec2InstanceId==' + instance_id['containerInstanceArns]
        if not arns:
        return None
    return arns[0]

def container_instance_task_arns(cluster, instance_arn):
    """Fetch tasks for a container instance ARN."""
    arns = ecs.list_tasks(cluster=cluster, containerInstance=instance_arn)['taskArns']
    return arns

def has_tasks(cluster, instance_arn, task_arns):
    """Return True if the instance is running tasks for the given cluster."""
    instances = ecs.describe_container_instances(cluster=cluster, containerInstances=[instance_arn])['containerInstances']
    if not instances:
        return False
    instance = instances[0]

    if instance['status'] == 'ACTIVE':
        # Start draining, then try again later
        set_container_instance_to_draining(cluster, instance_arn)
        return True

    task_count = None

    if task_arns:
        # Fetch details for tasks running on the container instance
        tasks = ecs.describe_tasks(cluster=cluster, tasks=task_arns)['tasks']
        if tasks:
        # Consider any non-stopped tasks as running
        task_count = sum(task['lastStatus'] != 'STOPPED' for task in tasks) + instance['pendingTasksCount']

    if not task_count:
        # Fallback to instance task counts if detailed task information is unavailable
        task_count = instance['runningTasksCount'] + instance['pendingTasksCount']
        
    print('Instance %s has %s tasks' % (instance_arn, task_count))

    return task_count > 0

def set_container_instance_to_draining(cluster, instance_arn):
    ecs.update_container_instances_state(
        cluster=cluster,
        containerInstances=[instance_arn], status='DRAINING')


def pick(dct, *keys):
    """Pick a subset of a dict."""
    return {k: v for k, v in dct.items() if k in keys}
```


## Deployment

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

