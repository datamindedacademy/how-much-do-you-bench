FROM hmdyb-task-base:1

# Airflow on the shared base rather than FROM apache/airflow. The official image
# is its own multi-gigabyte tree with a different parent chain, so it shared no
# layers with the other tasks -- and its entrypoint runs `airflow`, which prints
# help and exits, killing the task container and every exec into it with a
# misleading exit 137.
#
# Pinned with the upstream constraints file: an unpinned airflow resolves
# differently every build, and a task whose environment drifts is a task whose
# difficulty drifts.
ARG AIRFLOW_VERSION=3.0.3
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.12.txt"

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False \
    AIRFLOW__CORE__DAGS_FOLDER=/app/dags

WORKDIR /app
COPY dags/ /app/dags/
RUN mkdir -p /app/warehouse
