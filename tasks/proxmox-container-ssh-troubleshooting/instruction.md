# Reverse-proxy container: Terraform can't SSH into it

This is the `bpg/proxmox` Terraform for our platform reverse proxy.

`terraform apply` creates the container fine, but the `install_caddy` step hangs
and then fails: Terraform can't establish an SSH connection. Connecting by hand
(`ssh root@<ip>`) also fails: the connection is refused / closed immediately, even
though the SSH key is configured on the container. sshd never seems to be running.

Find and fix the root cause so Terraform can provision the container over SSH.
