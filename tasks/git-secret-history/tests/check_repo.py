"""The secret must be unrecoverable, and the work must still be there."""

import subprocess
import sys

SECRET = "sk-live-9f8271bd4c0a4e1fa77b"
failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}" + ("" if ok else f": {detail}"))
    if not ok:
        failures.append(label)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", "/app/repo", *args], capture_output=True, text=True
    )


# Every object still reachable, not just every commit on main: a rewrite that
# leaves the old commits dangling has not removed anything yet.
grep = git("grep", "-r", SECRET, "--all-match", "--", ".")
reachable = git("log", "--all", "-p", "-S", SECRET, "--oneline")
check("secret absent from working tree", grep.returncode != 0, grep.stdout[:200])
check(
    "secret absent from reachable history",
    not reachable.stdout.strip(),
    f"still introduced by: {reachable.stdout.strip()[:200]}",
)

# The strong form: nothing recoverable at all, including unreferenced objects.
objects = subprocess.run(
    "cd /app/repo && git rev-list --objects --all | cut -d' ' -f1 | "
    "xargs -r -n 50 git cat-file --batch 2>/dev/null | grep -c " + SECRET,
    shell=True, capture_output=True, text=True,
)
count = (objects.stdout or "0").strip() or "0"
check("secret absent from all objects", count == "0", f"{count} objects still contain it")

# The tree that matters.
tracked = sorted((git("ls-files").stdout or "").split())
check(
    "working tree intact",
    tracked == ["README.md", "config/settings.yml", "loader.py", "requirements.txt"],
    str(tracked),
)
loader = git("show", "HEAD:loader.py").stdout
for fn in ("def load(", "def transform(", "def publish("):
    check(f"loader keeps {fn}...)", fn in loader, "missing from HEAD")

settings = git("show", "HEAD:config/settings.yml").stdout
check("settings still reference the env var", "WAREHOUSE_API_KEY" in settings, settings[:120])

# The history itself: the later work has to remain separate commits.
commits = [c for c in (git("log", "--format=%s").stdout or "").splitlines() if c.strip()]
check("history is not squashed", len(commits) >= 4, f"{len(commits)} commits on main")
check(
    "later work still in history",
    any("publish" in c for c in commits) and any("transform" in c for c in commits),
    str(commits),
)
# The other refs have to survive the rewrite, not be deleted to pass the scan.
refs = (git("for-each-ref", "--format=%(refname)").stdout or "")
check("release branch kept", "refs/heads/release/2026-07" in refs, refs)
check("tag kept", "refs/tags/v0.1" in refs, refs)

check("still on main", (git("rev-parse", "--abbrev-ref", "HEAD").stdout or "").strip() == "main")

sys.exit(1 if failures else 0)
