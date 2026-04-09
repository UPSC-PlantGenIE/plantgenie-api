terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 3.2.0"
    }
  }
}

resource "openstack_compute_instance_v2" "neo4j" {
  name        = "${var.workspace}-${var.application_name}-neo4j"
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
    neo4j_username  = var.neo4j_username
    neo4j_password  = var.neo4j_password
  })
}

resource "openstack_blockstorage_volume_v3" "data" {
  name = "${var.workspace}-${var.application_name}-neo4j-data"
  size = var.storage_size
}

resource "openstack_compute_volume_attach_v2" "data" {
  instance_id = openstack_compute_instance_v2.neo4j.id
  volume_id   = openstack_blockstorage_volume_v3.data.id
  device      = "/dev/vdb"
}
