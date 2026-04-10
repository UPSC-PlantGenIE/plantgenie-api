terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 3.2.0"
    }
  }
}

resource "openstack_networking_floatingip_v2" "floating_ip" {
  pool = var.external_network_name
}

resource "openstack_compute_instance_v2" "nginx" {
  name        = "${var.workspace}-${var.application_name}-nginx"
  image_name  = var.base_image_name
  flavor_name = var.flavor_name
  key_pair    = var.ssh_keypair_name

  network {
    port = var.internal_port_id
  }

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    server_username      = var.server_username
    public_ssh_key       = var.ssh_public_key
    internal_subnet_cidr = var.internal_subnet_cidr
    neo4j_internal_ip    = var.neo4j_internal_ip
    rabbitmq_internal_ip = var.rabbitmq_internal_ip
  })
}

resource "openstack_networking_floatingip_associate_v2" "public_ip" {
  floating_ip = openstack_networking_floatingip_v2.floating_ip.address
  port_id     = var.internal_port_id
}

resource "openstack_blockstorage_volume_v3" "data" {
  name = "${var.workspace}-${var.application_name}-data"
  size = var.storage_size
}

resource "openstack_compute_volume_attach_v2" "data" {
  instance_id = openstack_compute_instance_v2.nginx.id
  volume_id   = openstack_blockstorage_volume_v3.data.id
  device      = "/dev/vdb"
}
