FROM ghcr.io/jvanbuel/hmdyb-task-base:1

ARG AIRFLOW_VERSION=3.0.3
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.12.txt"

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False \
    AIRFLOW__CORE__DAGS_FOLDER=/app/dags

WORKDIR /app
COPY dags/ /app/dags/
COPY generate_feed.py /app/generate_feed.py
RUN python /app/generate_feed.py && mkdir -p /app/out
