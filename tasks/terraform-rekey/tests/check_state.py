"""Rekeyed by name, nothing destroyed, legacy released rather than deleted."""

import json
import pathlib
import subprocess
import sys

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}" + ("" if ok else f": {detail}"))
    if not ok:
        failures.append(label)


def tf(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["terraform", *args], cwd="/app", capture_output=True, text=True
    )


# 1. Nothing left to do. -detailed-exitcode returns 2 when a plan has changes,
#    which is the whole point: a migration that still wants to destroy something
#    has not been done, however tidy the config looks.
#
#    -refresh=false because drift alone also returns 2: a plan that reports
#    "0 to add, 0 to change, 0 to destroy" still exits 2 when a managed file was
#    touched out of band, and a correct migration was failing on that. The files
#    are evidence for checks 2 and 3, which read them directly and far more
#    precisely than a refresh does.
plan = tf("plan", "-detailed-exitcode", "-refresh=false", "-input=false", "-no-color")
check(
    "plan is clean",
    plan.returncode == 0,
    f"exit {plan.returncode}: {(plan.stdout + plan.stderr).strip()[-400:]}",
)

# 2. The files are the evidence. A destroy-and-recreate leaves the content
#    identical and the mtime different, so mtime is what gets checked.
baseline = json.loads(pathlib.Path("/opt/baseline.json").read_text())
for name, want in sorted(baseline.items()):
    p = pathlib.Path("/app/envs") / name
    if not p.exists():
        check(f"{name} still exists", False, "file is gone")
        continue
    # Whole seconds: the image layer is a tarball and tar drops sub-second
    # precision, so a nanosecond baseline would never match its own file.
    check(f"{name} untouched", int(p.stat().st_mtime) == want["mtime"], "mtime changed")
    check(f"{name} content intact", p.read_text() == want["content"], "content changed")

# 3. Addresses carry names, not positions, and legacy is no longer managed.
show = tf("show", "-json")
if show.returncode != 0:
    check("state readable", False, show.stderr.strip()[-200:])
else:
    state = json.loads(show.stdout or "{}")
    resources = (state.get("values") or {}).get("root_module", {}).get("resources", [])
    addresses = [r.get("address", "") for r in resources]
    check("state has resources", bool(addresses), "state is empty")
    check(
        "keyed by name",
        all("[\"" in a for a in addresses),
        f"still positional: {addresses}",
    )
    check(
        "legacy released",
        not any("legacy" in a for a in addresses),
        f"legacy is still managed: {addresses}",
    )

# 4. The guard. Checked last: a test written with `command = apply` mutates the
#    files it manages, and the mtime evidence above has to be read before that.
tests = list(pathlib.Path("/app").rglob("*.tftest.hcl"))
check("a terraform test exists", bool(tests), "no *.tftest.hcl anywhere under /app")

if tests:
    run = tf("test", "-no-color")
    out = (run.stdout + run.stderr).strip()
    check("terraform test passes", run.returncode == 0, out[-400:])
    check("the test actually asserts something", "0 passed" not in out, out[-200:])

sys.exit(1 if failures else 0)
