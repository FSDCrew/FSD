# ============================================
# FRONTEND - AWS AMPLIFY
# Amplify App and Branch Configuration
# ============================================

# AWS Amplify App
resource "aws_amplify_app" "frontend" {
  name       = lower("${var.project_name}-frontend")
  repository = var.amplify_repository

  access_token = var.amplify_github_token

  build_spec = var.amplify_build_spec

  environment_variables = {
    NEXT_PUBLIC_CRUD_API_BASE_URL    = aws_lb.main.dns_name
    NEXT_PUBLIC_COGNITO_USER_POOL_ID = aws_cognito_user_pool.main.id
    NEXT_PUBLIC_COGNITO_CLIENT_ID    = aws_cognito_user_pool_client.main.id
    NEXT_PUBLIC_COGNITO_DOMAIN       = "${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
  }


  custom_rule {
    source = "https://${var.app_domain}"
    status = "302"
    target = "https://www.${var.app_domain}"
  }


  custom_rule {
    source = "</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|ttf|map|json)$)([^.]+$)/>"
    status = "200"
    target = "/index.html"
  }

  tags = {
    Name        = "${var.project_name}-frontend"
    Environment = var.environment
  }
}

# Amplify Branch
resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.frontend.id
  branch_name = var.amplify_branch_name

  enable_auto_build = true

  environment_variables = {
    API_ENDPOINT = aws_lb.main.dns_name
  }

  tags = {
    Name        = "${var.project_name}-frontend-${var.amplify_branch_name}"
    Environment = var.environment
  }
}

# Domain Association
resource "aws_amplify_domain_association" "main" {
  app_id      = aws_amplify_app.frontend.id
  domain_name = var.app_domain

  enable_auto_sub_domain = true
  wait_for_verification  = true

  # Root domain
  sub_domain {
    branch_name = aws_amplify_branch.main.branch_name
    prefix      = ""
  }

  # www subdomain
  sub_domain {
    branch_name = aws_amplify_branch.main.branch_name
    prefix      = "www"
  }
}
