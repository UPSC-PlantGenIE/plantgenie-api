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

variable "storage_size" {
  type        = number
  description = "Size of the neo4j block storage volume in GB"
}

variable "neo4j_username" {
  type        = string
  description = "Neo4j database username"
}

variable "neo4j_password" {
  type        = string
  sensitive   = true
  description = "Neo4j database password"
}
