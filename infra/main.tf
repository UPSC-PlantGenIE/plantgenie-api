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

resource "openstack_networking_secgroup_rule_v2" "neo4j_browser" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 7474
  port_range_max    = 7474
  remote_ip_prefix  = "130.239.0.0/16"
  security_group_id = openstack_networking_secgroup_v2.external_traffic.id
}

resource "openstack_networking_secgroup_rule_v2" "neo4j_bolt" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 7687
  port_range_max    = 7687
  remote_ip_prefix  = "130.239.0.0/16"
  security_group_id = openstack_networking_secgroup_v2.external_traffic.id
}

resource "openstack_networking_secgroup_rule_v2" "rabbitmq_management" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 15672
  port_range_max    = 15672
  remote_ip_prefix  = "130.239.0.0/16"
  security_group_id = openstack_networking_secgroup_v2.external_traffic.id
}

resource "openstack_networking_secgroup_rule_v2" "fastapi" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 8000
  port_range_max    = 8000
  remote_ip_prefix  = "130.239.0.0/16"
  security_group_id = openstack_networking_secgroup_v2.external_traffic.id
}

resource "openstack_networking_secgroup_v2" "internal_traffic" {
  name        = "${terraform.workspace}-${var.application_name}-internal"
  description = "security group for ssh and private network access"
}

resource "openstack_networking_secgroup_rule_v2" "allow_internal" {
  direction = "ingress"
  ethertype = "IPv4"
  protocol  = "tcp"
  # 0 allows all ports and doesn't cause destroy+recreate on new apply
  port_range_min    = 0
  port_range_max    = 0
  security_group_id = openstack_networking_secgroup_v2.internal_traffic.id
  # all VMs with this security group attached will be able to talk to one another
  remote_group_id = openstack_networking_secgroup_v2.internal_traffic.id
}

resource "openstack_identity_application_credential_v3" "api" {
  name        = "${terraform.workspace}-${var.application_name}-api"
  description = "Read-only application credential for the FastAPI backend"

  dynamic "access_rules" {
    for_each = toset(["GET", "HEAD"])
    content {
      service = "object-store"
      method  = access_rules.key
      path    = "/v1/AUTH_*"
    }
  }

  dynamic "access_rules" {
    for_each = toset(["GET", "HEAD"])
    content {
      service = "object-store"
      method  = access_rules.key
      path    = "/v1/AUTH_*/**"
    }
  }
}

resource "openstack_identity_application_credential_v3" "celery" {
  name        = "${terraform.workspace}-${var.application_name}-celery"
  description = "Application credential for the celery worker"

  dynamic "access_rules" {
    for_each = toset(["GET", "PUT", "POST", "DELETE", "HEAD"])
    content {
      service = "object-store"
      method  = access_rules.key
      path    = "/v1/AUTH_*"
    }
  }

  dynamic "access_rules" {
    for_each = toset(["GET", "PUT", "POST", "DELETE", "HEAD"])
    content {
      service = "object-store"
      method  = access_rules.key
      path    = "/v1/AUTH_*/**"
    }
  }
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
    openstack_networking_secgroup_v2.external_traffic.id,
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
  flavor_name           = "ssc.small"
  server_username       = var.server_username
  ssh_keypair_name      = openstack_compute_keypair_v2.ssh.name
  ssh_public_key        = tls_private_key.ssh.public_key_openssh
  internal_port_id      = openstack_networking_port_v2.web_proxy.id
  external_network_name = data.openstack_networking_network_v2.external.name
  storage_size          = var.nfs_storage_size
  internal_subnet_cidr  = data.openstack_networking_subnet_v2.internal.cidr
  neo4j_internal_ip     = openstack_networking_port_v2.neo4j.all_fixed_ips[0]
  rabbitmq_internal_ip    = openstack_networking_port_v2.rabbitmq.all_fixed_ips[0]
  application_internal_ip = openstack_networking_port_v2.application.all_fixed_ips[0]
}

module "neo4j" {
  source = "./modules/neo4j"

