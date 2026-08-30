data "waldur_openstack_flavor" "nginx" {
  filters = {
    name_exact  = var.nginx_flavor_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

resource "waldur_openstack_instance" "nginx" {
  name               = "plantgenie-nginx"
  project            = data.waldur_structure_project.plantgenie.url
  offering           = data.waldur_marketplace_offering.instance.url
  flavor             = data.waldur_openstack_flavor.nginx.url
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

  user_data = trimspace(templatefile("${path.module}/nginx-cloud-init.yaml", {
    server_username      = var.server_username
    public_ssh_key       = trimspace(tls_private_key.ssh.public_key_openssh)
    neo4j_internal_ip    = waldur_openstack_instance.neo4j.internal_ips[0]
    internal_subnet_cidr = data.waldur_openstack_subnet.internal.cidr
  }))
}

resource "null_resource" "nginx_security_groups" {
  triggers = {
    instance_id     = waldur_openstack_instance.nginx.id
    security_groups = join(",", local.nginx_security_group_urls)
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    environment = {
      WALDUR_API_URL      = var.waldur_api_url
      WALDUR_ACCESS_TOKEN = var.waldur_access_token
      TENANT_UUID         = data.waldur_openstack_tenant.plantgenie.id
      INTERNAL_IP         = waldur_openstack_instance.nginx.internal_ips[0]
      SECURITY_GROUPS     = jsonencode(local.nginx_security_group_urls)
    }

    command = "python3 ${path.module}/attach-security-groups.py"
  }
}

resource "waldur_openstack_security_group" "bolt" {
  name        = "bolt"
  description = "Neo4j Bolt"
  tenant      = data.waldur_openstack_tenant.plantgenie.url

  rules = [
    {
      direction = "ingress"
      ethertype = "IPv4"
      protocol  = "tcp"
      from_port = 7687
      to_port   = 7687
      cidr      = "0.0.0.0/0"
    },
  ]
}

locals {
  nginx_security_group_urls = [
    data.waldur_openstack_security_group.default.url,
    data.waldur_openstack_security_group.ssh.url,
    data.waldur_openstack_security_group.web.url,
    waldur_openstack_security_group.bolt.url,
  ]
}

output "nginx_floating_ip" {
  value = [for fip in waldur_openstack_instance.nginx.floating_ips : fip.address]
}
