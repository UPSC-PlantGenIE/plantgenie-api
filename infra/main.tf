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
    workspaces {
      name = "plantgenie-north"
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