  workspace        = terraform.workspace
  application_name = var.application_name
  base_image_name  = var.base_image_name
  flavor_name      = "ssc.small"
  server_username  = var.server_username
  ssh_keypair_name = openstack_compute_keypair_v2.ssh.name
  ssh_public_key   = tls_private_key.ssh.public_key_openssh
  internal_port_id = openstack_networking_port_v2.neo4j.id
  nfs_server_ip    = openstack_networking_port_v2.web_proxy.all_fixed_ips[0]
  storage_size     = var.neo4j_storage_size
  neo4j_username   = var.neo4j_username
  neo4j_password   = var.neo4j_password
}

module "application" {
  source = "./modules/application"

  workspace                        = terraform.workspace
  application_name                 = var.application_name
  base_image_name                  = var.base_image_name
  flavor_name                      = "ssc.xsmall"
  server_username                  = var.server_username
  ssh_keypair_name                 = openstack_compute_keypair_v2.ssh.name
  ssh_public_key                   = tls_private_key.ssh.public_key_openssh
  internal_port_id                 = openstack_networking_port_v2.application.id
  nfs_server_ip                    = openstack_networking_port_v2.web_proxy.all_fixed_ips[0]
  github_pat                       = var.github_pat
  github_username                  = var.github_username
  rabbitmq_username                = var.rabbitmq_username
  rabbitmq_password                = var.rabbitmq_password
  rabbitmq_internal_ip             = openstack_networking_port_v2.rabbitmq.all_fixed_ips[0]
  redis_internal_ip                = openstack_networking_port_v2.redis.all_fixed_ips[0]
  os_auth_url                      = var.os_auth_url
  os_region_name                   = var.os_region_name
  os_application_credential_id     = openstack_identity_application_credential_v3.api.id
  os_application_credential_secret = openstack_identity_application_credential_v3.api.secret
  fastapi_image_tag                = var.fastapi_image_tag
}

module "rabbitmq" {
  source = "./modules/rabbitmq"

  workspace         = terraform.workspace
  application_name  = var.application_name
  base_image_name   = var.base_image_name
  flavor_name       = "ssc.xsmall"
  server_username   = var.server_username
  ssh_keypair_name  = openstack_compute_keypair_v2.ssh.name
  ssh_public_key    = tls_private_key.ssh.public_key_openssh
  internal_port_id  = openstack_networking_port_v2.rabbitmq.id
  rabbitmq_username = var.rabbitmq_username
  rabbitmq_password = var.rabbitmq_password
}

module "redis" {
  source = "./modules/redis"

  workspace        = terraform.workspace
  application_name = var.application_name
  base_image_name  = var.base_image_name
  flavor_name      = "ssc.xsmall"
  server_username  = var.server_username
  ssh_keypair_name = openstack_compute_keypair_v2.ssh.name
  ssh_public_key   = tls_private_key.ssh.public_key_openssh
  internal_port_id = openstack_networking_port_v2.redis.id
}

module "queue" {
  source = "./modules/queue"

  workspace                        = terraform.workspace
  application_name                 = var.application_name
  base_image_name                  = var.base_image_name
  flavor_name                      = "ssc.small"
  server_username                  = var.server_username
  ssh_keypair_name                 = openstack_compute_keypair_v2.ssh.name
  ssh_public_key                   = tls_private_key.ssh.public_key_openssh
  internal_port_id                 = openstack_networking_port_v2.queue.id
  nfs_server_ip                    = openstack_networking_port_v2.web_proxy.all_fixed_ips[0]
  github_pat                       = var.github_pat
  github_username                  = var.github_username
  rabbitmq_username                = var.rabbitmq_username
  rabbitmq_password                = var.rabbitmq_password
  rabbitmq_internal_ip             = openstack_networking_port_v2.rabbitmq.all_fixed_ips[0]
  redis_internal_ip                = openstack_networking_port_v2.redis.all_fixed_ips[0]
  os_auth_url                      = var.os_auth_url
  os_region_name                   = var.os_region_name
  os_application_credential_id     = openstack_identity_application_credential_v3.celery.id
  os_application_credential_secret = openstack_identity_application_credential_v3.celery.secret
  celery_worker_image_tag          = var.celery_worker_image_tag
}
