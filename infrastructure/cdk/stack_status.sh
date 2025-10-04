#!/usr/bin/env bash
# Quick status helper for the CDK stack and ECS service.
# Usage: ./stack_status.sh [STACK_NAME]
# Defaults to GcseAiStack if no name provided.

set -euo pipefail
STACK=${1:-GcseAiStack}
REGION_FLAG=""
if [ -n "${AWS_REGION:-}" ]; then
  REGION_FLAG="--region $AWS_REGION"
fi

echo "=== CloudFormation Stack Status ($STACK) ==="
aws cloudformation describe-stacks --stack-name "$STACK" $REGION_FLAG \
  --query 'Stacks[0].{Status:StackStatus,CreationTime:CreationTime,LastUpdated:LastUpdatedTime}'

echo -e "\n=== Recent Failure / Rollback Events (if any) ==="
aws cloudformation describe-stack-events --stack-name "$STACK" $REGION_FLAG \
  --query 'StackEvents[?contains(ResourceStatus, `FAILED`) || contains(ResourceStatus, `ROLLBACK`)].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
  --output table | tail -n 25 || true

echo -e "\n=== Outputs ==="
aws cloudformation describe-stacks --stack-name "$STACK" $REGION_FLAG \
  --query 'Stacks[0].Outputs' --output table || true

# ECS service status attempt
echo -e "\n=== ECS Service Status (best effort) ==="
CLUSTERS=$(aws ecs list-clusters $REGION_FLAG --query 'clusterArns' --output text 2>/dev/null || true)
if [ -z "$CLUSTERS" ] || [ "$CLUSTERS" = "None" ]; then
  echo "No ECS clusters found (yet)."; exit 0
fi
# Pick first cluster containing 'AppCluster' else first
APP_CLUSTER=$(aws ecs list-clusters $REGION_FLAG --query 'clusterArns[?contains(@, `AppCluster`)] | [0]' --output text 2>/dev/null || true)
if [ -z "$APP_CLUSTER" ] || [ "$APP_CLUSTER" = "None" ]; then
  APP_CLUSTER=$(echo "$CLUSTERS" | awk '{print $1}')
fi
SERVICES=$(aws ecs list-services --cluster "$APP_CLUSTER" $REGION_FLAG --query 'serviceArns' --output text 2>/dev/null || true)
if [ -z "$SERVICES" ] || [ "$SERVICES" = "None" ]; then
  echo "No ECS services found (yet)."; exit 0
fi
APP_SERVICE=$(aws ecs list-services --cluster "$APP_CLUSTER" $REGION_FLAG --query 'serviceArns[?contains(@, `AppFargateService`)] | [0]' --output text 2>/dev/null || true)
if [ -z "$APP_SERVICE" ] || [ "$APP_SERVICE" = "None" ]; then
  APP_SERVICE=$(echo "$SERVICES" | awk '{print $1}')
fi
aws ecs describe-services --cluster "$APP_CLUSTER" --services "$APP_SERVICE" $REGION_FLAG \
  --query 'services[0].{Status:status,Running:runningCount,Pending:pendingCount,Desired:desiredCount,LaunchType:launchType,HealthCheckGrace:healthCheckGracePeriodSeconds}' \
  --output table || true

# ALB DNS quick fetch (from outputs) if present
LB_DNS=$(aws cloudformation describe-stacks --stack-name "$STACK" $REGION_FLAG --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerURL'].OutputValue" --output text 2>/dev/null || true)
if [ -n "$LB_DNS" ] && [ "$LB_DNS" != "None" ]; then
  echo -e "\nALB DNS: http://$LB_DNS"
fi

echo -e "\nDone."