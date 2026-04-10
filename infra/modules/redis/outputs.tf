output "internal_ip" {
  description = "Internal IP address of the redis VM"
  value       = openstack_compute_instance_v2.redis.network[0].fixed_ip_v4
}
