output "private_key_pem" {
  description = "Private SSH key for connecting to VMs (save locally, never commit)"
  value       = tls_private_key.ssh.private_key_pem
  sensitive   = true
}

output "nginx_floating_ip" {
  description = "Public floating IP address of the nginx VM"
  value       = module.nginx.floating_ip
}

output "nginx_internal_ip" {
  description = "Internal IP address of the nginx VM"
  value       = module.nginx.internal_ip
}

output "application_internal_ip" {
  description = "Internal IP address of the application VM"
  value       = module.application.internal_ip
}
