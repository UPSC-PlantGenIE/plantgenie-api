data "waldur_openstack_flavor" "nginx" {
  filters = {
    name_exact  = var.nginx_flavor_name
    tenant_uuid = data.waldur_openstack_tenant.plantgenie.id
  }
}

resource "waldur_openstack_floating_ip" "nginx" {
  tenant = data.waldur_openstack_tenant.plantgenie.url
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
      fixed_ips = [
        {
          ip_address = local.nginx_pinned_ip
          subnet_id  = data.waldur_openstack_subnet.internal.backend_id
        },
      ]
    },
  ]

  floating_ips = [
    {
      subnet = data.waldur_openstack_subnet.internal.url
      url    = waldur_openstack_floating_ip.nginx.url
    },
  ]

  security_groups = [
    { url = data.waldur_openstack_security_group.default.url },
    { url = data.waldur_openstack_security_group.ssh.url },
    { url = data.waldur_openstack_security_group.web.url },
    { url = waldur_openstack_security_group.bolt.url },
  ]

  release_floating_ips = false

  user_data = trimspace(templatefile("${path.module}/nginx-cloud-init.yaml", {
    server_username         = var.server_username
    public_ssh_key          = trimspace(tls_private_key.ssh.public_key_openssh)
    neo4j_internal_ip       = waldur_openstack_instance.neo4j.internal_ips[0]
    rabbitmq_internal_ip    = waldur_openstack_instance.rabbitmq.internal_ips[0]
    rustfs_internal_ip      = waldur_openstack_instance.rustfs.internal_ips[0]
    application_internal_ip = local.application_pinned_ip
    internal_subnet_cidr    = data.waldur_openstack_subnet.internal.cidr
    ui_download_url         = var.ui_download_url
    jbrowse_download_url    = var.jbrowse_download_url
    domain_names            = join(" ", var.domain_names)
    rustfs_domain_name      = var.rustfs_domain_name
  }))
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

output "nginx_floating_ip" {
  value = waldur_openstack_floating_ip.nginx.address
}
