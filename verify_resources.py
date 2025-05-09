import boto3

# Check if the VPC exists
def check_vpc(vpc_name):
    ec2 = boto3.client("ec2")
    response = ec2.describe_vpcs(
        Filters=[
            {"Name": "tag:Name", "Values": [vpc_name]}
        ]
    )
    print("VPC Response:", response)  # Debugging
    return response["Vpcs"]

# Check if the ECS Cluster exists
def check_ecs_cluster(cluster_name):
    ecs = boto3.client("ecs")
    response = ecs.describe_clusters(clusters=[cluster_name])
    print("ECS Response:", response)  # Debugging
    return response["clusters"]

# Check if the DynamoDB Table exists
def check_dynamodb_table(table_name):
    dynamodb = boto3.client("dynamodb")
    try:
        response = dynamodb.describe_table(TableName=table_name)
        print("DynamoDB Response:", response)  # Debugging
        return response["Table"]
    except dynamodb.exceptions.ResourceNotFoundException:
        return None

# Check if the IAM Role exists
def check_iam_role(role_name):
    iam = boto3.client("iam")
    try:
        response = iam.get_role(RoleName=role_name)
        print("IAM Role Response:", response)  # Debugging
        return response["Role"]
    except iam.exceptions.NoSuchEntityException:
        return None

# Check if the CloudWatch Log Group exists
def check_log_group(log_group_name):
    logs = boto3.client("logs")
    response = logs.describe_log_groups(
        logGroupNamePrefix=log_group_name
    )
    print("Log Group Response:", response)  # Debugging
    return response["logGroups"]

# Main function to check all resources
def main():

    # Check ECS Cluster
    clusters = check_ecs_cluster("AppCluster")
    if clusters:
        print(f"ECS Cluster '{clusters[0]['clusterName']}' exists.")
    else:
        print("ECS Cluster not found.")

    # Check DynamoDB Table
    table = check_dynamodb_table("student-progress")
    if table:
        print(f"DynamoDB Table '{table['TableName']}' exists.")
    else:
        print("DynamoDB Table not found.")

    # Check IAM Role
    role = check_iam_role("AppTaskExecutionRole")  # Replace with your role name
    if role:
        print(f"IAM Role '{role['RoleName']}' exists.")
    else:
        print("IAM Role not found.")

    # Check CloudWatch Log Group
    log_groups = check_log_group("/ecs/AppCluster")
    if log_groups:
        print(f"Log Group '{log_groups[0]['logGroupName']}' exists.")
    else:
        print("Log Group not found.")

    # Check VPC
    vpcs = check_vpc("AppVpc")
    if vpcs:
        print(f"VPC '{vpcs[0]['VpcId']}' exists.")
    else:
        print("VPC not found.")

if __name__ == "__main__":
    main()