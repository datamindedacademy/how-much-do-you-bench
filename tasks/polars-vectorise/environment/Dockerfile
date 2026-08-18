FROM hmdyb-task-base:1

RUN pip install --no-cache-dir polars==1.35.1 numpy==2.3.4 pyarrow==22.0.0

WORKDIR /app
COPY transform.py /app/transform.py
COPY generate_data.py /app/generate_data.py
RUN mkdir -p /app/data /app/out && python /app/generate_data.py

# The fixture's fingerprint, taken at build time and kept outside /app. Both the
# answer and the yardstick are computed from orders.parquet, so a submission that
# rewrote it would be graded against its own edit: a row count catches shrinking
# it, nothing catches changing the values in place.
RUN sha256sum /app/data/orders.parquet | cut -d' ' -f1 > /opt/orders.sha256
