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

data "waldur_openstack_flavor" "test" {
  filters = {
    name_exact  = var.test_flavor_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
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

resource "waldur_openstack_instance" "test" {
  name               = "plantgenie-test"
  project            = data.waldur_structure_project.plantgenie.url
  offering           = data.waldur_marketplace_offering.instance.url
  flavor             = data.waldur_openstack_flavor.test.url
  image              = data.waldur_openstack_image.test.url
  ssh_public_key     = waldur_core_ssh_public_key.ssh.url
  system_volume_size = 20480

  ports = [
    {
      subnet = data.waldur_openstack_subnet.internal.url
    },
  ]

  floating_ips = [
    {
      subnet = data.waldur_openstack_subnet.internal.url
    },
  ]
}

resource "null_resource" "instance_security_groups" {
  triggers = {
    instance_id     = waldur_openstack_instance.test.id
    security_groups = join(",", local.instance_security_group_urls)
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    environment = {
      WALDUR_API_URL      = var.waldur_api_url
      WALDUR_ACCESS_TOKEN = var.waldur_access_token
      TENANT_UUID         = data.waldur_openstack_tenant.plantgenie.id
      INTERNAL_IP         = waldur_openstack_instance.test.internal_ips[0]
      SECURITY_GROUPS     = jsonencode(local.instance_security_group_urls)
    }

    command = "python3 ${path.module}/attach-security-groups.py"
  }
}

locals {
  instance_security_group_urls = [
    data.waldur_openstack_security_group.default.url,
    data.waldur_openstack_security_group.ssh.url,
    data.waldur_openstack_security_group.web.url,
  ]
}

output "test_instance_floating_ip" {
  value = [for fip in waldur_openstack_instance.test.floating_ips : fip.address]
}

output "test_instance_private_key" {
  value     = tls_private_key.ssh.private_key_openssh
  sensitive = true
}
