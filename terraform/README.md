# Terraform Template Overview

This Terraform template deploys a complete AWS infrastructure for the campAIgn app with:
- AWS Cognito for user authentication and authorisation
- 2 Auto Scaling Groups for microservices
- Application Load Balancer (public-facing)
- AWS Amplify for frontend deployment
- VPC with public subnets across multiple AZs
- S3 Bucket for crew outputs
- Split-horizon hosted zone for domains and routing

Note: This template outlines the basic infrastructure for our app's MVP,
in an actual production environment consider deployment of services in private subnets
and keeping secrets private using secrets manager.

## Prerequisites

The following prerequisites must be met before the terraform template can be applied:
- Terraform >= 1.0
- AWS CLI
- AWS Public Hosted Zone for a purchased domain
- Supabase account & empty database setup
- Generate an AWS Access Key for Github Actions
- Generate an AWS Access Key for Terraform and configure AWS CLI
- GitHub Personal Access Token for Amplify

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                     Internet                         │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
                    ┌─────────┐
                    │ Amplify │
                    │Frontend │
                    │         │
                    │ Cognito │
                    │  Auth   │
                    └────┬────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Application Load    │
              │     Balancer (ALB)   │
              └──────────┬───────────┘
                         │
                  ┌───────────────┐
                  │               │
                  ▼               ▼
             ┌─────────┐    ┌──────────┐
             │  ASG 1  │    │  ASG 2   │
             │ (Crud)  │    │  (Crew)  │
             │         │    │          │
             │  ECR 1  │    │  ECR 2   │
             └─────────┘    └──────────┘

Components:
- AWS Cognito: User authentication and authorization
- ECR Repositories: Container image storage for microservices
- Auto Scaling Groups: Deploy containers from ECR images
- Application Load Balancer: Routes traffic to microservices
- AWS Amplify: Frontend hosting with Cognito integration
- GitHub Actions: CI/CD workflow pushes images to ECR
```

## File Structure

```
├── main.tf                 # Provider configuration
├── variables.tf            # All input variables
├── outputs.tf              # All outputs
├── networking.tf           # VPC, subnets, ALB, security groups, Domain configuration
├── iam-identity.tf         # IAM roles, Cognito
├── crud-service.tf         # CRUD service ASG and launch template, ECR repository
├── crew-service.tf         # Crew service ASG and launch template, ECR repository
├── frontend.tf             # AWS Amplify configuration
├── s3.tf                   # S3 Bucket configuration
├── data-sources.tf         # AWS Data Sources
└── terraform.tfvars        # Your configuration values
```


## Prerequisite Guide

### 1. Terraform CLI

You must have Terraform installed to provision the infrastructure.
1.  **Download:** Visit the [Terraform Downloads page](https://www.terraform.io/downloads).
2.  **Install:** Follow the instructions for your operating system (macOS, Windows, or Linux).
3.  **Verify:** Open your terminal and run:
    ```bash
    terraform -version
    ```
    *Ensure the version is >= 1.0.0.*

### 2. AWS CLI 

The AWS Command Line Interface is required for Terraform to authenticate with your AWS account.
1.  **Install:** Follow the [official AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
2.  **Verify:** Run the following command:
    ```bash
    aws --version
    ```

### 3. R53 Public Hosted Zone Setup

You need a registered domain name (e.g., `campaign.ongspace.com`) managed by AWS Route 53.
1.  **If you bought the domain on AWS:**
    * A Hosted Zone is automatically created. Note down the **Domain Name**.
2.  **If you bought the domain elsewhere (GoDaddy, Namecheap, etc.):**
    * Log in to the AWS Console and navigate to **Route 53**.
    * Click **Create Hosted Zone**.
    * Enter your domain name and select **Public Hosted Zone**.
    * **Crucial Step:** Copy the 4 `NS` (Name Server) records provided by AWS.
    * Go to your third-party registrar settings and update their "Custom Nameservers" to match the 4 AWS values.

### 4. Supabase Setup

This project uses Supabase as the external PostgreSQL database.
1.  Log in to [Supabase](https://supabase.com/).
2.  Create a **New Project**.
3.  **Database Password:** Create a strong password and **save it immediately** (you cannot view it again).
4.  Once the project is ready, click on you project and locate the **Connect** button on the top bar
5.  Select the **Connection String** tab and change the method to **Session Pooler**. 
6.  Click on the dropdown to **view parameters**. It will look like this:
    ```bash
      host: *****.pooler.supabase.com
      port: 5432
      database: postgres
      user: postgres.xxxxx
    ```
6.  Store these variables (including your password); you will need it for the Terraform variables.

### 5. Generating AWS Access Keys

You need two sets AWS Access Keys (Access Key ID and Secret Access Key) to allow Terraform and GitHub Actions to authenticate with your account.

**A. Access Keys for Terraform (Local Machine):**
1.  Log in to the **AWS Console**.
2.  Click your **Username** in the top-right corner and select **Security credentials**.
3.  Scroll down to the **Access keys** section and click **Create access key**.
4.  Select **Command Line Interface (CLI)** as the use case.
5.  Check the confirmation box ("I understand...") and click **Next**.
6.  Click **Create access key**.
7.  **Important:** Copy the **Access Key ID** and **Secret Access Key** immediately or download the `.csv` file. You will not be able to view the Secret Key again.
8.  **Configure Local CLI:**
    Open your terminal and run the command below. Paste your keys when prompted:
    ```bash
    aws configure
    ```

**B. Access Keys for Github Actions (CI/CD):**
1.  Repeat steps 1-3 above to start creating a second key.
2.  Select **Third-party service** as the use case.
3.  Check the confirmation box (acknowledging AWS recommendations) and click **Next**.
4.  Click **Create access key**.
5.  **Important:** Copy these keys and save them securely. You will need to add them to your **GitHub Repository Secrets** later (typically named `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`).

### 6. Generating Github Personal Access Token
AWS Amplify needs permission to watch your repository and deploy the frontend automatically.

1.  Log in to GitHub.
2.  Go to **Settings** (Click your profile photo) -> **Developer settings** (bottom left).
3.  Select **Personal access tokens** -> **Tokens (classic)**.
4.  Click **Generate new token (classic)**.
5.  **Scopes:** Select the following scopes:
    * `repo` (Full control of private repositories)
    * `admin:repo_hook` (Full control of repository hooks)
6.  Generate and **copy the token**. You will need this for the Terraform variable `amplify_github_token`.


## Full Deployment Guide

### 1. Clone and Configure Terraform Variables

```bash
# Change your directory to the terraform folder
cd terraform

