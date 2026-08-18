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

# The workspace *is* the repository, rather than a directory that happens to
# contain one. Every other task gives its workspace a git repo so a harness that
# navigates by repo map -- aider -- can find the files; this task builds a real
# one already, and starting the agent inside it gives the same property without
# nesting a second repo around the first.
#
# The verifier and the instruction both name /app/repo absolutely, so neither
# depends on this.
WORKDIR /app/repo
