data "waldur_openstack_flavor" "application" {
  filters = {
    name_exact  = var.application_flavor_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

resource "waldur_openstack_instance" "application" {
  name               = "plantgenie-application"
  project            = data.waldur_structure_project.plantgenie.url
  offering           = data.waldur_marketplace_offering.instance.url
  flavor             = data.waldur_openstack_flavor.application.url
  image              = data.waldur_openstack_image.test.url
  ssh_public_key     = waldur_core_ssh_public_key.ssh.url
  system_volume_size = 51200

  ports = [
    {
      subnet = data.waldur_openstack_subnet.internal.url
      fixed_ips = [
        {
          ip_address = local.application_pinned_ip
          subnet_id  = data.waldur_openstack_subnet.internal.backend_id
        },
      ]
    },
  ]

  user_data = trimspace(templatefile("${path.module}/application-cloud-init.yaml", {
    server_username                  = var.server_username
    public_ssh_key                   = trimspace(tls_private_key.ssh.public_key_openssh)
    nfs_internal_ip                  = local.nginx_pinned_ip
    github_pat                       = var.github_pat
    github_username                  = var.github_username
    rabbitmq_username                = var.rabbitmq_username
    rabbitmq_password                = var.rabbitmq_password
    rabbitmq_internal_ip             = waldur_openstack_instance.rabbitmq.internal_ips[0]
    redis_internal_ip                = waldur_openstack_instance.redis.internal_ips[0]
    neo4j_internal_ip                = waldur_openstack_instance.neo4j.internal_ips[0]
    neo4j_username                   = var.neo4j_username
    neo4j_password                   = var.neo4j_password
    os_auth_url                      = var.os_auth_url
    os_region_name                   = var.os_region_name
    os_application_credential_id     = var.os_application_credential_id
    os_application_credential_secret = var.os_application_credential_secret
    fastapi_image_tag                = var.fastapi_image_tag
  }))
}

resource "null_resource" "application_security_groups" {
  triggers = {
    instance_id     = waldur_openstack_instance.application.id
    security_groups = join(",", local.application_security_group_urls)
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    environment = {
      WALDUR_API_URL      = var.waldur_api_url
      WALDUR_ACCESS_TOKEN = var.waldur_access_token
      TENANT_UUID         = data.waldur_openstack_tenant.plantgenie.id
      INTERNAL_IP         = waldur_openstack_instance.application.internal_ips[0]
      SECURITY_GROUPS     = jsonencode(local.application_security_group_urls)
    }

    command = "python3 ${path.module}/attach-security-groups.py"
  }
}

locals {
  application_security_group_urls = [
    data.waldur_openstack_security_group.default.url,
    data.waldur_openstack_security_group.ssh.url,
  ]
}

output "application_internal_ip" {
  value = waldur_openstack_instance.application.internal_ips[0]
}
