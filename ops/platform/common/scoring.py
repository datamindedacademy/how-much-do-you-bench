"""Ranking rules. The only part of the platform with logic worth getting wrong.

Kept apart from api.py so it can be tested without AWS.
"""


def _dominates(a: dict, b: dict) -> bool:
    """`a` beat `b`: at least as good on both axes and strictly better on one."""
    return (
        a["passed"] >= b["passed"]
        and a["tokens"] <= b["tokens"]
        and (a["passed"] > b["passed"] or a["tokens"] < b["tokens"])
    )


def pareto(submissions: list[dict]) -> list[str]:
    """Submission ids nobody beats on passed and tokens at the same time.

    A submission is dominated when another passed at least as many tasks using
    no more tokens, and was strictly better on one of the two.
    """
    # Spending nothing is not winning: a rollout that died before its first
    # model call records zero tokens, and nothing beats zero on cost.
    ran = [s for s in submissions if s["tokens"] > 0]
    return [
        c["submission_id"]
        for c in ran
        if not any(_dominates(o, c) for o in ran)
    ]


def contenders(pending: list[dict], finished: list[dict]) -> list[str]:
    """Running submissions nobody has already beaten on both axes.

    A live run pushing the boundary is the interesting moment, but its score
    can still climb and its spend can only grow, so this is a provisional claim
    and never enters the ranking. Here rather than in the dashboard so the
    dominance rule has one implementation instead of one per language.
    """
    return [
        p["submission_id"]
        for p in pending
        if p["tokens"] > 0 and not any(_dominates(f, p) for f in finished)
    ]


def accuracy_board(submissions: list[dict]) -> list[dict]:
    """Most tasks passed, ties broken by fewer tokens."""
    return sorted(submissions, key=lambda s: (-s["passed"], s["tokens"]))



def _demo() -> None:
    subs = [
        {"submission_id": "a", "passed": 15, "tokens": 200_000},
        {"submission_id": "b", "passed": 15, "tokens": 120_000},  # beats a outright
        {"submission_id": "c", "passed": 8, "tokens": 20_000},  # cheap but weaker
        {"submission_id": "d", "passed": 1, "tokens": 2_000},  # gave up
        {"submission_id": "e", "passed": 8, "tokens": 60_000},  # beaten by c
    ]

    frontier = pareto(subs)
    assert frontier == ["b", "c", "d"], frontier
    assert "a" not in frontier, "a is dominated by b on both axes"
    assert "e" not in frontier, "e is dominated by c on both axes"

    assert [s["submission_id"] for s in accuracy_board(subs)] == ["b", "a", "c", "e", "d"]

    # A tie on both axes leaves both on the frontier rather than dropping one.
    tied = [
        {"submission_id": "x", "passed": 5, "tokens": 100},
        {"submission_id": "y", "passed": 5, "tokens": 100},
    ]
    assert pareto(tied) == ["x", "y"]

    assert pareto([]) == []

    # A submission that never ran spends nothing, and nothing beats nothing on
    # cost. It must not take the frontier from teams that actually ran.
    crashed = {"submission_id": "crashed", "passed": 0, "tokens": 0}
    assert "crashed" not in pareto([*subs, crashed])
    assert contenders([crashed], subs) == []

    # A running submission is a contender only until someone finished beats it.
    live = [{"submission_id": "live", "passed": 4, "tokens": 5_000}]
    assert contenders(live, subs) == ["live"], "nobody has beaten it on both axes"
    assert contenders(live, [{"submission_id": "z", "passed": 9, "tokens": 1_000}]) == []

    print("scoring ok")


if __name__ == "__main__":
    _demo()
