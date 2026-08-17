"""The results table: its shape, and the two ways it is used.

This is the contract between the two services. The worker writes rows, the API
reads them, and if they disagree about a field name the disagreement shows up
during the event rather than in a test. Keeping the shape in one module is the
reason `common` exists at all.

Rows are keyed `submission_id` / `task_id`. The sentinel task id `_meta` holds
the submission itself; every other row is one rollout.
"""

import os
from datetime import UTC, datetime
from typing import Any

import boto3

META = "_meta"

# Written by the worker, read by the API. Absent keys are omitted rather than
# stored as null, because DynamoDB charges for what you write.
ROLLOUT_FIELDS = (
    "tokens_in",
    "tokens_out",
    "job_dir",
    "error",
    "rewards",
    "requests",
)


def region() -> str:
    """Explicit, because a profile's own region silently outranks AWS_REGION
    and the resources live beside Gemma in eu-central-1."""
    return os.environ.get("BENCHMARK_REGION", "eu-central-1")


def table(name: str | None = None):
    name = name or os.environ["RESULTS_TABLE"]
    return boto3.resource("dynamodb", region_name=region()).Table(name)


def scan(tbl) -> list[dict]:
    """Every row, following pagination.

    At ~50 submissions x 20 tasks this is a single page. Revisit at ten times
    that, when it becomes worth a secondary index.
    """
    items: list[dict] = []
    kwargs: dict[str, Any] = {}
    while True:
        page = tbl.scan(**kwargs)
        items.extend(page["Items"])
        if "LastEvaluatedKey" not in page:
            return items
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def meta_item(submission_id: str, team: str, repo_url: str, commit: str, task_count: int) -> dict:
    return {
        "submission_id": submission_id,
        "task_id": META,
        "team": team,
        "repo_url": repo_url,
        "commit": commit,
        "task_count": task_count,
        "created_at": datetime.now(UTC).isoformat(),
    }


def rollout_item(job: dict, result: dict) -> dict:
    """One finished rollout, ready to write.

    Floats are stored as strings: DynamoDB has no float type, and rounding a
    duration or a spend into a Decimal loses precision in a way that only
    surfaces when the numbers are added up.
    """
    item = {
        "submission_id": job["submission_id"],
        "task_id": job["task_id"],
        "team": job["team"],
        "commit": job["commit"],
        "status": result.get("status"),
        "passed": bool(result.get("passed")),
        "duration_s": str(result.get("duration_s") or 0),
    }
    for field in ROLLOUT_FIELDS:
        if result.get(field) is not None:
            item[field] = result[field]
    if result.get("spend_usd") is not None:
        item["spend_usd"] = str(result["spend_usd"])
    return item


def summarise(items: list[dict]) -> list[dict]:
    """Collapse rows into one record per submission, as the dashboard wants it."""
    meta: dict[str, dict] = {}
    rollouts: dict[str, list[dict]] = {}

    for item in items:
        if item["task_id"] == META:
            meta[item["submission_id"]] = item
        else:
            rollouts.setdefault(item["submission_id"], []).append(item)

    submissions = []
    for submission_id, info in meta.items():
        done = rollouts.get(submission_id, [])
        submissions.append(
            {
                "submission_id": submission_id,
                "team": info["team"],
                "commit": info["commit"][:8],
                "created_at": info.get("created_at"),
                "task_count": int(info.get("task_count", 0)),
                "completed": len(done),
                "passed": sum(1 for r in done if r.get("passed")),
                "tokens": sum(
                    int(r.get("tokens_in") or 0) + int(r.get("tokens_out") or 0)
                    for r in done
                ),
                # Summed, not wall clock: rollouts of one submission run on
                # whichever workers are free, so elapsed time measures how busy
                # the fleet was. The sum is the agent time the submission cost,
                # which is the part that belongs to the submission.
                "duration_s": sum(float(r.get("duration_s") or 0) for r in done),
                "tasks": sorted(
                    (
                        {
                            "task_id": r["task_id"],
                            "passed": bool(r.get("passed")),
                            "status": r.get("status"),
                            "duration_s": float(r.get("duration_s") or 0),
                            "job_dir": r.get("job_dir"),
                            "error": r.get("error"),
                        }
                        for r in done
                    ),
                    key=lambda t: t["task_id"],
                ),
            }
        )
    return submissions
