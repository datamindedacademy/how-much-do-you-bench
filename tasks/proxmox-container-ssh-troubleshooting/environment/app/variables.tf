variable "proxmox_node" {
  type        = string
  description = "Target node that will host the container, e.g. pve01."
}

variable "vm_id" {
  type        = number
  description = "Proxmox VMID for the container (shared numeric space with VMs)."
  validation {
    condition     = var.vm_id >= 200 && var.vm_id <= 300
    error_message = "vm_id for containers must be in the 200-300 range."
  }
}

variable "vm_name" {
  type        = string
  default     = "reverse-proxy01"
  description = "Container hostname."
}

variable "vm_ipv4_address" {
  type        = string
  description = "Static IP with prefix from the VM pool (.2-.99), e.g. 10.20.83.2/24."

  validation {
    condition     = can(regex("^10\\.20\\.83\\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])/24$", var.vm_ipv4_address))
    error_message = "vm_ipv4_address must be in the 10.20.83.0/24 range and a /24 CIDR, e.g. 10.20.83.2/24."
  }
}

variable "vm_gateway" {
  type    = string
  default = "10.20.83.1"
}

variable "dns_servers" {
  type    = list(string)
  default = ["193.190.2.30"] # Uhasselt DNS
}

variable "ssh_public_keys" {
  type        = list(string)
  description = "SSH public keys authorized for root (used by Terraform to provision the container over SSH)."
}

variable "vm_cores" {
  type    = number
  default = 2
}

variable "vm_memory" {
  type        = number
  default     = 512
  description = "RAM in MB. A reverse proxy needs very little."
}

variable "disk_size" {
  type        = number
  default     = 4
  description = "Root filesystem size in GB."
}

variable "datastore_id" {
  type        = string
  default     = "vmdata"
  description = "Datastore for the container rootfs. Must have the 'Container' content type enabled."
}

variable "network_bridge" {
  type    = string
  default = "vmbr0"
}
