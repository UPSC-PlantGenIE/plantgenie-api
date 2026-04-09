terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 3.2.0"
    }
  }
}

resource "openstack_compute_instance_v2" "application" {
  name        = "${var.workspace}-${var.application_name}-application"
  image_name  = var.base_image_name
  flavor_name = var.flavor_name
  key_pair    = var.ssh_keypair_name

  network {
    port = var.internal_port_id
  }

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    server_username = var.server_username
    public_ssh_key  = var.ssh_public_key
    nfs_internal_ip = var.nfs_server_ip
    github_pat      = var.github_pat
    github_username = var.github_username
  })
}
