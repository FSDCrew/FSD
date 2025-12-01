variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-southeast-2"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "project_name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (e.g., prod, staging, dr)"
  type        = string
  default     = "prod"
}

variable "app_domain" {
  description = "App domain name (e.g., campaign.ongspace.com)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b"]
}


# ============================================
# SUPABASE Configuration
# ============================================

variable "db_host" {
  description = "Hostname for the Supabase database pooler"
  type        = string
}

variable "db_port" {
  description = "Port number for the Supabase database"
  type        = number
  default     = 5432
}

variable "db_name" {
  description = "Supabase database name"
  type        = string
}

variable "db_user" {
  description = "Supabase database user"
  type        = string
}

variable "db_password" {
  description = "Password for the database user"
  type        = string
  sensitive   = true
}


# ============================================
# CRUD SERVICE (Microservice 1) Configuration
# ============================================

variable "crud_service_instance_type" {
  description = "Instance type for CRUD service"
  type        = string
  default     = "t3.micro"
}

variable "crud_service_min_size" {
  description = "Minimum number of instances for CRUD service"
  type        = number
  default     = 1
}

variable "crud_service_max_size" {
  description = "Maximum number of instances for CRUD service"
  type        = number
  default     = 4
}

variable "crud_service_desired_capacity" {
  description = "Desired number of instances for CRUD service"
  type        = number
  default     = 2
}

variable "crud_service_port" {
  description = "Port for CRUD service"
  type        = number
  default     = 6010
}

variable "crud_service_health_check_path" {
  description = "Health check path for CRUD service"
  type        = string
  default     = "/status/health"
}


# ============================================
# CREW SERVICE (Microservice 2) Configuration
# ============================================

variable "crew_service_instance_type" {
  description = "Instance type for Crew service"
  type        = string
  default     = "t3.small"
}

variable "crew_service_min_size" {
  description = "Minimum number of instances for Crew service"
  type        = number
  default     = 1
}

variable "crew_service_max_size" {
  description = "Maximum number of instances for Crew service"
  type        = number
  default     = 4
}

variable "crew_service_desired_capacity" {
  description = "Desired number of instances for Crew service"
  type        = number
  default     = 2
}

variable "crew_service_port" {
  description = "Port for Crew service"
  type        = number
  default     = 6011
}

variable "crew_service_health_check_path" {
  description = "Health check path for Crew service"
  type        = string
  default     = "/status/health"
}


# ============================================
# CREW SERVICE CONFIGURATION VARIABLES
# ============================================

variable "internal_crew_api_key" {
  description = "Internal API key for authenticating requests between CRUD and Crew services"
  type        = string
  sensitive   = true
}

variable "queue_poll_interval_seconds" {
  description = "Interval in seconds for polling the job queue"
  type        = number
  default     = 5
}

variable "job_visibility_timeout_seconds" {
  description = "Visibility timeout in seconds for jobs in the queue"
  type        = number
  default     = 300
}

variable "heartbeat_interval_seconds" {
  description = "Interval in seconds for sending heartbeat signals"
  type        = number
  default     = 60
}

variable "openai_api_key" {
  description = "OpenAI API key for GPT model access"
  type        = string
  sensitive   = true
}

variable "headless" {
  description = "Run browser in headless mode (True/False)"
  type        = string
  default     = "True"
}

variable "bright_data_api_key" {
  description = "Bright Data API key for proxy/scraping services"
  type        = string
  sensitive   = true
}

variable "bright_data_zone" {
  description = "Bright Data zone identifier"
  type        = string
  default     = "serp_api1"
}

variable "orshot_api_key" {
   description = "Orshot API key"
  type        = string
}

variable "orshot_api_url" {
  description = "Orshot API URL"
  type        = string
}

# ============================================
# AWS AMPLIFY Configuration
# ============================================

variable "amplify_repository" {
  description = "GitHub repository URL for Amplify"
  type        = string
}

variable "amplify_github_token" {
  description = "GitHub personal access token for Amplify"
  type        = string
  sensitive   = true
}

variable "amplify_branch_name" {
  description = "Branch name to deploy in Amplify"
  type        = string
  default     = "main"
}

variable "amplify_build_spec" {
  description = "Build specification for Amplify"
  type        = string
  default     = <<-EOT
    version: 1
    appRoot: frontend
    frontend:
      phases:
        preBuild:
          commands:
            - rm -rf node_modules
            - rm -f package-lock.json
            - npm cache clean --force
            - nvm install 20.19.0 
            - nvm use 20.19.0
            - node -v
            - 'echo "Starting build from: $PWD"'
            - npm install
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: out
        files:
          - "**/*"
      cache:
        paths:
          - .next/cache/**/*
  EOT
}


# ============================================
# COGNITO Configuration
# ============================================

variable "cognito_password_minimum_length" {
  description = "Minimum length for user passwords"
  type        = number
  default     = 8
}

variable "cognito_password_require_lowercase" {
  description = "Require lowercase characters in password"
  type        = bool
  default     = true
}

variable "cognito_password_require_uppercase" {
  description = "Require uppercase characters in password"
  type        = bool
  default     = true
}

variable "cognito_password_require_numbers" {
  description = "Require numbers in password"
  type        = bool
  default     = true
}

variable "cognito_password_require_symbols" {
  description = "Require symbols in password"
  type        = bool
  default     = true
}

variable "cognito_auto_verified_attributes" {
  description = "Attributes to auto-verify (email, phone_number)"
  type        = list(string)
  default     = ["email"]
}

variable "cognito_mfa_configuration" {
  description = "MFA configuration (OFF, ON, OPTIONAL)"
  type        = string
  default     = "OFF"
}

variable "cognito_username_attributes" {
  description = "Attributes that can be used as username (email, phone_number)"
  type        = list(string)
  default     = ["email"]
}

variable "cognito_refresh_token_validity" {
  description = "Refresh token validity in days"
  type        = number
  default     = 30
}

variable "cognito_access_token_validity" {
  description = "Access token validity in hours"
  type        = number
  default     = 1
}

variable "cognito_id_token_validity" {
  description = "ID token validity in hours"
  type        = number
  default     = 1
}

variable "cognito_callback_urls" {
  description = "List of allowed callback URLs"
  type        = list(string)
  default     = ["http://localhost:3000/studio", "https://www.campaign.ongspace.com/studio"]
}

variable "cognito_logout_urls" {
  description = "List of allowed logout URLs"
  type        = list(string)
  default     = ["http://localhost:3000/", "https://www.campaign.ongspace.com/"]
}

variable "cognito_enable_oauth" {
  description = "Enable OAuth flows"
  type        = bool
  default     = true
}

variable "cognito_custom_domain" {
  description = "Custom domain for Cognito (leave empty for AWS-managed domain)"
  type        = string
  default     = ""
}

variable "cognito_read_attributes" {
  description = "List of attributes the app client can read"
  type        = list(string)
  default     = ["email", "email_verified", "name", "family_name", "given_name", "picture"]
}

variable "cognito_write_attributes" {
  description = "List of attributes the app client can write"
  type        = list(string)
  default     = ["email", "name", "family_name", "given_name", "picture"]
}


# ============================================
# ECR Configuration
# ============================================

variable "ecr_image_tag_mutability" {
  description = "Image tag mutability setting (MUTABLE or IMMUTABLE)"
  type        = string
  default     = "MUTABLE"
}

variable "ecr_scan_on_push" {
  description = "Enable image scanning on push"
  type        = bool
  default     = true
}

variable "ecr_image_count_limit" {
  description = "Number of images to retain in ECR"
  type        = number
  default     = 10
}
