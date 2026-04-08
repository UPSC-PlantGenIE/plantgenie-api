terraform {
  required_version = ">= 1.14"

  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 3.2.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.1.0"
    }
  }

  cloud {
    organization = "upsc-plantgenie"
    # workspaces {
    #   name = "north-dev"
    # }
    workspaces {
      tags = [ "plantgenie" ]
    }
  }
}

data "openstack_networking_network_v2" "external" {
  name = var.external_network_name
}

data "openstack_networking_network_v2" "internal" {
  name = var.internal_network_name
}

data "openstack_networking_subnet_v2" "internal" {
  network_id = data.openstack_networking_network_v2.internal.id
  ip_version = 4
}

resource "openstack_networking_secgroup_v2" "external_traffic" {
  name        = "${terraform.workspace}-${var.application_name}-external"
  description = "security group for web proxy instance"
}

resource "openstack_networking_secgroup_rule_v2" "external_ssh_traffic" {
  direction = "ingress"
  ethertype = "IPv4"
  protocol  = "tcp"

  port_range_min = 22
  port_range_max = 22

  remote_ip_prefix = "130.239.0.0/16"

  security_group_id = openstack_networking_secgroup_v2.external_traffic.id
}

resource "openstack_networking_secgroup_rule_v2" "external_http_traffic" {
  direction = "ingress"
  ethertype = "IPv4"
  protocol  = "tcp"

  port_range_min = 80
  port_range_max = 80

  remote_ip_prefix = "0.0.0.0/0"

  security_group_id = openstack_networking_secgroup_v2.external_traffic.id
}

resource "openstack_networking_secgroup_rule_v2" "external_https_traffic" {
  direction = "ingress"
  ethertype = "IPv4"
  protocol  = "tcp"

  port_range_min = 443
  port_range_max = 443

  remote_ip_prefix = "0.0.0.0/0"

  security_group_id = openstack_networking_secgroup_v2.external_traffic.id
}

resource "openstack_networking_secgroup_v2" "internal_traffic" {
  name        = "${terraform.workspace}-${var.application_name}-internal"
  description = "security group for ssh and private network access"
}

resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "openstack_compute_keypair_v2" "ssh" {
  name       = "${terraform.workspace}-${var.application_name}-keypair"
  public_key = tls_private_key.ssh.public_key_openssh
}

resource "openstack_networking_port_v2" "web_proxy" {
  name           = "${terraform.workspace}-${var.application_name}-web-proxy-port"
  network_id     = data.openstack_networking_network_v2.internal.id
  admin_state_up = true

  security_group_ids = [
    openstack_networking_secgroup_v2.external_traffic.id,
    openstack_networking_secgroup_v2.internal_traffic.id,
  ]

  fixed_ip {
    subnet_id = data.openstack_networking_subnet_v2.internal.id
  }
}

resource "openstack_networking_port_v2" "application" {
  name           = "${terraform.workspace}-${var.application_name}-application-port"
  network_id     = data.openstack_networking_network_v2.internal.id
  admin_state_up = true

  security_group_ids = [
    openstack_networking_secgroup_v2.internal_traffic.id,
  ]

  fixed_ip {
    subnet_id = data.openstack_networking_subnet_v2.internal.id
  }
}

resource "openstack_networking_port_v2" "queue" {
  name           = "${terraform.workspace}-${var.application_name}-queue-port"
  network_id     = data.openstack_networking_network_v2.internal.id
  admin_state_up = true

  security_group_ids = [
    openstack_networking_secgroup_v2.internal_traffic.id,
  ]

  fixed_ip {
    subnet_id = data.openstack_networking_subnet_v2.internal.id
  }
}

resource "openstack_networking_port_v2" "rabbitmq" {
  name           = "${terraform.workspace}-${var.application_name}-rabbitmq-port"
  network_id     = data.openstack_networking_network_v2.internal.id
  admin_state_up = true

  security_group_ids = [
    openstack_networking_secgroup_v2.internal_traffic.id,
  ]

  fixed_ip {
    subnet_id = data.openstack_networking_subnet_v2.internal.id
  }
}

resource "openstack_networking_port_v2" "redis" {
  name           = "${terraform.workspace}-${var.application_name}-redis-port"
  network_id     = data.openstack_networking_network_v2.internal.id
  admin_state_up = true

  security_group_ids = [
    openstack_networking_secgroup_v2.internal_traffic.id,
  ]

  fixed_ip {
    subnet_id = data.openstack_networking_subnet_v2.internal.id
  }
}

resource "openstack_networking_port_v2" "neo4j" {
  name           = "${terraform.workspace}-${var.application_name}-neo4j-port"
  network_id     = data.openstack_networking_network_v2.internal.id
  admin_state_up = true

  security_group_ids = [
    openstack_networking_secgroup_v2.internal_traffic.id,
  ]

  fixed_ip {
    subnet_id = data.openstack_networking_subnet_v2.internal.id
  }
}

module "nginx" {
  source = "./modules/nginx"

  workspace             = terraform.workspace
  application_name      = var.application_name
  base_image_name       = var.base_image_name
  flavor_name           = "ssc.medium"
  server_username       = var.server_username
  ssh_keypair_name      = openstack_compute_keypair_v2.ssh.name
  ssh_public_key        = tls_private_key.ssh.public_key_openssh
  internal_port_id      = openstack_networking_port_v2.web_proxy.id
  external_network_name = data.openstack_networking_network_v2.external.name
  storage_size          = var.nfs_storage_size
}