# Copy the example tfvars file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
vim terraform.tfvars
```

#### Required Variables

Edit `terraform.tfvars` with your specific values:

| Variable                | Description                              | Example                        |
|-------------------------|------------------------------------------|--------------------------------|
| `aws_region`            | AWS Region for deployment                | `ap-southeast-1`               |
| `project_name`          | Project Name (fully lowercase)           | `campaign`                     |
| `app_domain`            | Domain used for app                      | `campaign.ongspace.com`        |
| `db_host`               | Supabase DB Host                         | `xxxxx.pooler.supabase.com`    |
| `db_port`               | Supabase DB Port                         | `5432`                         |
| `db_name`               | Supabase DB Name                         | `crud`                         |
| `db_user`               | Supabase User                            | `postgres.xxxxx`               |
| `db_password`           | Supabase DB password                     | `xxxxx`                        |
| `internal_crew_api_key` | Internal Crew API Key                    | `xxxxx`                        |
| `openai_api_key`        | OpenAI API Key                           | `xxxxx`                        |
| `bright_data_api_key`   | Bright Data API Key                      | `xxxxx`                        |
| `bright_data_zone`      | Bright Data Zone                         | `xxxxx`                        |
| `orshot_api_key`        | Orshot API Key                           | `xxxxx`                        |
| `orshot_api_url`        | Orshot API URL                           | `https://api.orshot.com/xxxxx` |
| `gemini_api_key`        | Gemini API Key                           | `xxxxx`                        |
| `amplify_repository`    | GitHub Repository URL with frontend code | `https://github.com/user/repo` |
| `amplify_github_token`  | GitHub Personal Access Token             | `ghp_xxxxx`                    |
| `amplify_branch_name`   | GitHub Branch name to deploy             | `main`                         |

#### Optional Variables
- Instance types
- Auto Scaling Group sizes
- Health check paths
- Path patterns for routing
- VPC CIDR and availability zones
- Cognito Attributes

See `variables.tf` for all available options.

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review the Plan

```bash
terraform plan
```

### 4. Deploy

```bash
terraform apply
```

### 5. Configure Github Secrets

Github Actions is used to automate builds and push container images to AWS ECR.
The following secrets must be added for the pipeline to succeed:

