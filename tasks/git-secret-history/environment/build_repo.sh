#!/bin/bash
# Builds the repository at image build time: a credential committed early, later
# deleted, with real work layered on top of it.
set -euo pipefail

export GIT_AUTHOR_NAME=dev GIT_AUTHOR_EMAIL=dev@example.com
export GIT_COMMITTER_NAME=dev GIT_COMMITTER_EMAIL=dev@example.com

rm -rf /app/repo && mkdir -p /app/repo && cd /app/repo
git init -q -b main

printf 'name: pipeline\n' > README.md
git add . && git commit -qm "initial commit"

printf 'def load():\n    return "ok"\n' > loader.py
git add . && git commit -qm "add loader"

mkdir -p config
printf 'warehouse:\n  host: db.internal\n  api_key: sk-live-9f8271bd4c0a4e1fa77b\n' > config/secrets.yml
git add . && git commit -qm "wire up warehouse credentials"

printf 'def load():\n    return "ok"\n\n\ndef transform(rows):\n    return [r for r in rows if r]\n' > loader.py
git add . && git commit -qm "add transform step"

git rm -q config/secrets.yml
mkdir -p config  # git rm took the last file with it, and the directory too
printf 'warehouse:\n  host: db.internal\n  api_key: ${WAREHOUSE_API_KEY}\n' > config/settings.yml
git add . && git commit -qm "move the credential out of the repo"

printf 'def load():\n    return "ok"\n\n\ndef transform(rows):\n    return [r for r in rows if r]\n\n\ndef publish(rows):\n    return len(rows)\n' > loader.py
printf 'pytest\n' > requirements.txt
git add . && git commit -qm "add publish step and pin deps"

# A release branch cut while the credential was still committed, plus a tag on
# the same commit. Rewriting main alone leaves both of them holding the blob.
git branch release/2026-07 HEAD~2
git tag v0.1 HEAD~3
