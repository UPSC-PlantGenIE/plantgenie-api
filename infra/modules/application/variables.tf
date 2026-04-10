variable "workspace" {
  type        = string
  description = "Terraform workspace name, used to prefix resource names"
}

variable "application_name" {
  type        = string
  description = "Name of the application, used to prefix resource names"
}

variable "base_image_name" {
  type        = string
  description = "Name of the base OS image for the VM"
}

variable "flavor_name" {
  type        = string
  description = "OpenStack flavor (size) for the VM"
}

variable "ssh_keypair_name" {
  type        = string
  description = "Name of the OpenStack keypair for SSH access"
}

variable "ssh_public_key" {
  type        = string
  description = "Public SSH key injected into the VM via cloud-init"
}

variable "internal_port_id" {
  type        = string
  description = "ID of the pre-created internal network port"
}

variable "server_username" {
  type        = string
  description = "Username for the non-root user account on the VM"
}

variable "nfs_server_ip" {
  type        = string
  description = "Internal IP of the nginx VM, used for NFS mount"
}

variable "github_pat" {
  type        = string
  sensitive   = true
  description = "GitHub personal access token for pulling images from GHCR"
}

variable "github_username" {
  type        = string
  description = "GitHub username associated with the PAT"
}

variable "rabbitmq_username" {
  type        = string
  description = "RabbitMQ username for the Celery broker URL"
}

variable "rabbitmq_password" {
  type        = string
  sensitive   = true
  description = "RabbitMQ password for the Celery broker URL"
}

variable "rabbitmq_internal_ip" {
  type        = string
  description = "Internal IP of the rabbitmq VM"
}

variable "redis_internal_ip" {
  type        = string
  description = "Internal IP of the redis VM"
}

variable "os_auth_url" {
  type        = string
  description = "OpenStack identity service URL"
}

variable "os_region_name" {
  type        = string
  description = "OpenStack region name"
}

variable "os_application_credential_id" {
  type        = string
  sensitive   = true
  description = "OpenStack application credential ID, created by Terraform"
}

variable "os_application_credential_secret" {
  type        = string
  sensitive   = true
  description = "OpenStack application credential secret, created by Terraform"
}

variable "fastapi_image_tag" {
  type        = string
  description = "Docker image tag for the FastAPI backend (e.g. v0.4.0)"
}
