Support cannot answer two questions from our customer history, and both should be
easy.

`/app/run_pipeline.sh` replays three days of the CRM feed from a clean warehouse
and snapshots it into `customers_snapshot`. The feed is a full extract each day:
whatever the CRM holds that morning, with no change tracking of its own.

**"When did this customer's tier change?"** The history says every customer
changed every day. Only one of them actually changed anything across the three
days. History should record a new version of a customer when something about that
customer changes, and not otherwise.

**"Is this customer still with us?"** One customer disappears from the feed on the
last day. The history still shows them as current, indistinguishable from an
active customer. A customer who leaves the feed must be visibly closed off in the
history rather than left open forever.

Constraints:

- Do not edit anything under `/app/feed`, and do not change what
  `run_pipeline.sh` loads.
- `/app/run_pipeline.sh` must still rebuild the warehouse from scratch. It will
  be run from a clean state to check your work, so writing rows into the
  warehouse by hand will not help.
- Keep the snapshot named `customers_snapshot` and keyed on `customer_id`.
