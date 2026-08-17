# Terraform with the state already in place, keyed by list position.
FROM python:3.12-slim

ARG TERRAFORM_VERSION=1.11.4
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl unzip ca-certificates git jq \
    && curl -fsSLo /tmp/tf.zip \
       "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip" \
    && unzip -q /tmp/tf.zip -d /usr/local/bin \
    && rm /tmp/tf.zip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY main.tf /app/main.tf

# A filesystem mirror, so the agent can re-run init without the network.
RUN terraform providers mirror /providers >/dev/null \
    && printf 'provider_installation {\n  filesystem_mirror {\n    path    = "/providers"\n    include = ["registry.terraform.io/*/*"]\n  }\n  direct {\n    exclude = ["registry.terraform.io/*/*"]\n  }\n}\n' > /root/.terraformrc

# The state the task starts from: four environments, indexed by position.
RUN mkdir -p /app/envs \
    && terraform init -input=false >/dev/null \
    && terraform apply -auto-approve -input=false >/dev/null \
    && python - <<'PY'
import json, pathlib
envs = pathlib.Path("/app/envs")
baseline = {
    # Whole seconds: an image layer is a tarball and tar drops sub-second
    # precision, so a nanosecond baseline would not match its own file at runtime.
    p.name: {"content": p.read_text(), "mtime": int(p.stat().st_mtime)}
    for p in sorted(envs.glob("*.txt"))
}
pathlib.Path("/app/baseline.json").write_text(json.dumps(baseline, indent=2))
print("baseline:", sorted(baseline))
PY

# Pre-install the harnesses. Harbor installs them on every rollout regardless;
# finding them already present turns that into a version check rather than a
# download. Versions track harbor.agents.installed.node_install -- see
# tasks/AGENTS.md.
ENV NVM_DIR=/root/.nvm
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/* \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash \
    && . "$NVM_DIR/nvm.sh" \
    && nvm install 22 \
    && npm i -g opencode-ai@latest @openai/codex @mariozechner/pi-coding-agent \
    && npm cache clean --force

# uv, and the interpreter and tools the pip-installed harnesses want. swe-agent
# re-clones its own repo every run, so pre-cloning is pointless -- but it checks
# for uv before fetching it, and `uv python install 3.12` and a warm uv cache are
# the downloads worth removing. aider's installer is uv-based, so a pre-installed
# aider-chat resolves from cache instead of the network.
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy
# uv tool installs land here; harbor's aider adapter sources this itself, but a
# harness that just calls `aider` should find it too.
ENV PATH="/root/.local/bin:$PATH"
RUN uv python install 3.12 \
    && uv tool install aider-chat \
    && uv cache prune --ci || true
