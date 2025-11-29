# Web Application Terraform Infrastructure

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
- A public hosted zone for a purchased domain (Note: follow the steps below to manually create a public hosted zone in your AWS account)
- Generate an AWS Access Key for Github Actions
- Generate an AWS Access Key for Terraform and configure AWS CLI


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

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured
- Docker installed (for building container images)
- GitHub account with a repository for frontend
- GitHub Personal Access Token for Amplify

## File Structure

```
├── main.tf                 # Provider configuration
├── variables.tf            # All input variables
├── outputs.tf              # All outputs
├── backend.tf              # State management configuration
├── networking.tf           # VPC, subnets, ALB, security groups, Domain configuration
├── iam-identity.tf         # IAM roles, Cognito
├── crud-service.tf         # CRUD service ASG and launch template, ECR repository
├── crew-service.tf         # Crew service ASG and launch template, ECR repository
├── frontend.tf             # AWS Amplify configuration
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

| Variable               | Description               | Example                        |
|------------------------|---------------------------|--------------------------------|
| `aws_region`           | AWS region for deployment | `us-east-1`                    |
| `project_name`         | Project name              | `my-web-app`                   |
| `microservice_1_ami`   | AMI ID for microservice 1 | `ami-0c55b159cbfafe1f0`        |
| `microservice_2_ami`   | AMI ID for microservice 2 | `ami-0c55b159cbfafe1f0`        |
| `amplify_repository`   | GitHub repo URL           | `https://github.com/user/repo` |
| `amplify_github_token` | GitHub PAT                | `ghp_xxxxx` (keep secret!)     |

### Optional Variables

You can customize:
- Instance types
- Auto Scaling Group sizes
- Health check paths
- Path patterns for routing
- VPC CIDR and availability zones

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
- `COGNITO_USER_POOL_ID`
- `COGNITO_CLIENT_ID`
- `COGNITO_IDENTITY_POOL_ID`
- `COGNITO_REGION`

### Backend Integration

Your microservices can validate Cognito JWT tokens. The User Pool endpoint is available via:

```bash
terraform output cognito_user_pool_endpoint
```

### Common Cognito Customizations

**Enable MFA:**
```hcl
cognito_mfa_configuration = "ON"  # or "OPTIONAL"
```

**Add custom user attributes:**
```hcl
cognito_custom_attributes = [
  {
    name     = "company"
    type     = "String"
    mutable  = true
    required = false
  }
]
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
- `{project-name}-microservice-1`
- `{project-name}-microservice-2`

### Getting ECR Repository URLs

```bash
terraform output ecr_repository_url_microservice_1
terraform output ecr_repository_url_microservice_2
```

### Building and Pushing Images


### Using ECR Images in Auto Scaling Groups

Update your launch template to use ECR images in your user data:

```bash
#!/bin/bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {account-id}.dkr.ecr.us-east-1.amazonaws.com

# Pull and run container
docker pull {ecr-repository-url}:latest
docker run -d -p 8080:8080 {ecr-repository-url}:latest
```

Or in your `terraform.tfvars`:

```hcl
microservice_1_user_data = <<-EOF
#!/bin/bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-1.amazonaws.com
docker pull ${aws_ecr_repository.microservice_1.repository_url}:latest
docker run -d -p 8080:8080 ${aws_ecr_repository.microservice_1.repository_url}:latest
EOF
```

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

## GitHub Actions Deployment

### Setup

1. **Add GitHub Secrets:**
   Navigate to your repository Settings → Secrets and add:
   
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

   - `COGNITO_APP_CLIENT_ID`
   - `COGNITO_REGION`
   - `COGNITO_REGION`
   - `COGNITO_USER_POOL_ID`
   - `CREW_SERVICE_URL`
   - `DB_HOST`
   - `DB_NAME`
   - `DB_PASSWORD`
   - `DB_PORT`
   - `DB_USER`
   - `INTERNAL_CREW_API_KEY`
   - `S3_BUCKET_NAME`
   - `S3_REGION`

   - `PROJECT_NAME`
   - `MICROSERVICE_1_AMI`
   - `MICROSERVICE_1_INSTANCE_TYPE`
   - `MICROSERVICE_1_MIN_SIZE`
   - `MICROSERVICE_1_MAX_SIZE`
   - `MICROSERVICE_1_DESIRED_CAPACITY`
   - `MICROSERVICE_2_AMI`
   - `MICROSERVICE_2_INSTANCE_TYPE`
   - `MICROSERVICE_2_MIN_SIZE`
   - `MICROSERVICE_2_MAX_SIZE`
   - `MICROSERVICE_2_DESIRED_CAPACITY`
   - `AMPLIFY_REPOSITORY`
   - `AMPLIFY_GITHUB_TOKEN`
   - `AMPLIFY_BRANCH_NAME`

2. **Manual Deployment:**
   - Go to Actions tab
   - Select "Deploy Infrastructure"
   - Click "Run workflow"
   - Choose:
     - Environment (prod/dr/staging)
     - AWS Region
     - Action (plan/apply/destroy)

### Workflow Features

- ✅ Manual trigger only (workflow_dispatch)
- ✅ Choose environment and region dynamically
- ✅ Plan before apply
- ✅ Output infrastructure details
- ✅ Secure credential handling

## Outputs

After deployment, Terraform outputs:

- `alb_dns_name` - Load balancer DNS for backend API
- `amplify_branch_url` - Frontend application URL
- `cognito_user_pool_id` - Cognito User Pool ID for authentication
- `cognito_client_id` - Cognito App Client ID
- `cognito_identity_pool_id` - Cognito Identity Pool ID
- `cognito_hosted_ui_url` - Cognito Hosted UI URL
- `ecr_repository_url_microservice_1` - ECR repository URL for MS1
- `ecr_repository_url_microservice_2` - ECR repository URL for MS2
- `vpc_id` - VPC identifier
- `microservice_1_asg_name` - Auto Scaling Group for MS1
- `microservice_2_asg_name` - Auto Scaling Group for MS2

Access outputs:
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
   - Consider AWS Secrets Manager for production

2. **Network Security:**
   - Microservices are in private subnets
   - Only ALB is publicly accessible
   - Security groups follow least-privilege

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

### Adding HTTPS Support

1. Request ACM certificate
2. Add HTTPS listener to ALB:

```hcl
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.microservice_1.arn
  }
}
```

### Adding Auto Scaling Policies

```hcl
resource "aws_autoscaling_policy" "cpu_scaling" {
  name                   = "${var.project_name}-cpu-scaling"
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

1. **AMI not available in region:**
   - Ensure AMI IDs are region-specific
   - Copy AMIs to target region if needed

2. **Amplify deployment fails:**
   - Verify GitHub token has correct permissions
   - Check repository URL format
   - Ensure build spec matches your frontend framework

3. **Health checks failing:**
   - Verify health check paths in your application
   - Check security group rules
   - Review application logs in CloudWatch

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning:** This will delete all infrastructure. Ensure you have backups!

## License

MIT

## Support

For issues or questions, please open an issue in this repository.
