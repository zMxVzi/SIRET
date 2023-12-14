provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "integradora" {
  cidr_block             = "10.0.0.0/16"
  enable_dns_support     = true
  enable_dns_hostnames   = true

  tags = {
    Name = "integradora-vpc"
  }
}

resource "aws_subnet" "public1" {
  vpc_id                  = aws_vpc.integradora.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public1-subnet"
  }
}

resource "aws_subnet" "public2" {
  vpc_id                  = aws_vpc.integradora.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "public2-subnet"
  }
}

resource "aws_internet_gateway" "integradora" {
  vpc_id = aws_vpc.integradora.id

  tags = {
    Name = "integradora-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.integradora.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.integradora.id
  }

  tags = {
    Name = "public-route-table"
  }
}

resource "aws_route_table_association" "public1" {
  subnet_id      = aws_subnet.public1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public2" {
  subnet_id      = aws_subnet.public2.id
  route_table_id = aws_route_table.public.id
}

resource "aws_eip" "integradora" {}

resource "aws_nat_gateway" "integradora" {
  allocation_id = aws_eip.integradora.id
  subnet_id     = aws_subnet.public1.id

  tags = {
    Name = "integradora-nat-gateway"
  }
}

resource "aws_security_group" "autoescalado_sg" {
  name        = "public-security-group"
  description = "Grupo de seguridad para autoescalado-siret"
  vpc_id      = aws_vpc.integradora.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 22
    to_port     = 22
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
    Name = "public-security-group"
  }
}

resource "aws_launch_configuration" "integradora" {
  name            = "autoescalado-siscon-config_v2"
  image_id        = "ami-0230bd60aa48260c6"
  instance_type   = "t2.micro"
  security_groups = [aws_security_group.autoescalado_sg.id]
  
  user_data = <<-EOF
    #!/bin/bash
    sudo yum update -y
    sudo amazon-linux-extras install python3 -y
    sudo yum install python3-pip -y
    pip3 install flask gunicorn
    sudo yum install git -y
    git clone https://github.com/zMxVzi/SIRET
    cd SIRET/
    pip3 install -r requirements.txt
    nohup gunicorn -w 2 -b 0.0.0.0:8000 run:app > /dev/null 2>&1 &
  EOF  

  lifecycle {
    create_before_destroy = true
  }
}


resource "aws_lb" "integradora" {
  name               = "integradora-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups = [aws_security_group.autoescalado_sg.id]

  enable_deletion_protection = false
  subnets                    = [aws_subnet.public1.id, aws_subnet.public2.id]
  enable_http2               = true
  idle_timeout               = 60
  enable_cross_zone_load_balancing = true
}

resource "aws_lb_target_group" "integradora" {
  name     = "integradora-target-group"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.integradora.id
}

resource "aws_lb_listener" "mi_listener" {
  load_balancer_arn = aws_lb.integradora.arn
  port              = 8000
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.integradora.arn
  }
}


resource "aws_autoscaling_group" "integradora" {
  desired_capacity          = 1
  max_size                  = 3
  min_size                  = 1
  health_check_type         = "EC2"
  health_check_grace_period = 300
  force_delete              = true

  vpc_zone_identifier = [
    aws_subnet.public1.id
  ]

  launch_configuration = aws_launch_configuration.integradora.id

  tag {
    key                 = "Name"
    value               = "integradora-instance"
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_attachment" "integradora" {
  autoscaling_group_name = aws_autoscaling_group.integradora.name
  lb_target_group_arn    = aws_lb_target_group.integradora.arn
}



