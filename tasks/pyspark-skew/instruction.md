Finance says our revenue report is overstated, and they are right: the total in
`/app/out/revenue.parquet` is higher than the money that actually came in.

`/app/job.py` joins the event stream to the customer dimension and aggregates by
segment and country. The events are the source of truth: every event happened once
and its amount should be counted once.

Make the report reconcile: the revenue it totals must equal the total amount in
the events, and the events it counts must equal the number of events. Nothing may
be counted twice, and nothing may be dropped.

Where a customer cannot be identified at all, count the event under segment
`unknown` and country `unknown` rather than discarding it -- finance would rather
see unattributed revenue than a total that does not add up.

Attribute each event to what we currently believe about that customer.

Constraints:

- Do not edit anything under `/app/data`.
- `python /app/job.py` must remain the way it is run, reading and writing the same
  paths.
- Keep the output columns `segment`, `country`, `revenue`, `events`.
