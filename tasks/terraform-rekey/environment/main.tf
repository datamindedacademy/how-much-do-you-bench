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
  type    = list(string)
  default = ["dev", "staging", "prod", "legacy"]
}

# One marker file per environment. In the real config these are DNS records; the
# shape of the problem is the same and this one runs without credentials.
resource "local_file" "env" {
  count    = length(var.environments)
  filename = "/app/envs/${var.environments[count.index]}.txt"
  content  = "environment: ${var.environments[count.index]}\n"
}
