output "vm_id" {
  value       = proxmox_virtual_environment_container.reverse_proxy.vm_id
  description = "Proxmox VMID of the container."
}

output "container_id" {
  value       = proxmox_virtual_environment_container.reverse_proxy.id
  description = "Resource ID, handy as a provisioner trigger."
}

output "vm_ip" {
  value       = local.vm_ip
  description = "Container IPv4 address (no prefix)."
}
