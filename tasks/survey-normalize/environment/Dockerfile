FROM ghcr.io/jvanbuel/hmdyb-task-base:1

# The exercise is stdlib only: csv, sqlite3, re. pytest is for the grader.
RUN pip install --no-cache-dir pytest==8.4.1

WORKDIR /app
COPY normalize.py /app/normalize.py
COPY quant151.csv /app/quant151.csv
