output "private_key_pem" {
  description = "Private SSH key for connecting to VMs (save locally, never commit)"
  value       = tls_private_key.ssh.private_key_pem
  sensitive   = true
}
