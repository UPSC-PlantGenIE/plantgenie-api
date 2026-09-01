data "waldur_openstack_flavor" "neo4j" {
  filters = {
    name_exact  = var.neo4j_flavor_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

resource "waldur_openstack_instance" "neo4j" {
  name               = "plantgenie-neo4j"
  project            = data.waldur_structure_project.plantgenie.url
  offering           = data.waldur_marketplace_offering.instance.url
  flavor             = data.waldur_openstack_flavor.neo4j.url
  image              = data.waldur_openstack_image.test.url
  ssh_public_key     = waldur_core_ssh_public_key.ssh.url
  system_volume_size = 20480

  ports = [
    {
      subnet = data.waldur_openstack_subnet.internal.url
    },
  ]

  user_data = trimspace(templatefile("${path.module}/neo4j-cloud-init.yaml", {
    server_username = var.server_username
    public_ssh_key  = trimspace(tls_private_key.ssh.public_key_openssh)
    neo4j_username  = var.neo4j_username
    neo4j_password  = var.neo4j_password
  }))
}

resource "null_resource" "neo4j_security_groups" {
  triggers = {
    instance_id     = waldur_openstack_instance.neo4j.id
    security_groups = join(",", local.neo4j_security_group_urls)
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    environment = {
      WALDUR_API_URL      = var.waldur_api_url
      WALDUR_ACCESS_TOKEN = var.waldur_access_token
      TENANT_UUID         = data.waldur_openstack_tenant.plantgenie.id
      INTERNAL_IP         = waldur_openstack_instance.neo4j.internal_ips[0]
      SECURITY_GROUPS     = jsonencode(local.neo4j_security_group_urls)
    }

    command = "python3 ${path.module}/attach-security-groups.py"
  }
}

locals {
  neo4j_security_group_urls = [
    data.waldur_openstack_security_group.default.url,
    data.waldur_openstack_security_group.ssh.url,
  ]
}

output "neo4j_internal_ip" {
  value = waldur_openstack_instance.neo4j.internal_ips[0]
}
