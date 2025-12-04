# ============================================
# CREW SERVICE
# Auto Scaling Group, Launch Template
# ============================================

# Launch Template for Crew Service
resource "aws_launch_template" "crew_service" {
  name_prefix   = "${var.project_name}-crew-"
  image_id      = data.aws_ami.amazon_linux_2023.id
  instance_type = var.crew_service_instance_type

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
    ECR_REGISTRY_URL="${aws_ecr_repository.crew_service.repository_url}"
    AWS_ACCOUNT_ID="${data.aws_caller_identity.user.account_id}"
    AWS_REGION="${var.aws_region}"

    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

    # 5. Pull the Image
    docker pull $ECR_REGISTRY_URL:latest

    # 6. Run the Container
    docker run -d \
      -p ${var.crew_service_port}:${var.crew_service_port} \
      --name crew-service-container \
      --restart always \
      -e CRUD_SERVICE_URL=https://crud-api.${var.app_domain} \
      -e INTERNAL_CREW_API_KEY=${var.internal_crew_api_key} \
      -e QUEUE_POLL_INTERVAL_SECONDS=${var.queue_poll_interval_seconds} \
      -e JOB_VISIBILITY_TIMEOUT_SECONDS=${var.job_visibility_timeout_seconds} \
      -e HEARTBEAT_INTERVAL_SECONDS=${var.heartbeat_interval_seconds} \
      -e OPENAI_API_KEY=${var.openai_api_key} \
      -e HEADLESS=${var.headless} \
      -e PLAYWRIGHT_TIMEOUT_MS=${var.playwright_timeout_ms} \
      -e BRIGHT_DATA_API_KEY=${var.bright_data_api_key} \
      -e BRIGHT_DATA_ZONE=${var.bright_data_zone} \
      -e ORSHOT_API_KEY=${var.orshot_api_key} \
      -e ORSHOT_API_URL=${var.orshot_api_url} \
      -e ORSHOT_MOCK_MODE=${var.orshot_mock_mode} \
      -e GEMINI_API_KEY=${var.gemini_api_key} \
      $ECR_REGISTRY_URL:latest

    echo "User Data Script Finished!"
    EOT
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.project_name}-crew-service"
      Environment = var.environment
      Service     = "crew-service"
    }
  }

  tags = {
    Name        = "${var.project_name}-crew-launch-template"
    Environment = var.environment
    Service     = "crew-service"
  }
}

# Auto Scaling Group for Crew Service
resource "aws_autoscaling_group" "crew_service" {
  name                = "${var.project_name}-crew-asg"
  vpc_zone_identifier = aws_subnet.public[*].id
  target_group_arns   = [aws_lb_target_group.crew_service.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = var.crew_service_min_size
  max_size         = var.crew_service_max_size
  desired_capacity = var.crew_service_desired_capacity

  launch_template {
    id      = aws_launch_template.crew_service.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-crew-service"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "Service"
    value               = "crew-service"
    propagate_at_launch = true
  }
}


# ============================================
# ECR REPOSITORIES
# ============================================

# ECR Repository for Crew Service
resource "aws_ecr_repository" "crew_service" {
  name                 = lower("${var.project_name}-crew-service")
  image_tag_mutability = var.ecr_image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.ecr_scan_on_push
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "${var.project_name}-crew-service"
    Environment = var.environment
    Service     = "crew-service"
  }
}

# ECR Lifecycle Policy for Crew Service
resource "aws_ecr_lifecycle_policy" "crew_service" {
  repository = aws_ecr_repository.crew_service.name

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
