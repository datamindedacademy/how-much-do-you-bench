#!/bin/bash
# Rewrite every commit to drop the file, then make the old objects unrecoverable:
# expiring the reflog and pruning is the part that turns a rewrite into a removal.
set -euo pipefail

cd /app/repo
export FILTER_BRANCH_SQUELCH_WARNING=1

git filter-branch --force --index-filter \
  'git rm -r --cached --ignore-unmatch config/secrets.yml' \
  --prune-empty --tag-name-filter cat -- --all

rm -rf .git/refs/original
git reflog expire --expire=now --all
git gc --prune=now --aggressive >/dev/null 2>&1
