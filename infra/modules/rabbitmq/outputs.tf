output "internal_ip" {
  description = "Internal IP address of the rabbitmq VM"
  value       = openstack_compute_instance_v2.rabbitmq.network[0].fixed_ip_v4
}