1.  Navigate to your github repository.
2.  Click **Settings** in the top bar.
3.  Click **Secrets and variables -> Actions** in the side bar.
4.  Click **New Repository Secret**.

The following secrets must be added for the pipeline to succeed:

| Name                    | Description                                | Example                        |
|-------------------------|--------------------------------------------|--------------------------------|
| `AWS_ACCESS_KEY_ID`     | AWS Access Key ID (for Github Actions)     | `xxxxx`                        |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key (for Github Actions) | `xxxxx`                        |
| `AWS_REGION`            | AWS Deployment Region                      | `ap-southeast-1`               |
| `COGNITO_APP_CLIENT_ID` | Cognito App Client ID                      | `xxxxx`                        |
| `COGNITO_USER_POOL_ID`  | Cognito User Pool ID                       | `ap-southeast-1_xxxxx`         |
| `COGNITO_REGION`        | Cognito region (same as deployment region) | `ap-southeast-1`               |
| `S3_BUCKET_NAME`        | S3 Bucket Name                             | `campaign-prod-bucket`         |
| `S3_REGION`             | S3 Region (same as deployment region)      | `ap-southeast-1`               |
| `INTERNAL_CREW_API_KEY` | Internal Crew API Key                      | `xxxxx`                        |
| `CREW_SERVICE_URL`      | Internal Crew API Key                      | `xxxxx`                        |
| `CRUD_ECR_REPOSITORY`   | CRUD ECR Repository Name                   | `prod/crud`                    |
| `CREW_ECR_REPOSITORY`   | CREW ECR Repository Name                   | `prod/crew`                    |
| `CRUD_ASG_NAME`         | CRUD ASG Name                              | `crud-asg`                     |
| `CREW_ASG_NAME`         | CREW ASG Name                              | `crew-asg`                     |
| `DB_HOST`               | Supabase DB Host                           | `xxxxx.pooler.supabase.com`    |
| `DB_PORT`               | Supabase DB Port                           | `5432`                         |
| `DB_NAME`               | Supabase DB Name                           | `crud`                         |
| `DB_USER`               | Supabase User                              | `postgres.xxxxx`               |
| `DB_PASSWORD`           | Supabase DB password                       | `xxxxx`                        |
| `FRONTEND_ORIGIN`       | Your site url                              | `https://wwww.xxxxx.com`       |

The following secrets can be found from terraform outputs:
1.  AWS_REGION            = aws_region
2.  COGNITO_APP_CLIENT_ID = cognito_client_id
3.  COGNITO_USER_POOL_ID  = cognito_user_pool_id
4.  COGNITO_REGION        = aws_region
5.  S3_BUCKET_NAME        = bucket_name
6.  S3_REGION             = aws_region
7.  CREW_SERVICE_URL      = crew_api_private_url
8.  CRUD_ECR_REPOSITORY   = ecr_repository_name_crud_service
9.  CREW_ECR_REPOSITORY   = ecr_repository_name_crew_service
10. CRUD_ASG_NAME         = crud_service_asg_name
11. CREW_ASG_NAME         = crew_service_asg_name

To access all outputs:
```bash
terraform output
```

### 6. Manually Trigger CD Pipelines

1.  Navigate to your github repository.
2.  Click **Actions** in the top bar.
3.  Select **CD | CREW Service Deployment** in the sidebar.
4.  Click **Run workflow**; Ensure that the branch selected is **main**.
5.  Select **CD | CRUD Service Deployment** in the sidebar and repeat step 4.

Once the pipelines succeed, you should be able to access your app through your domain.


### Frontend Integration

The Amplify app automatically receives Cognito configuration as environment variables:

- `NEXT_PUBLIC_APP_ENV`
- `NEXT_PUBLIC_APP_DOMAIN`
- `NEXT_PUBLIC_CREW_API_BASE_URL`
- `NEXT_PUBLIC_CRUD_API_BASE_URL`
- `NEXT_PUBLIC_COGNITO_USER_POOL_ID`
- `NEXT_PUBLIC_COGNITO_CLIENT_ID`
- `NEXT_PUBLIC_COGNITO_DOMAIN`

### Backend Integration

The CRUD service can validate Cognito JWT tokens.
The CRUD service EC2 launch template automatically receives Cognito configuration as environment variables:

- `COGNITO_REGION`
- `COGNITO_APP_CLIENT_ID`
- `COGNITO_USER_POOL_ID`

### Common Cognito Customizations

**To Enable MFA:**
```hcl
cognito_mfa_configuration = "ON"  # or "OPTIONAL"
```

