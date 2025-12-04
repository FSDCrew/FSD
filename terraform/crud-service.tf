# ============================================
# CRUD SERVICE
# Auto Scaling Group, Launch Template
# ============================================

# Launch Template for CRUD Service
resource "aws_launch_template" "crud_service" {
  name_prefix   = "${var.project_name}-crud-"
  image_id      = data.aws_ami.amazon_linux_2023.id
  instance_type = var.crud_service_instance_type

  vpc_security_group_ids = [aws_security_group.microservices.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.backend_instance_profile.name
  }

  user_data = base64encode(<<-EOT
    #!/bin/bash
    # 1. Redirect output to a log file for debugging
    exec > >(tee /var/log/user-data.log|logger -t user-data -s) 2>&1

    echo "Starting User Data Script..."

    # 2. Install and Configure Docker
    yum update -y
    yum install docker -y
    systemctl enable docker
    systemctl start docker

    # 3. Add users to group (allows ssm-user to debug later without sudo)
    usermod -a -G docker ec2-user
    usermod -a -G docker ssm-user

    # 4. Login to ECR
    ECR_REGISTRY_URL="${aws_ecr_repository.crud_service.repository_url}"
    AWS_ACCOUNT_ID="${data.aws_caller_identity.user.account_id}"
    AWS_REGION="${var.aws_region}"

    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

    # 5. Pull the Image
    docker pull $ECR_REGISTRY_URL:latest

    # 6. Run the Container
    docker run -d \
      -p ${var.crew_service_port}:${var.crew_service_port} \
      --name crud-service-container \
      --restart always \
      -e CREW_SERVICE_URL=https://crew-api.${var.app_domain} \
      -e DB_HOST=${var.db_host} \
      -e DB_PORT=${var.db_port} \
      -e DB_NAME=${var.db_name} \
      -e DB_USER=${var.db_user} \
      -e DB_PASSWORD=${var.db_password} \
      -e COGNITO_REGION=${var.aws_region} \
      -e COGNITO_USER_POOL_ID=${aws_cognito_user_pool.main.id} \
      -e COGNITO_APP_CLIENT_ID=${aws_cognito_user_pool_client.main.id} \
      -e S3_REGION=${var.aws_region} \
      -e S3_BUCKET_NAME=${aws_s3_bucket.main.bucket} \
      -e FRONTEND_ORIGIN=https://www.${var.app_domain} \
      $ECR_REGISTRY_URL:latest

    echo "User Data Script Finished!"
    EOT
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.project_name}-crud-service"
      Environment = var.environment
      Service     = "crud-service"
    }
  }

  tags = {
    Name        = "${var.project_name}-crud-launch-template"
    Environment = var.environment
    Service     = "crud-service"
  }
}

# Auto Scaling Group for CRUD Service
resource "aws_autoscaling_group" "crud_service" {
  name                      = "${var.project_name}-crud-asg"
  vpc_zone_identifier       = aws_subnet.public[*].id
  target_group_arns         = [aws_lb_target_group.crud_service.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 300
  default_cooldown          = 150

  min_size         = var.crud_service_min_size
  max_size         = var.crud_service_max_size
  desired_capacity = var.crud_service_desired_capacity

  launch_template {
    id      = aws_launch_template.crud_service.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-crud-service"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "Service"
    value               = "crud-service"
    propagate_at_launch = true
  }
}

# Target Tracking Scaling Policy - CPU Utilization
resource "aws_autoscaling_policy" "crud_service_cpu" {
  name                   = "${var.project_name}-crud-cpu-scaling-policy"
  autoscaling_group_name = aws_autoscaling_group.crud_service.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}


# ============================================
# ECR REPOSITORIES
# ============================================

# ECR Repository for CRUD Service
resource "aws_ecr_repository" "crud_service" {
  name                 = lower("${var.project_name}-crud-service")
  image_tag_mutability = var.ecr_image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.ecr_scan_on_push
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "${var.project_name}-crud-service"
    Environment = var.environment
    Service     = "crud-service"
  }
}

# ECR Lifecycle Policy for CRUD Service
resource "aws_ecr_lifecycle_policy" "crud_service" {
  repository = aws_ecr_repository.crud_service.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.ecr_image_count_limit} images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = var.ecr_image_count_limit
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}