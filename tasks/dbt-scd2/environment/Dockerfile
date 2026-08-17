FROM ghcr.io/jvanbuel/hmdyb-task-base:1

# dbt 1.9 or later: the deletion handling this task needs did not exist before.
RUN pip install --no-cache-dir \
      dbt-core==1.9.4 \
      dbt-duckdb==1.9.3 \
      duckdb==1.4.1

WORKDIR /app
COPY pipeline/ /app/pipeline/
COPY feed/ /app/feed/
COPY run_pipeline.sh /app/run_pipeline.sh
RUN chmod +x /app/run_pipeline.sh
