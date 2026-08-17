#!/bin/bash
# The feed carries no change tracking, so timestamp/loaded_at makes every ingest
# look like a change. The check strategy compares the customer's own attributes
# instead, and hard_deletes closes the record of a customer who leaves the feed.
set -euo pipefail

cat > /app/pipeline/snapshots/customers_snapshot.yml <<'YML'
snapshots:
  - name: customers_snapshot
    relation: source('crm', 'raw_customers')
    config:
      unique_key: customer_id
      strategy: check
      check_cols: ["name", "tier"]
      hard_deletes: new_record
YML
