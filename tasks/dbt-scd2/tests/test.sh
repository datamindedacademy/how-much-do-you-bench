#!/bin/bash
mkdir -p /logs/verifier

bash /app/run_pipeline.sh > /logs/verifier/pipeline.log 2>&1 || \
  echo "run_pipeline.sh exited non-zero" >> /logs/verifier/pipeline.log

python /tests/check_history.py > /logs/verifier/checks.log 2>&1
status=$?
cat /logs/verifier/checks.log
if [ $status -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
