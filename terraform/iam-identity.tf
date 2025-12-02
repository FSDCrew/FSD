# ============================================
# IAM & IDENTITY CONFIGURATION
# IAM Roles, Cognito User Pool, Identity Pool,
# ============================================

# ============================================
# IAM ROLES & POLICIES
# ============================================

# IAM Role for EC2 Instances
resource "aws_iam_role" "backend_instance_role" {
  name = "${var.project_name}-backend-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-backend-role"
    Environment = var.environment
  }
}

# Attach SSM policy for instance management
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.backend_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM Policy for ECR access
resource "aws_iam_role_policy" "ecr_access" {
  name = "${var.project_name}-ecr-access"
  role = aws_iam_role.backend_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetRepositoryPolicy",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:DescribeImages",
          "ecr:BatchGetImage",
          "ecr:GetLifecyclePolicy",
          "ecr:GetLifecyclePolicyPreview",
          "ecr:ListTagsForResource",
          "ecr:DescribeImageScanFindings"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "backend_instance_profile" {
  name = "${var.project_name}-backend-instance-profile"
  role = aws_iam_role.backend_instance_role.name
}


# ============================================
# COGNITO USER AUTHENTICATION
# ============================================

# Random string for Cognito domain uniqueness
resource "random_string" "cognito_domain" {
  length  = 8
  special = false
  upper   = false
}

# Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-user-pool"

  # Password policy
  password_policy {
    minimum_length                   = var.cognito_password_minimum_length
    require_lowercase                = var.cognito_password_require_lowercase
    require_uppercase                = var.cognito_password_require_uppercase
    require_numbers                  = var.cognito_password_require_numbers
    require_symbols                  = var.cognito_password_require_symbols
    temporary_password_validity_days = 7
  }

  # User attributes
  auto_verified_attributes = var.cognito_auto_verified_attributes

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # MFA configuration
  mfa_configuration = var.cognito_mfa_configuration

  # User attribute update settings
  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }

  # Username attributes
  username_attributes = var.cognito_username_attributes

  tags = {
    Name        = "${var.project_name}-user-pool"
    Environment = var.environment
  }
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.project_name}-app-client"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret                      = false
  refresh_token_validity               = var.cognito_refresh_token_validity
  access_token_validity                = var.cognito_access_token_validity
  id_token_validity                    = var.cognito_id_token_validity
  token_validity_units {
    refresh_token = "days"
    access_token  = "hours"
    id_token      = "hours"
  }

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  supported_identity_providers = ["COGNITO"]

  callback_urls = [
    "http://localhost:3000/studio",
    "https://www.${var.app_domain}/studio"
  ]
  
  logout_urls = [
    "http://localhost:3000/",
    "https://www.${var.app_domain}/"
  ]

  allowed_oauth_flows_user_pool_client = var.cognito_enable_oauth
  allowed_oauth_flows                  = var.cognito_enable_oauth ? ["code"] : []
  allowed_oauth_scopes                 = var.cognito_enable_oauth ? ["email", "openid", "profile"] : []

  prevent_user_existence_errors = "ENABLED"

  read_attributes  = var.cognito_read_attributes
  write_attributes = var.cognito_write_attributes
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = lower("${var.project_name}-${var.environment}-${random_string.cognito_domain.result}")
  user_pool_id = aws_cognito_user_pool.main.id
}