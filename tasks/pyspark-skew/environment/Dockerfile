FROM ghcr.io/jvanbuel/hmdyb-task-base:1

RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pyspark==3.5.3 polars==1.35.1 numpy==2.3.4 pyarrow==22.0.0

ENV JAVA_HOME=/usr/lib/jvm/default-java \
    SPARK_LOCAL_IP=127.0.0.1

WORKDIR /app
COPY job.py /app/job.py
COPY generate_data.py /app/generate_data.py
RUN mkdir -p /app/data /app/out && python /app/generate_data.py
