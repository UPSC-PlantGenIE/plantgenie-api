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
