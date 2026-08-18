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

# A git repo, because a harness that curates its own file list has no other way
# to find them: aider's context comes from its repo map, the repo map comes from
# git, and without one it asks the user to paste the code. Cloning the real
# repository here would hand the agent tests/ and solution/solve.sh, so the
# fixtures get their own single commit instead -- same discovery, no answers, no
# history to mine.
RUN cd /app \
 && git init -q \
 && git config user.email fixtures@example.com \
 && git config user.name fixtures \
 && git add -A \
 && git commit -qm "task fixtures"
