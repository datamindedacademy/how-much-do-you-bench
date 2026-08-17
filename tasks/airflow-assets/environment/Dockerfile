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

WORKDIR /app
COPY dags/ /app/dags/
RUN mkdir -p /app/warehouse && chmod -R 0777 /app
