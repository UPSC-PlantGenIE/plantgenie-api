terraform {
  required_providers {
    waldur = {
      source  = "waldur/waldur"
      version = "8.1.3-rc.2"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.1.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

provider "waldur" {
  endpoint = var.waldur_api_url
  token    = var.waldur_access_token
}

data "waldur_openstack_network" "internal" {
  id = "d562b9c5dd2c4fa88f10fa1486ee97b8"
}

locals {
  nginx_pinned_ip       = "192.168.42.11"
  application_pinned_ip = "192.168.42.12"
}

output "internal_network" {
  value = {
    name    = data.waldur_openstack_network.internal.name
    type    = data.waldur_openstack_network.internal.type
    tenant  = data.waldur_openstack_network.internal.tenant_name
    subnets = data.waldur_openstack_network.internal.subnets
  }
}
