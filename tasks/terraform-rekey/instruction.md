Three things went wrong with this config, and they have to be fixed together.

`/app/main.tf` manages one file per environment in `/app/envs`. The list is
`["dev", "staging", "prod", "legacy"]`.

**One.** Last month someone inserted an environment into the middle of that list.
Terraform then rewrote every environment after it, because each resource is
identified by its position in the list rather than by which environment it is.
Identify them by name instead, so inserting or removing one leaves the others
alone.

**Two.** That change must not destroy or recreate anything. These stand in for
DNS records: deleting and recreating one is an outage, even if the end state
looks identical. `terraform plan` must come out clean, with nothing to add,
change or destroy.

**Three.** `legacy` is being handed over to another team. Terraform must stop
managing it, but the file must stay exactly where it is, untouched. Removing it
from the config the obvious way deletes it.

**Four.** Leave a guard behind. Someone will reintroduce positional keys in six
months during a hurried refactor, and `plan` will look fine to them. Add a check
that runs as part of the configuration and fails if the environments stop being
keyed by name -- Terraform can do this natively, without a CI script.

Constraints:

- Do not edit or delete anything under `/app/envs`, and do not touch
  `/app/baseline.json`.
- Do not hand-edit `terraform.tfstate`.
- `terraform plan` must report no changes when you are done.
