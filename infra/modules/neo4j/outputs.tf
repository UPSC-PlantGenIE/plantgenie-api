output "internal_ip" {
  description = "Internal IP address of the neo4j VM"
  value       = openstack_compute_instance_v2.neo4j.network[0].fixed_ip_v4
}
