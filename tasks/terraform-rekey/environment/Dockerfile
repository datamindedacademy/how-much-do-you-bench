# Terraform with the state already in place, keyed by list position.
FROM hmdyb-task-base:1

ARG TERRAFORM_VERSION=1.11.4
RUN curl -fsSLo /tmp/tf.zip \
       "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip" \
    && unzip -q /tmp/tf.zip -d /usr/local/bin \
    && rm /tmp/tf.zip

WORKDIR /app
COPY main.tf /app/main.tf

# A filesystem mirror, so the agent can re-run init without the network.
RUN terraform providers mirror /providers >/dev/null \
    && printf 'provider_installation {\n  filesystem_mirror {\n    path    = "/providers"\n    include = ["registry.terraform.io/*/*"]\n  }\n  direct {\n    exclude = ["registry.terraform.io/*/*"]\n  }\n}\n' > /root/.terraformrc

# The state the task starts from: four environments, indexed by position.
# The baseline lands in /opt, not /app: it is the verifier's evidence, and an
# agent tidying its workspace has every reason to delete a stray baseline.json
# and no way to know it is being graded on it.
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
pathlib.Path("/opt/baseline.json").write_text(json.dumps(baseline, indent=2))
print("baseline:", sorted(baseline))
PY

# A git repo, because a harness that curates its own file list has no other way
# to find them: aider's context comes from its repo map, the repo map comes from
# git, and without one it asks the user to paste the code. Cloning the real
# repository here would hand the agent tests/ and solution/solve.sh, so the
# fixtures get their own single commit instead -- same discovery, no answers, no
# history to mine.
RUN cd /app \
 && git init -q \
 && git config user.email fixtures@example.com \
 && git config user.name fixtures \
 && git add -A \
 && git commit -qm "task fixtures"
