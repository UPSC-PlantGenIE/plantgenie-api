output "floating_ip" {
  description = "Public floating IP address of the nginx VM"
  value       = openstack_networking_floatingip_v2.floating_ip.address
}
