# ============================================
# NETWORKING CONFIGURATION
# VPC, Subnets, Internet Gateway, Route Tables,
# ============================================

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project_name}-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-igw"
    Environment = var.environment
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-public-subnet-${count.index + 1}"
    Environment = var.environment
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.project_name}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-alb-sg"
    Environment = var.environment
  }
}

# Security Group for Microservices
resource "aws_security_group" "microservices" {
  name        = "${var.project_name}-microservices-sg"
  description = "Security group for microservices"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = var.crud_service_port
    to_port         = var.crud_service_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    from_port       = var.crew_service_port
    to_port         = var.crew_service_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-microservices-sg"
    Environment = var.environment
  }
}


# ============================================
# ROUTE 53
# Split Horizon Hosted Zone,
# ACM SSL Certificate for ALB
# ============================================

# Public Hosted Zone
# - crew-api.campaign.ongspace.com (A Alias Record to ALB)
# - crud-api.campaign.ongspace.com (A Alias Record to ALB)
# - www.campaign.ongspace.com (auto created CNAME record to CF by Amplify)

# Private Hosted Zone
# - crew-api.campaign.ongspace.com (A Alias Record to ALB)
# - crud-api.campaign.ongspace.com (A Alias Record to ALB)

# SSL Certificate
# - *.campaign.ongspace.com

# Private Hosted Zone for Split Horizon DNS
resource "aws_route53_zone" "private" {
  name = var.app_domain

  vpc {
    vpc_id = aws_vpc.main.id
  }

  tags = {
    Name        = "${var.project_name}-private-zone"
    Environment = var.environment
  }
}

# Request ACM SSL Certificate for ALB
resource "aws_acm_certificate" "alb" {
  domain_name       = "*.${var.app_domain}"
  validation_method = "DNS"

  subject_alternative_names = [
    var.app_domain
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.project_name}-alb-cert"
    Environment = var.environment
  }
}

# DNS validation records for ACM certificate in public hosted zone
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.alb.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }

  zone_id = data.aws_route53_zone.public.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60

  allow_overwrite = true
}

# Wait for certificate validation to complete
resource "aws_acm_certificate_validation" "alb" {
  certificate_arn         = aws_acm_certificate.alb.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}


# ============================================
# PUBLIC DNS RECORDS (External Access)
# ============================================

# Public A Record for CRUD API (points to ALB)
resource "aws_route53_record" "crud_api_public" {
  zone_id = data.aws_route53_zone.public.zone_id
  name    = "crud-api.${var.app_domain}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Public A Record for Crew API (points to ALB)
resource "aws_route53_record" "crew_api_public" {
  zone_id = data.aws_route53_zone.public.zone_id
  name    = "crew-api.${var.app_domain}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# ============================================
# PRIVATE DNS RECORDS (Internal VPC Access)
# ============================================

# Private A Record for CRUD API (points to ALB)
resource "aws_route53_record" "crud_api_private" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "crud-api.${var.app_domain}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Private A Record for Crew API (points to ALB)
resource "aws_route53_record" "crew_api_private" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "crew-api.${var.app_domain}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}


# ============================================
# APPLICATION LOAD BALANCER CONFIGURATION
# Target Groups, Listeners
# ============================================

# Application Load Balancer
resource "aws_lb" "main" {
  name               = lower("${var.project_name}-alb")
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name        = "${var.project_name}-alb"
    Environment = var.environment
  }
}

# Target Group for CRUD Service
resource "aws_lb_target_group" "crud_service" {
  name     = lower("${var.project_name}-crud-tg")
  port     = var.crud_service_port
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = var.crud_service_health_check_path
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.project_name}-crud-tg"
    Environment = var.environment
    Service     = "crud-service"
  }
}

# Target Group for Crew Service
resource "aws_lb_target_group" "crew_service" {
  name     = lower("${var.project_name}-crew-tg")
  port     = var.crew_service_port
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = var.crew_service_health_check_path
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.project_name}-crew-tg"
    Environment = var.environment
    Service     = "crew-service"
  }
}

# ALB Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.alb.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.crud_service.arn
  }
}

# HTTP to HTTPS Redirect Listener
resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# Listener Rules for routing
resource "aws_lb_listener_rule" "crud_service" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.crud_service.arn
  }

  condition {
    host_header {
      values = [aws_route53_record.crud_api_public.name]
    }
  }
}

resource "aws_lb_listener_rule" "crew_service" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.crew_service.arn
  }

  condition {
    host_header {
      values = [aws_route53_record.crew_api_public.name]
    }
  }
}