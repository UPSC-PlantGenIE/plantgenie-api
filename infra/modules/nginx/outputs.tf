output "floating_ip" {
  description = "Public floating IP address of the nginx VM"
  value       = openstack_networking_floatingip_v2.floating_ip.address
}

output "internal_ip" {
  description = "Internal IP address of the nginx VM"
  value       = openstack_compute_instance_v2.nginx.network[0].fixed_ip_v4
}
