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

variable "test_image_name" {
  description = "OS image for every instance"
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

variable "shared_volume_size" {
  description = "Size of the shared NFS volume on nginx in GB"
  type        = number
}

variable "nginx_flavor_name" {
  description = "Flavor for the nginx instance"
  type        = string
}

variable "ui_download_url" {
  description = "URL to download the React frontend zip from GitHub releases"
  type        = string
}

variable "domain_names" {
  description = "Domain names for this deployment, used for nginx server_name"
  type        = list(string)
}

variable "rabbitmq_flavor_name" {
  description = "Flavor for the rabbitmq instance"
  type        = string
}

variable "rabbitmq_username" {
  description = "RabbitMQ default user"
  type        = string
}

variable "rabbitmq_password" {
  description = "RabbitMQ default user password"
  type        = string
  sensitive   = true
}

variable "redis_flavor_name" {
  description = "Flavor for the redis instance"
  type        = string
}

variable "queue_flavor_name" {
  description = "Flavor for the celery queue instance"
  type        = string
}

variable "application_flavor_name" {
  description = "Flavor for the fastapi backend instance"
  type        = string
}

variable "github_pat" {
  description = "GitHub personal access token for pulling images from GHCR"
  type        = string
  sensitive   = true
}

variable "github_username" {
  description = "GitHub username associated with the PAT"
  type        = string
}

variable "celery_worker_image_tag" {
  description = "Docker image tag for the celery worker (e.g. v0.4.5)"
  type        = string
}

variable "fastapi_image_tag" {
  description = "Docker image tag for the fastapi backend (e.g. v0.4.5)"
  type        = string
}

variable "os_auth_url" {
  description = "OpenStack identity service URL of the old cluster, still hosting Swift"
  type        = string
}

variable "os_region_name" {
  description = "OpenStack region name of the old cluster"
  type        = string
}

variable "os_application_credential_id" {
  description = "OpenStack application credential id for Swift access"
  type        = string
  sensitive   = true
}

variable "os_application_credential_secret" {
  description = "OpenStack application credential secret for Swift access"
  type        = string
  sensitive   = true
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
