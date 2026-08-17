"""The producer: accepts submissions, enqueues rollouts, serves the dashboard.

Deliberately cannot consume the queue or write rollout rows. Those belong to
the worker, and the IAM policy enforces the split rather than trusting this
module to behave.
"""

import json
import os
import re
import uuid
from pathlib import Path

import boto3
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from common import results
from common.scoring import accuracy_board, contenders, pareto

QUEUE_URL = os.environ["QUEUE_URL"]
TASKS = os.environ.get("TASKS", "incremental-dupes").split(",")
MAX_SUBMISSIONS = int(os.environ.get("MAX_SUBMISSIONS", "5"))
# Where the trajectory viewer is served. Empty when it is not deployed, which
# the dashboard reads as "render no trace links" rather than dead ones.
VIEWER_URL = os.environ.get("VIEWER_URL", "").rstrip("/")

sqs = boto3.client("sqs", region_name=results.region())
table = results.table()

app = FastAPI()


class SubmitRequest(BaseModel):
    team: str
    repo_url: str
    commit: str


@app.post("/submit")
def submit(request: SubmitRequest):
    # Full hash only. GitHub serves a fetch-by-object request for a full SHA
    # and nothing else, so an abbreviated one is not a shorter way to say the
    # same thing: it is four rollouts that fail on checkout twenty minutes from
    # now. `make submit` derives this, which is why it exists.
    if not re.fullmatch(r"[0-9a-f]{40}", request.commit):
        raise HTTPException(
            400,
            "commit must be the full 40-character SHA. Submit with: make submit TEAM=your-team",
        )

    used = _submission_count(request.team)
    if used >= MAX_SUBMISSIONS:
        raise HTTPException(
            429, f"team {request.team} has used all {MAX_SUBMISSIONS} submissions"
        )

    submission_id = f"{request.team}-{uuid.uuid4().hex[:8]}"

    # Written before enqueueing, so a submission is never invisible while its
    # rollouts are already running.
    table.put_item(
        Item=results.meta_item(
            submission_id=submission_id,
            team=request.team,
            repo_url=request.repo_url,
            commit=request.commit,
            task_count=len(TASKS),
        )
    )

    for task_id in TASKS:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(
                {
                    "submission_id": submission_id,
                    "task_id": task_id,
                    "team": request.team,
                    "repo_url": request.repo_url,
                    "commit": request.commit,
                }
            ),
        )

    return {
        "submission_id": submission_id,
        "tasks_queued": len(TASKS),
        "submissions_remaining": MAX_SUBMISSIONS - used - 1,
    }


def _submission_count(team: str) -> int:
    return sum(
        1
        for item in results.scan(table)
        if item.get("task_id") == results.META and item.get("team") == team
    )


@app.get("/results")
def results_endpoint():
    submissions = results.summarise(results.scan(table))

    # A submission still running has an artificially low token count and an
    # artificially low score, so it can neither dominate nor be dominated yet.
    def finished(s: dict) -> bool:
        return s["completed"] >= s["task_count"] > 0

    scored = [s for s in submissions if finished(s)]
    running = [s for s in submissions if not finished(s)]
    return {
        "submissions": accuracy_board(submissions),
        "pareto": pareto(scored),
        "contenders": contenders(running, scored),
        "viewer_url": VIEWER_URL,
    }


# The built Svelte app. Mounted last so it does not shadow the API routes.
#
# no-cache means revalidate, not don't store: with the ETag StaticFiles already
# sends, an unchanged file costs a 304. Without it browsers apply heuristic
# freshness to index.html and a tab left open across a deploy keeps asking for
# a bundle hash that no longer exists.
class Dashboard(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["cache-control"] = "no-cache"
        return response


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/", Dashboard(directory=STATIC_DIR, html=True), name="dashboard")