**Configure OAuth URLs:**
```hcl
cognito_callback_urls = [
  "https://yourdomain.com/callback",
  "http://localhost:3000/callback"
]
cognito_logout_urls = [
  "https://yourdomain.com/logout",
  "http://localhost:3000/logout"
]
```

## Working with ECR

### ECR Repositories

Two ECR repositories are created automatically:
- `{project-name}-crud-service`
- `{project-name}-crew-service`

### Getting ECR Repository URLs

```bash
terraform output ecr_repository_url_crud_service
terraform output ecr_repository_url_crew_service
```

### Building and Pushing Images


### Using ECR Images in Auto Scaling Groups

EC2 launch templates are automatically configured to pull and use ECR images in user data.


### ECR Lifecycle Policy

Images are automatically cleaned up based on `ecr_image_count_limit` (default: 10 most recent images retained).

To change the retention policy:

```hcl
ecr_image_count_limit = 20  # Keep last 20 images
```


## Disaster Recovery

### Deploying to a Different Region

1. **Update region in tfvars:**
   ```hcl
   aws_region = "ap-southeast-2"
   availability_zones = ["ap-southeast-2a", "ap-southeast-2b"]
   ```

2. **Update environment:**
   ```hcl
   environment = "dr"
   ```

3. **Deploy:**
   ```bash
   terraform init
   terraform apply
   ```


### Multi-Region Strategy

For a complete DR setup:

1. **Use separate state files per region:**
   ```hcl
   # backend.tf
   terraform {
     backend "s3" {
       bucket = "terraform-state-bucket"
       key    = "webapp/us-east-1/terraform.tfstate"
       region = "us-east-1"
     }
   }
   ```

2. **Create region-specific tfvars:**
   - `terraform.prod.tfvars` (primary)
   - `terraform.dr.tfvars` (disaster recovery)

3. **Deploy to both regions:**
   ```bash
   # Primary region
   terraform apply -var-file="terraform.prod.tfvars"
   
   # DR region (in separate directory or workspace)
   terraform apply -var-file="terraform.dr.tfvars"
   ```


## Outputs

After deployment, important Terraform outputs include but are not limited to:

- `vpc_id` - VPC identifier
- `public_subnet_ids` - IDs of public subnets
- `amplify_custom_domain_url` - Frontend application URL
- `amplify_domain_status` - Status of the custom domain integration
- `cognito_user_pool_id` - Cognito User Pool ID for authentication
- `cognito_client_id` - Cognito App Client ID
- `cognito_domain` - Cognito User Pool domain
- `ecr_repository_url_crud_service` - ECR repository URL for crud service
- `ecr_repository_url_crew_service` - ECR repository URL for crew service
- `crud_service_asg_name` - Auto Scaling Group for crud service
- `crew_service_asg_name` - Auto Scaling Group for crew service
- `bucket_name` - S3 Bucket name

To access all outputs:
```bash
terraform output
```


## Resource Tagging

All resources are tagged with:
- `Name` - Resource name
- `Environment` - Environment identifier (prod/dr/staging)

## Security Considerations

1. **Never commit sensitive values:**
   - Add `terraform.tfvars` to `.gitignore`
   - Use GitHub Secrets for CI/CD
   - Store secrets in AWS Secrets Manager for production

2. **Network Security (production):**
   - Place Microservices in private subnets instead of public subsets
   - Only ALB is publicly accessible
   - Ensure Security Groups follow least-privilege

3. **IAM Permissions:**
   - EC2 instances use IAM roles
   - Update IAM policies as needed for your services


## Customization Tips

### Adding NAT Gateways

For private subnet internet access (e.g., package downloads):

```hcl
resource "aws_eip" "nat" {
  count  = length(var.availability_zones)
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  count         = length(var.availability_zones)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}
```

### Adding Auto Scaling Policies

```hcl
resource "aws_autoscaling_policy" "cpu_scaling" {
  name                   = lower("${var.project_name}-cpu-scaling")
  autoscaling_group_name = aws_autoscaling_group.microservice_1.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```


## Troubleshooting

### Common Issues

1. **Amplify deployment fails:**
   - Verify GitHub token has correct permissions
   - Check repository URL format
   - Ensure build spec matches your frontend framework

2. **Health checks failing:**
   - Verify health check paths in your application
   - Check security group rules
   - Review application logs in CloudWatch


## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning:** This will delete all infrastructure. Ensure you have backups!


## Support

For issues or questions, please open an issue in this repository.
