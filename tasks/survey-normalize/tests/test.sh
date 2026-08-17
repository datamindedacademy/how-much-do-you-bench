#!/bin/bash
# The grader imports `normalize` from BENCH_TARGET, which is where the candidate
# file lives in this task.
mkdir -p /logs/verifier

BENCH_TARGET=/app python -m pytest /tests/test_normalize.py -rA \
  > /logs/verifier/pytest.log 2>&1
status=$?
tail -40 /logs/verifier/pytest.log

if [ $status -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
