output "aws_region" {
  description = "AWS Deployment Region"
  value       = var.aws_region
}

# ============================================
# NETWORKING OUTPUTS
# ============================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "crud_api_public_url" {
  description = "Public URL for CRUD API"
  value       = "https://crud-api.${var.app_domain}"
}

output "crew_api_public_url" {
  description = "Public URL for Crew API"
  value       = "https://crew-api.${var.app_domain}"
}

output "crud_api_private_url" {
  description = "Private URL for CRUD API (VPC internal)"
  value       = "https://crud-api.${var.app_domain}"
}

output "crew_api_private_url" {
  description = "Private URL for Crew API (VPC internal)"
  value       = "https://crew-api.${var.app_domain}"
}

output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate.alb.arn
}

output "private_hosted_zone_id" {
  description = "ID of the private hosted zone"
  value       = aws_route53_zone.private.zone_id
}


# ============================================
# MICROSERVICES OUTPUTS
# ============================================

output "crud_service_asg_name" {
  description = "Name of the Auto Scaling Group for CRUD service"
  value       = aws_autoscaling_group.crud_service.name
}

output "crew_service_asg_name" {
  description = "Name of the Auto Scaling Group for Crew service"
  value       = aws_autoscaling_group.crew_service.name
}


# ============================================
# FRONTEND OUTPUTS
# ============================================

output "amplify_app_id" {
  description = "ID of the Amplify app"
  value       = aws_amplify_app.frontend.id
}

output "amplify_default_domain" {
  description = "Default domain of the Amplify app"
  value       = aws_amplify_app.frontend.default_domain
}

output "amplify_branch_url" {
  description = "URL of the Amplify branch"
  value       = "https://${var.amplify_branch_name}.${aws_amplify_app.frontend.default_domain}"
}

output "amplify_custom_domain_url" {
  description = "Custom domain URL"
  value       = "https://${var.app_domain}"
}

output "amplify_domain_status" {
  description = "Status of the custom domain"
  value       = aws_amplify_domain_association.main.certificate_verification_dns_record
}


# ============================================
# COGNITO OUTPUTS
# ============================================

output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.arn
}

output "cognito_user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.endpoint
}

output "cognito_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.main.id
}

output "cognito_domain" {
  description = "Cognito User Pool domain"
  value       = aws_cognito_user_pool_domain.main.domain
}

output "cognito_hosted_ui_url" {
  description = "Cognito Hosted UI URL"
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
}


# ============================================
# ECR OUTPUTS
# ============================================

output "ecr_repository_url_crud_service" {
  description = "URL of ECR repository for CRUD service"
  value       = aws_ecr_repository.crud_service.repository_url
}

output "ecr_repository_arn_crud_service" {
  description = "ARN of ECR repository for CRUD service"
  value       = aws_ecr_repository.crud_service.arn
}

output "ecr_repository_name_crud_service" {
  description = "Name of ECR repository for CRUD service"
  value       = aws_ecr_repository.crud_service.name
}

output "ecr_repository_url_crew_service" {
  description = "URL of ECR repository for Crew service"
  value       = aws_ecr_repository.crew_service.repository_url
}

output "ecr_repository_arn_crew_service" {
  description = "ARN of ECR repository for Crew service"
  value       = aws_ecr_repository.crew_service.arn
}

output "ecr_repository_name_crew_service" {
  description = "ARN of ECR repository for Crew service"
  value       = aws_ecr_repository.crew_service.name
}


# ============================================
# S3 OUTPUTS
# ============================================

output "bucket_name" {
  description = "The name of the S3 bucket"
  value       = aws_s3_bucket.main.bucket
}