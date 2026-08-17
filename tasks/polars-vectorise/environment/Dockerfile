FROM ghcr.io/jvanbuel/hmdyb-task-base:1

RUN pip install --no-cache-dir polars==1.35.1 numpy==2.3.4 pyarrow==22.0.0

WORKDIR /app
COPY transform.py /app/transform.py
COPY generate_data.py /app/generate_data.py
RUN mkdir -p /app/data /app/out && python /app/generate_data.py
