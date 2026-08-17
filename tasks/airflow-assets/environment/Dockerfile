# The official Airflow image, so the build is a registry pull and nothing else.
#
# Installing airflow with pip needs PyPI and GitHub over TLS, which fails behind
# any intercepting proxy -- a participant's laptop should not have to negotiate
# a corporate CA to run a task. Pinned, because a task whose environment drifts
# is a task whose difficulty drifts.
FROM apache/airflow:3.0.3-python3.12

USER root

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False \
    AIRFLOW__CORE__DAGS_FOLDER=/app/dags

# The airflow image adds pgdg, mariadb and microsoft apt sources. An agent that
# runs apt-get update as part of installing itself then waits on three repos it
# has no use for, and gets killed. Debian main is enough, and curl is what the
# installers actually want.
RUN rm -f /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

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
    && npm i -g opencode-ai@latest @anthropic-ai/claude-code @openai/codex \
         @google/gemini-cli @qwen-code/qwen-code \
    && npm cache clean --force

WORKDIR /app
COPY dags/ /app/dags/
RUN mkdir -p /app/warehouse && chmod -R 0777 /app

# The airflow image's entrypoint runs `airflow`, which prints help and exits, so
# the container stops as soon as it starts and every exec into it is killed --
# exit 137, which reads like an out-of-memory kill and is not one. The task
# container only has to stay alive.
ENTRYPOINT []
CMD ["sleep", "infinity"]
