data "waldur_openstack_flavor" "rustfs" {
  filters = {
    name_exact  = var.rustfs_flavor_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

resource "waldur_openstack_instance" "rustfs" {
  name               = "plantgenie-rustfs"
  project            = data.waldur_structure_project.plantgenie.url
  offering           = data.waldur_marketplace_offering.instance.url
  flavor             = data.waldur_openstack_flavor.rustfs.url
  image              = data.waldur_openstack_image.test.url
  ssh_public_key     = waldur_core_ssh_public_key.ssh.url
  system_volume_size = 20480

  ports = [
    {
      subnet = data.waldur_openstack_subnet.internal.url
    },
  ]

  security_groups = [
    { url = data.waldur_openstack_security_group.default.url },
    { url = data.waldur_openstack_security_group.ssh.url },
  ]

  user_data = trimspace(templatefile("${path.module}/rustfs-cloud-init.yaml", {
    server_username      = var.server_username
    public_ssh_key       = trimspace(tls_private_key.ssh.public_key_openssh)
    internal_subnet_cidr = data.waldur_openstack_subnet.internal.cidr
    rustfs_download_url  = var.rustfs_download_url
    rustfs_access_key    = var.rustfs_access_key
    rustfs_secret_key    = var.rustfs_secret_key
  }))
}

resource "waldur_openstack_volume" "rustfs_data" {
  name     = "plantgenie-rustfs-data"
  project  = data.waldur_structure_project.plantgenie.url
  offering = data.waldur_marketplace_offering.volume.url
  size     = var.rustfs_data_volume_size * 1024
}

resource "waldur_openstack_volume_attachment" "rustfs_data" {
  volume   = waldur_openstack_volume.rustfs_data.id
  instance = waldur_openstack_instance.rustfs.url
}

output "rustfs_internal_ip" {
  value = waldur_openstack_instance.rustfs.internal_ips[0]
}