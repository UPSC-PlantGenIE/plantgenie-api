variable "application_name" {
  description = "Name of the application, used to prefix resource names"
  type        = string
}

variable "internal_network_name" {
  description = "Name of the internal IPv4 network"
  type        = string
}

variable "external_network_name" {
  description = "Name of the external IPv4 network"
  type        = string
}

variable "base_image_name" {
  description = "Name of the base OS image for VMs"
  type        = string
}

variable "server_username" {
  description = "Username for the non-root user account on VMs"
  type        = string
}

variable "nfs_storage_size" {
  description = "Size of the nginx NFS block storage volume in GB"
  type        = number
}

variable "neo4j_storage_size" {
  description = "Size of the neo4j block storage volume in GB"
  type        = number
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

variable "github_pat" {
  description = "GitHub personal access token for pulling images from GHCR"
  type        = string
  sensitive   = true
}

variable "github_username" {
  description = "GitHub username associated with the PAT"
  type        = string
}

variable "rabbitmq_username" {
  description = "RabbitMQ default username"
  type        = string
}

variable "rabbitmq_password" {
  description = "RabbitMQ default password"
  type        = string
  sensitive   = true
}

variable "os_auth_url" {
  description = "OpenStack identity service URL"
  type        = string
}

variable "os_region_name" {
  description = "OpenStack region name"
  type        = string
}

variable "celery_worker_image_tag" {
  description = "Docker image tag for the celery worker (e.g. v0.4.0)"
  type        = string
}

variable "fastapi_image_tag" {
  description = "Docker image tag for the FastAPI backend (e.g. v0.4.0)"
  type        = string
}

variable "ui_download_url" {
  description = "URL to download the React frontend zip from GitHub releases"
  type        = string
}
