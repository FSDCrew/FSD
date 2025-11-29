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
and keeping secrets private using secrets manager

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

## TODO: Prerequisite Guide


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

## Quick Start

### 1. Clone and Configure

```bash
# Copy the example tfvars file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
vim terraform.tfvars
```

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

## Configuration

### Required Variables

Edit `terraform.tfvars` with your specific values:

| Variable                | Description                              | Example                        |
|-------------------------|------------------------------------------|--------------------------------|
| `aws_region`            | AWS Region for deployment                | `us-east-1`                    |
| `project_name`          | Project Name (fully lowercase)           | `my-web-app`                   |
| `app_domain`            | Domain used for app                      | `campaign.ongspace.com`        |
| `db_host`               | Supabase DB Host                         | `xxxxx.pooler.supabase.com`    |
| `db_port`               | Supabase DB Port                         | `5432`                         |
| `db_name`               | Supabase DB Name                         | `crud`                         |
| `db_user`               | Supabase User                            | `postgres`                     |
| `db_password`           | Supabase DB password                     | `xxxxx`                        |
| `internal_crew_api_key` | Internal Crew API Key                    | `xxxxx`                        |
| `openai_api_key`        | OpenAI API Key                           | `xxxxx`                        |
| `bright_data_api_key`   | Bright Data API Key                      | `xxxxx`                        |
| `bright_data_zone`      | Bright Data Zone                         | `xxxxx`                        |
| `amplify_repository`    | GitHub Repository URL with frontend code | `https://github.com/user/repo` |
| `amplify_github_token`  | GitHub Personal Access Token             | `ghp_xxxxx`                    |
| `amplify_branch_name`   | GitHub Branch name to deploy             | `main`                         |


### Optional Variables
- Instance types
- Auto Scaling Group sizes
- Health check paths
- Path patterns for routing
- VPC CIDR and availability zones
- Cognito Attributes

See `variables.tf` for all available options.

## Working with Cognito

### User Pool Configuration

The template creates a complete Cognito setup:
- **User Pool**: Manages user registration and authentication
- **User Pool Client**: Allows your application to authenticate users
- **Custom Domain**: Auto-generated subdomain for hosted UI

### Accessing Cognito Configuration

After deployment, get your Cognito details:

```bash
terraform output cognito_user_pool_id
terraform output cognito_client_id
terraform output cognito_identity_pool_id
terraform output cognito_hosted_ui_url
```

### Frontend Integration

The Amplify app automatically receives Cognito configuration as environment variables:

- `NEXT_PUBLIC_COGNITO_USER_POOL_ID`
- `NEXT_PUBLIC_COGNITO_CLIENT_ID`
- `NEXT_PUBLIC_COGNITO_DOMAIN`

### Backend Integration

Your microservices can validate Cognito JWT tokens.
The EC2 launch template automatically receives Cognito configuration as environment variables:

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
