provider "aws" {
  region = "us-east-1"
}

# Recursos para la VPC, subredes, Internet Gateway, y tablas de ruteo
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
  availability_zone       = "us-east-1a"  # Cambia según tu disponibilidad
  map_public_ip_on_launch = true

  tags = {
    Name = "public1-subnet"
  }
}

resource "aws_subnet" "public2" {
  vpc_id                  = aws_vpc.integradora.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"  # Cambia según tu disponibilidad
  map_public_ip_on_launch = true

  tags = {
    Name = "public2-subnet"
  }
}

resource "aws_subnet" "private1" {
  vpc_id                  = aws_vpc.integradora.id
  cidr_block              = "10.0.3.0/24"
  availability_zone       = "us-east-1a"  # Cambia según tu disponibilidad

  tags = {
    Name = "private1-subnet"
  }
}

resource "aws_subnet" "private2" {
  vpc_id                  = aws_vpc.integradora.id
  cidr_block              = "10.0.4.0/24"
  availability_zone       = "us-east-1b"  # Cambia según tu disponibilidad

  tags = {
    Name = "private2-subnet"
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

# Recursos para los Grupos de Seguridad
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

resource "aws_security_group" "rds_sg" {
  name        = "rds-security-group"
  description = "Grupo de seguridad para rds"
  vpc_id      = aws_vpc.integradora.id

  ingress {
    from_port        = 3306
    to_port          = 3306
    protocol         = "tcp"
    security_groups  = [aws_security_group.autoescalado_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rds-security-group"
  }
}


resource "aws_launch_configuration" "integradora" {
  name            = "autoescalado-siscon-config"
  image_id        = "ami-0ec0e428fa292fc5c"
  instance_type   = "t2.micro"
  security_groups = [aws_security_group.autoescalado_sg.id]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "integradora" {
  desired_capacity          = 2
  max_size                  = 4
  min_size                  = 2
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

resource "aws_lb" "integradora" {
  name               = "integradora-lb"
  internal           = false # Cambia a true si deseas un LB interno
  load_balancer_type = "application"

  enable_deletion_protection = false # Ajusta según tus necesidades

  subnets = [aws_subnet.public1.id, aws_subnet.public2.id] # Reemplaza con tus subnets

  enable_http2 = true # Habilita HTTP/2
  idle_timeout = 60   # Ajusta según tus necesidades

  enable_cross_zone_load_balancing = true # Distribuir el tráfico de forma uniforme entre las instancias
}
# Crear un grupo objetivo para el ALB
resource "aws_lb_target_group" "example" {
  name     = "example-target-group"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.integradora.id
}

resource "aws_autoscaling_attachment" "integradora" {
  autoscaling_group_name = aws_autoscaling_group.integradora.name
  lb_target_group_arn    = aws_lb_target_group.example.arn # Usa lb_target_group_arn en lugar de alb_target_group_arn
}