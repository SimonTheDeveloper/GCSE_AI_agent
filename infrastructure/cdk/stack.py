from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
)
from constructs import Construct
import os

class GcseAiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC (2 AZs)
        vpc = ec2.Vpc(self, "AppVpc", max_azs=2)

        # ECS Cluster
        cluster = ecs.Cluster(self, "AppCluster", vpc=vpc)

        # DynamoDB Table
        table = dynamodb.Table(
            self, "student-progress",
            table_name="student-progress",
            partition_key=dynamodb.Attribute(name="student_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="subject_topic", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # IAM Role for Task Execution
        task_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        table.grant_read_write_data(task_role)

        # Fargate Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self, "AppTaskDef",
            cpu=256,
            memory_limit_mib=512,
            task_role=task_role
        )

        container = task_definition.add_container(
            "AppContainer",
            image=ecs.ContainerImage.from_asset("./"),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="AppLogs",
                log_retention=logs.RetentionDays.ONE_WEEK
            )
        )
        container.add_port_mappings(ecs.PortMapping(container_port=80))

        # Fargate Service behind Load Balancer
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "AppFargateService",
            cluster=cluster,
            task_definition=task_definition,
            public_load_balancer=True
        )

        # S3 bucket for React frontend hosting
        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.NONE,  # <-- Add this line
            removal_policy=RemovalPolicy.DESTROY
        )

        # (Optional) Deploy local build folder to S3 on cdk deploy
        s3deploy.BucketDeployment(
            self, "DeployReactApp",
            sources=[s3deploy.Source.asset("../frontend/build")],
            destination_bucket=frontend_bucket,
        )

        # Output Load Balancer DNS
        CfnOutput(self, "LoadBalancerURL",
                  value=service.load_balancer.load_balancer_dns_name,
                  description="Public URL for the FastAPI app",
                  export_name="FastApiLoadBalancerUrl")

        CfnOutput(self, "FrontendBucketURL", value=frontend_bucket.bucket_website_url)