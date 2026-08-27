data "waldur_marketplace_offering" "volume" {
  filters = {
    name         = "Volume in ${var.project_name}"
    project_uuid = data.waldur_structure_project.plantgenie.id
  }
}

resource "waldur_openstack_volume" "neo4j_data" {
  name     = "plantgenie-neo4j-data"
  project  = data.waldur_structure_project.plantgenie.url
  offering = data.waldur_marketplace_offering.volume.url
  size     = var.neo4j_data_volume_size * 1024
}

resource "null_resource" "neo4j_data_attachment" {
  triggers = {
    volume_id   = waldur_openstack_volume.neo4j_data.id
    instance_id = waldur_openstack_instance.neo4j.id
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    environment = {
      WALDUR_API_URL      = var.waldur_api_url
      WALDUR_ACCESS_TOKEN = var.waldur_access_token
      VOLUME_UUID         = waldur_openstack_volume.neo4j_data.id
      INSTANCE_URL        = waldur_openstack_instance.neo4j.url
    }

    command = "python3 ${path.module}/attach-volume.py"
  }
}
