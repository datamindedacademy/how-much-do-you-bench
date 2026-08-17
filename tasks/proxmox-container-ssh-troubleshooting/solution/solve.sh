#!/bin/bash
# The upstream reference answer, embedded file by file.
set -euo pipefail

mkdir -p /app
cat > /app/main.tf <<'SOLUTION_EOF'
locals {
  vm_ip = split("/", var.vm_ipv4_address)[0]
}

# Reverse-proxy for the platform: a Proxmox LXC container that Terraform then
# configures over SSH (installs Caddy). Because the whole provisioning flow talks
# to the container over SSH, the container OS must run an SSH server kept up by an
# init system.
resource "proxmox_virtual_environment_container" "reverse_proxy" {
  node_name     = var.proxmox_node
  vm_id         = var.vm_id
  tags          = ["terraform", "caddy", "reverse-proxy"]
  unprivileged  = true
  start_on_boot = true
  started       = true

  cpu {
    cores = var.vm_cores
  }

  memory {
    dedicated = var.vm_memory
  }

  disk {
    datastore_id = var.datastore_id
    size         = var.disk_size
  }

  network_interface {
    name   = "eth0"
    bridge = var.network_bridge
  }

  operating_system {
    # A *standard* Proxmox LXC system template: full Debian userland with systemd
    # as PID 1 and openssh-server available/enabled, so Terraform can SSH in. The
    # previous value was an OCI application image -- a single-process rootfs with
    # no init and no sshd, so nothing ever listens on port 22 (download the LXC
    # template once with: pveam update && pveam download local debian-13-standard_...).
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  initialization {
    hostname = var.vm_name

    ip_config {
      ipv4 {
        address = var.vm_ipv4_address
        gateway = var.vm_gateway
      }
    }

    dns {
      servers = var.dns_servers
    }

    user_account {
      keys = var.ssh_public_keys
    }
  }

  features {
    nesting = false
  }
}

# Install and start Caddy over SSH once the container is up. This step (and every
# later config push) connects to the container as root over SSH.
resource "terraform_data" "install_caddy" {
  triggers_replace = [proxmox_virtual_environment_container.reverse_proxy.id]

  connection {
    type        = "ssh"
    host        = local.vm_ip
    user        = "root"
    password    = "pwd"
    timeout     = "5m"
  }

  provisioner "remote-exec" {
    inline = [
      "set -eu",
      "export DEBIAN_FRONTEND=noninteractive",
      "apt-get update",
      "apt-get install -y caddy",
      "systemctl enable --now caddy",
    ]
  }
}
SOLUTION_EOF
