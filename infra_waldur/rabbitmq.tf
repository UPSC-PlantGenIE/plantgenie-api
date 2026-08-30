data "waldur_openstack_flavor" "rabbitmq" {
  filters = {
    name_exact  = var.rabbitmq_flavor_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

resource "waldur_openstack_instance" "rabbitmq" {
  name               = "plantgenie-rabbitmq"
  project            = data.waldur_structure_project.plantgenie.url
  offering           = data.waldur_marketplace_offering.instance.url
  flavor             = data.waldur_openstack_flavor.rabbitmq.url
  image              = data.waldur_openstack_image.test.url
  ssh_public_key     = waldur_core_ssh_public_key.ssh.url
  system_volume_size = 51200

  ports = [
    {
      subnet = data.waldur_openstack_subnet.internal.url
    },
  ]

  user_data = trimspace(templatefile("${path.module}/rabbitmq-cloud-init.yaml", {
    server_username   = var.server_username
    public_ssh_key    = trimspace(tls_private_key.ssh.public_key_openssh)
    rabbitmq_username = var.rabbitmq_username
    rabbitmq_password = var.rabbitmq_password
  }))
}

resource "null_resource" "rabbitmq_security_groups" {
  triggers = {
    instance_id     = waldur_openstack_instance.rabbitmq.id
    security_groups = join(",", local.rabbitmq_security_group_urls)
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    environment = {
      WALDUR_API_URL      = var.waldur_api_url
      WALDUR_ACCESS_TOKEN = var.waldur_access_token
      TENANT_UUID         = data.waldur_openstack_tenant.plantgenie.id
      INTERNAL_IP         = waldur_openstack_instance.rabbitmq.internal_ips[0]
      SECURITY_GROUPS     = jsonencode(local.rabbitmq_security_group_urls)
    }

    command = "python3 ${path.module}/attach-security-groups.py"
  }
}

locals {
  rabbitmq_security_group_urls = [
    data.waldur_openstack_security_group.default.url,
    data.waldur_openstack_security_group.ssh.url,
  ]
}

output "rabbitmq_internal_ip" {
  value = waldur_openstack_instance.rabbitmq.internal_ips[0]
}
