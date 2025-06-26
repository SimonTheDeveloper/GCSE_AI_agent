# Airline Test

## Description
Coding test set by ajaali consulting.

## Requirements
- Python 3.9+
- Poetry (version 1.1.0 or later)
- Node.js (version 16.x or later)
- AWS CDK CLI (version 2.166.0)
- AWS CLI (configured with appropriate credentials)

## Setup

1. **Install Poetry**  
   Open a terminal and run:
   ```sh
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install Python dependencies using Poetry**  
   ```sh
   poetry install
   ```

3. **Create a `.env` file**  
   In the root of your project directory, add your AWS credentials and other necessary environment variables:
   ```env
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   AWS_DEFAULT_REGION=your_default_region
   ```

   > **Tip:** For CI/CD, use GitHub Secrets instead of storing credentials in `.env`.

4. **Install Node.js and AWS CDK CLI**  
   Ensure you have Node.js 16.x or later and AWS CDK CLI installed:
   ```sh
   npm install -g aws-cdk@2.166.0
   ```

5. **Install frontend dependencies and build the React app**  
   ```sh
   cd frontend
   npm install
   npm run build
   cd ..
   ```

6. **Configure AWS CLI**  
   ```sh
   aws configure
   ```

7. **Bootstrap the AWS environment**  
   ```sh
   cdk bootstrap aws://ACCOUNT-NUMBER/REGION
   ```
   Replace `ACCOUNT-NUMBER` and `REGION` with your AWS account and region.

8. **Deploy using CDK**  
   ```sh
   cdk deploy
   ```

9. **Generate stub data**  
   ```sh
   poetry run python backend/load_flight_data.py
   ```

10. **Run the FastAPI server locally**  
    ```sh
    poetry run uvicorn backend.app.main:app --reload
    ```

---

## Frontend

- The React app is deployed to S3 via CDK.  
- After deployment, access your app using the S3 static website URL output by CDK.

---

## GitHub Actions AWS Credentials

This template uses the [aws-actions/configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials) action in the workflow:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v2
  with:
    role-to-assume: arn:aws:iam::<YOUR_ACCOUNT_ID>:role/GitHubActionsECRPushRole
    aws-region: <YOUR_REGION>
    role-session-name: github-actions-session
```

Replace the `role-to-assume` and `aws-region` values with your own.

---

## GitHub Actions IAM Role

This template expects you to have an IAM role in AWS named `GitHubActionsECRPushRole` that GitHub Actions can assume for deploying infrastructure and pushing to ECR (if needed).

### Example Trust Relationship for GitHub Actions OIDC

When creating the `GitHubActionsECRPushRole` IAM role, set the following trust relationship to allow GitHub Actions from your repository to assume the role via OIDC:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<YOUR_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:sub": "repo:SimonTheDeveloper/GCSE_AI_agent:ref:refs/heads/main",
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

- Replace `<YOUR_ACCOUNT_ID>` with your AWS account number.
- Update the `repo:...` value if you fork or rename the repository, or want to allow other branches.

> For more details, see [Configuring OpenID Connect in AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect).

### Required IAM Policies

Attach the following policies to your `GitHubActionsECRPushRole`:

#### 1. **AmazonEC2ContainerRegistryPowerUser** (AWS managed)

Allows GitHub Actions to push and pull images to Amazon ECR.

#### 2. **CDKDeployWideAccess** (Custom Inline Policy)

Example policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "s3:*",
        "ec2:*",
        "ecr:*",
        "ecs:*",
        "logs:*",
        "iam:PassRole",
        "dynamodb:*",
        "ssm:GetParameter"
      ],
      "Resource": "*"
    }
  ]
}
```

> **Note:**  
> The above permissions allow full access to the main AWS services used by this template. You may further restrict them for production use.

---

With these permissions and the trust relationship, your GitHub Actions workflow will be able to deploy infrastructure and push images as needed.