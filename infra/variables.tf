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

variable "github_pat" {
  description = "GitHub personal access token for pulling images from GHCR"
  type        = string
  sensitive   = true
}

variable "github_username" {
  description = "GitHub username associated with the PAT"
  type        = string
}
