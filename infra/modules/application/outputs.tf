output "internal_ip" {
  description = "Internal IP address of the application VM"
  value       = openstack_compute_instance_v2.application.network[0].fixed_ip_v4
}
