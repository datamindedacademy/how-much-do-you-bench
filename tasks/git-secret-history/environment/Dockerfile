FROM hmdyb-task-base:1

WORKDIR /app
COPY build_repo.sh /app/build_repo.sh
# Identity and safe.directory first: the script commits, and a rewrite later runs
# as a different user than the one that built the image.
RUN git config --global user.email "dev@example.com" \
    && git config --global user.name "dev" \
    && git config --global --add safe.directory /app/repo \
    && git config --global init.defaultBranch main \
    && chmod +x /app/build_repo.sh \
    && /app/build_repo.sh
