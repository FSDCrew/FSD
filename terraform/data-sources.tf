data "aws_caller_identity" "user" {}

# Prerequisite public hosted zone for app domain
data "aws_route53_zone" "public" {
  name         = var.app_domain
  private_zone = false
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}