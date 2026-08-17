"""Cheap to parse, still fans out per partition, and backfillable.

The parse budget is measured rather than linted: any arrangement that keeps the
scan out of module scope passes, and any that does not fails regardless of how it
is written.
"""

import ast
import os
import subprocess
import sys
import time

os.environ.setdefault("AIRFLOW__CORE__DAGS_FOLDER", "/app/dags")
os.environ.setdefault("AIRFLOW__CORE__LOAD_EXAMPLES", "False")

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}" + ("" if ok else f": {detail}"))
    if not ok:
        failures.append(label)


# Parse in a fresh process, so nothing this script already imported warms it up.
probe = subprocess.run(
    [
        sys.executable,
        "-c",
        # Marked output: airflow logs to stdout too, so position is not reliable.
        "import time;"
        "from airflow.models.dagbag import DagBag;"
        "t=time.perf_counter();"
        "b=DagBag(dag_folder='/app/dags', include_examples=False);"
        "print('ELAPSED', time.perf_counter()-t);"
        "print('ERRORS', len(b.import_errors), b.import_errors)",
    ],
    capture_output=True,
    text=True,
)
marked = {
    line.split(" ", 1)[0]: line.split(" ", 1)[1]
    for line in (probe.stdout or "").splitlines()
    if line.startswith(("ELAPSED ", "ERRORS "))
}
if "ELAPSED" not in marked:
    check("dag parses", False, (probe.stderr or probe.stdout)[-400:])
else:
    elapsed = float(marked["ELAPSED"])
    errors = marked.get("ERRORS", "0")
    check("dag parses", errors.startswith("0 "), errors[:300])
    check("parse is cheap", elapsed < 3.0, f"parsing took {elapsed:.1f}s")
    print(f"     parse time: {elapsed:.2f}s")

from airflow.models.dagbag import DagBag  # noqa: E402

bag = DagBag(dag_folder="/app/dags", include_examples=False)
dag = bag.dags.get("partitioned_load")
check("dag present", dag is not None, str(sorted(bag.dag_ids)))

if dag is not None:
    # Fan-out has to survive: one unit of work per partition, decided at run time.
    mapped = [t for t in dag.tasks if getattr(t, "is_mapped", False)]
    check(
        "work still fans out per partition",
        bool(mapped),
        f"no mapped task; tasks are {[t.task_id for t in dag.tasks]}",
    )
    check(
        "partitions are not hard-coded as tasks",
        len(dag.tasks) < 12,
        f"{len(dag.tasks)} tasks, which is one per partition at parse time",
    )
    check("catchup is off", dag.catchup is False, f"catchup={dag.catchup}")

# A start_date that moves on every parse has no fixed point to backfill from.
source = open("/app/dags/partitioned_load.py").read()
moving = [
    node.func.attr
    for node in ast.walk(ast.parse(source))
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Attribute)
    and node.func.attr in {"now", "today", "utcnow"}
]
check("start date is fixed", not moving, f"start_date still derives from {moving}")

# Airflow 3 already defaults catchup to False, so reading dag.catchup says nothing
# about whether this DAG stated its intent. The source has to.
declared = any(
    kw.arg == "catchup"
    for node in ast.walk(ast.parse(source))
    if isinstance(node, ast.Call)
    for kw in node.keywords
)
check("backfill behaviour is declared", declared, "no catchup= anywhere in the DAG file")

sys.exit(1 if failures else 0)
