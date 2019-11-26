terraform {
  required_version = ">= 0.12.2"
}

provider "aws" {
  version = ">= 2.28.1"
  region  = local.aws_region
}

provider "local" {
  version = "~> 1.2"
}

locals {
  aws_region         = "us-west-1"
  key_name           = "emr-dev"
  emr_bucket_name    = "emr-airflow"
  emr_bootstrap_path = "scripts/bootstrap.sh"
}

resource "tls_private_key" "example" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "key_priv" {
  content  = tls_private_key.example.private_key_pem
  filename = "${path.module}/id_rsa"
}

resource "local_file" "key_pub" {
  content  = tls_private_key.example.public_key_pem
  filename = "${path.module}/id_rsa.pub"
}

resource "aws_key_pair" "generated_key" {
  key_name   = local.key_name
  public_key = tls_private_key.example.public_key_openssh
}

resource "aws_s3_bucket" "emr_bucket" {
  bucket = local.emr_bucket_name
  acl    = "private"
  region = local.aws_region
}

resource "aws_s3_bucket_object" "bootstrap" {
  bucket = aws_s3_bucket.emr_bucket.id
  key    = local.emr_bootstrap_path
  source = "${path.module}/scripts/bootstrap.sh"
  etag   = "${filemd5("${path.module}/scripts/bootstrap.sh")}"
}

output "ec2_attributes" {
  value = {
    subnet_id                         = aws_subnet.main.id
    emr_managed_master_security_group = aws_security_group.allow_access.id
    emr_managed_slave_security_group  = aws_security_group.allow_access.id
  }
}

resource "aws_security_group" "allow_access" {
  name        = "allow_access"
  description = "Allow inbound traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"

    cidr_blocks = ["0.0.0.0/0"] # open to world for debug/demo
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  depends_on = ["aws_subnet.main"]

  tags = {
    name = "emr_test"
  }
}

resource "aws_vpc" "main" {
  cidr_block           = "168.31.0.0/16"
  enable_dns_hostnames = true

  tags = {
    name = "emr_test"
  }
}

resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "168.31.0.0/20"

  tags = {
    name = "emr_test"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "r" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

resource "aws_main_route_table_association" "a" {
  vpc_id         = aws_vpc.main.id
  route_table_id = aws_route_table.r.id
}
