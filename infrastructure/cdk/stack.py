from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
    aws_cognito as cognito,
    CfnOutput,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
    Duration,
)
from constructs import Construct
import os

class GcseAiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Read project-specific values from environment variables or use defaults
        # Force new single-table name gcse_app unless overridden explicitly
        table_name = os.environ.get("DYNAMODB_TABLE_NAME", "gcse_app")
        bucket_name = os.environ.get("FRONTEND_BUCKET_NAME", "frontend-bucket")

        # VPC (2 AZs)
        vpc = ec2.Vpc(self, "AppVpc", max_azs=2)

        # ECS Cluster
        cluster = ecs.Cluster(self, "AppCluster", vpc=vpc)

        # DynamoDB Single Table (PK/SK + GSI1)
        table = dynamodb.Table(
            self, "GcseAppTable",
            table_name=table_name,
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # CHANGE TO RETAIN FOR PRODUCTION
        )
        table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(name="GSI1PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="GSI1SK", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL
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
            # Build Docker image from the backend directory (two levels up from cdk/)
            image=ecs.ContainerImage.from_asset("../../backend"),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="AppLogs",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            environment={
                "DYNAMODB_TABLE_NAME": table_name,
                "DYNAMODB_GSI1": "GSI1",
                # Placeholder values, updated after Cognito is defined below
            }
        )
        # Align container port with uvicorn port inside Dockerfile (8001)
        container.add_port_mappings(ecs.PortMapping(container_port=8001))

        # Fargate Service behind Load Balancer
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "AppFargateService",
            cluster=cluster,
            task_definition=task_definition,
            public_load_balancer=True,
            health_check_grace_period=Duration.seconds(120),
        )

        # Make ALB health checks hit /health and expect HTTP 200
        service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )

        # S3 bucket for React frontend hosting
        # If user did not explicitly set FRONTEND_BUCKET_NAME, let CDK generate a unique name
        if os.environ.get("FRONTEND_BUCKET_NAME"):
            frontend_bucket = s3.Bucket(
                self, "FrontendBucket",
                bucket_name=bucket_name,
                website_index_document="index.html",
                website_error_document="index.html",
                public_read_access=True,
                block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
                removal_policy=RemovalPolicy.DESTROY,
                auto_delete_objects=True,   # ensure deletable during rollback/destroy
            )
        else:
            frontend_bucket = s3.Bucket(
                self, "FrontendBucket",
                website_index_document="index.html",
                website_error_document="index.html",
                public_read_access=True,
                block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
                removal_policy=RemovalPolicy.DESTROY,
                auto_delete_objects=True,
            )

        # (Optional) Deploy local build folder to S3 on cdk deploy
        s3deploy.BucketDeployment(
            self, "DeployReactApp",
            sources=[s3deploy.Source.asset("../../frontend/build")],
            destination_bucket=frontend_bucket,
        )

        # Output Load Balancer DNS
        CfnOutput(self, "LoadBalancerURL",
                  value=service.load_balancer.load_balancer_dns_name,
                  description="Public URL for the FastAPI app",
                  export_name="FastApiLoadBalancerUrl")

        CfnOutput(self, "FrontendBucketURL", value=frontend_bucket.bucket_website_url)
        CfnOutput(self, "DynamoTableName", value=table.table_name)
        CfnOutput(self, "DynamoGSI1", value="GSI1")

        # ==========================
        # Cognito User Pool + Hosted UI
        # ==========================
        # Allow overrides from env for domain prefix and callback URLs
        domain_prefix = os.environ.get("COGNITO_DOMAIN_PREFIX") or f"gcse-ai-{Stack.of(self).stack_name.lower()}"
        # Trim invalid chars and length for domain prefix
        domain_prefix = domain_prefix.replace("_", "-")[:63]

        user_pool = cognito.UserPool(
            self,
            "UserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False)
            ),
            password_policy=cognito.PasswordPolicy(min_length=8),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY,  # consider RETAIN for prod
        )

        callback_urls = [
            "http://localhost:3000",
        ]
        logout_urls = [
            "http://localhost:3000",
        ]
        # Allow env overrides
        if os.environ.get("COGNITO_CALLBACK_URLS"):
            callback_urls = [u.strip() for u in os.environ["COGNITO_CALLBACK_URLS"].split(",") if u.strip()]
        if os.environ.get("COGNITO_LOGOUT_URLS"):
            logout_urls = [u.strip() for u in os.environ["COGNITO_LOGOUT_URLS"].split(",") if u.strip()]

        user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=user_pool,
            generate_secret=False,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True, implicit_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL, cognito.OAuthScope.PROFILE],
                callback_urls=callback_urls,
                logout_urls=logout_urls,
            ),
            prevent_user_existence_errors=True,
        )

        domain = user_pool.add_domain(
            "CognitoDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix),
        )

        issuer_url = f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool.user_pool_id}"

        # Update container env with Cognito details so backend can verify JWTs
        container.add_environment("AWS_REGION", self.region)
        container.add_environment("COGNITO_USER_POOL_ID", user_pool.user_pool_id)
        container.add_environment("COGNITO_APP_CLIENT_ID", user_pool_client.user_pool_client_id)
        container.add_environment("COGNITO_ISSUER", issuer_url)

        CfnOutput(self, "CognitoUserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "CognitoUserPoolClientId", value=user_pool_client.user_pool_client_id)
        CfnOutput(self, "CognitoDomain", value=domain.domain_name)
        CfnOutput(self, "CognitoIssuer", value=issuer_url)