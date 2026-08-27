variable "waldur_api_url" {
  description = "Waldur API endpoint URL"
  type        = string
}

variable "waldur_access_token" {
  description = "Waldur API access token"
  type        = string
  sensitive   = true
}

variable "external_network_uuid" {
  description = "Waldur UUID of the external network (openstack-pub)"
  type        = string
}

variable "external_network_backend_id" {
  description = "OpenStack backend id of the external network, as reported by the tenant"
  type        = string
}

variable "project_name" {
  description = "Waldur project name, also used as the tenant name"
  type        = string
}

variable "internal_subnet_name" {
  description = "Name of the tenant's internal subnet"
  type        = string
}

variable "test_flavor_name" {
  description = "Flavor for the test instance"
  type        = string
}

variable "test_image_name" {
  description = "OS image for the test instance"
  type        = string
}

variable "neo4j_data_volume_size" {
  description = "Size of the neo4j data volume in GB"
  type        = number
}

variable "neo4j_flavor_name" {
  description = "Flavor for the neo4j instance"
  type        = string
}

variable "nginx_flavor_name" {
  description = "Flavor for the nginx instance"
  type        = string
}

variable "server_username" {
  description = "Username for the non-root user account on the VMs"
  type        = string
}

variable "neo4j_username" {
  description = "Neo4j database username"
  type        = string
}

variable "neo4j_password" {
  description = "Neo4j database password"
  type        = string
  sensitive   = true
}
