#!/bin/bash
# for_each keys by name. moved blocks carry the existing state across, so nothing
# is destroyed. legacy cannot be released with a removed block directly -- those
# target a whole resource, not one instance of a counted one -- so it is first
# moved to its own address and then removed with destroy = false.
set -euo pipefail

cat > /app/main.tf <<'TF'
terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "2.5.2"
    }
  }
}

variable "environments" {
  type    = set(string)
  default = ["dev", "staging", "prod"]
}

resource "local_file" "env" {
  for_each = var.environments
  filename = "/app/envs/${each.key}.txt"
  content  = "environment: ${each.key}\n"
}

moved {
  from = local_file.env[0]
  to   = local_file.env["dev"]
}

moved {
  from = local_file.env[1]
  to   = local_file.env["staging"]
}

moved {
  from = local_file.env[2]
  to   = local_file.env["prod"]
}

moved {
  from = local_file.env[3]
  to   = local_file.legacy
}

removed {
  from = local_file.legacy

  lifecycle {
    destroy = false
  }
}
TF

# The guard: plan-only, so running it does not touch the files it describes.
mkdir -p /app/tests
cat > /app/tests/rekey.tftest.hcl <<'HCL'
run "keyed_by_name" {
  command = plan

  assert {
    condition     = local_file.env["dev"].filename == "/app/envs/dev.txt"
    error_message = "dev is not keyed by name"
  }

  assert {
    condition     = length(local_file.env) == 3
    error_message = "expected exactly three managed environments"
  }
}
HCL

cd /app && terraform apply -auto-approve -input=false >/dev/null
