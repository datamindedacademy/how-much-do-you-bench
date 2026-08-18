FROM hmdyb-task-base:1

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
