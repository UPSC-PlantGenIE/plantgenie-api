data "waldur_structure_project" "plantgenie" {
  filters = {
    name = var.project_name
  }
}

data "waldur_openstack_tenant" "plantgenie" {
  filters = {
    name         = var.project_name
    project_uuid = data.waldur_structure_project.plantgenie.id
  }
}

data "waldur_marketplace_offering" "instance" {
  filters = {
    name         = "Virtual machine in ${var.project_name}"
    project_uuid = data.waldur_structure_project.plantgenie.id
  }
}

data "waldur_openstack_image" "test" {
  filters = {
    name        = var.test_image_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

data "waldur_openstack_subnet" "internal" {
  filters = {
    name        = var.internal_subnet_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

data "waldur_openstack_security_group" "default" {
  filters = {
    name_exact  = "default"
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

data "waldur_openstack_security_group" "ssh" {
  filters = {
    name_exact  = "ssh"
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

data "waldur_openstack_security_group" "web" {
  filters = {
    name_exact  = "web"
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "waldur_core_ssh_public_key" "ssh" {
  name       = "plantgenie-test"
  public_key = trimspace(tls_private_key.ssh.public_key_openssh)
}

output "ssh_private_key" {
  value     = tls_private_key.ssh.private_key_openssh
  sensitive = true
}
