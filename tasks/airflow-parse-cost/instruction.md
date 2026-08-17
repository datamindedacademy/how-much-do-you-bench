The scheduler is spending most of its time on one DAG.

`partitioned_load` in `/app/dags` processes one partition of `/app/feed/events.csv`
per task. To know which partitions exist, it reads the feed. That read happens
while the file is being parsed, which the scheduler does every few seconds for
every DAG it knows about -- so a 38MB scan runs continuously, and the scheduler
has less and less time for everything else.

Fix that without giving up the per-partition parallelism: the work must still be
split into one unit per partition, discovered from the feed rather than
hard-coded, so a new partition appearing in the feed is picked up without a code
change.

Two other things in this file will bite later:

- The DAG cannot be backfilled. Its history moves every time the file is parsed,
  so there is no fixed point to backfill from.
- Whether it backfills on deploy is currently left to the cluster's default. Say
  what this DAG wants, in the DAG.

Constraints:

- Keep the DAG id `partitioned_load`.
- Do not edit `/app/feed/events.csv`, and do not hard-code the partition names.
- Parsing `/app/dags` must take under three seconds.
