FROM hmdyb-task-base:1

# Constraints vendored rather than fetched: pulling them from
# raw.githubusercontent.com on every build made the task depend on an anonymous
# rate limit, and twenty-odd builds in an afternoon earned a 429.
ARG AIRFLOW_VERSION=3.0.3
COPY constraints-3.12.txt /tmp/constraints-3.12.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" \
      --constraint /tmp/constraints-3.12.txt

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False \
    AIRFLOW__CORE__DAGS_FOLDER=/app/dags

WORKDIR /app
COPY dags/ /app/dags/
COPY generate_feed.py /app/generate_feed.py
RUN python /app/generate_feed.py && mkdir -p /app/out
