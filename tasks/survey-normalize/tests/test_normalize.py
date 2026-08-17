"""Hidden grader for exercise 15: normalize the survey into a 4-table SQLite db
with readable, summarized column names on the wide tables."""
import csv
import importlib
import sqlite3

import pytest

UID0 = "31ba5b66-dea6-445e-b8cf-665991451f90"   # first respondent
# A respondent whose *single* deep-dive slot covers two challenges (the loop ran
# for two challenges in the same slot). Solutions that assume one challenge per
# slot silently drop the second one.
UID_MULTI = "3cdae85b-7903-4df0-9b19-c0693c5e9f1d"

REVENUE = {"€10M - €50M", "€100M - €1B", "More than €1B",
           "€50M - €100M", "€1M - €10M", "Less than €1M"}
INDUSTRIES = {"Financial Services", "Technology, Media & Telecommunications", "Retail"}


@pytest.fixture(scope="session")
def con(target_dir, tmp_path_factory):
    mod = importlib.import_module("normalize")
    db = tmp_path_factory.mktemp("db") / "survey.sqlite"
    mod.build_database(target_dir / "quant151.csv", db)
    assert db.exists() and db.stat().st_size > 0, "no database file was written"
    c = sqlite3.connect(str(db))
    yield c
    c.close()


@pytest.fixture(scope="session")
def original_codes(target_dir):
    with open(target_dir / "quant151.csv", encoding="utf-8-sig", newline="") as f:
        return set(next(csv.reader(f)))


def _tables(con):
    return {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def _cols(con, table):
    return {r[1] for r in con.execute(f'PRAGMA table_info("{table}")')}


def _count(con, table):
    return con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


def _dump(con, table):
    cur = con.execute(f'SELECT * FROM "{table}"')
    names = [d[0] for d in cur.description]
    return names, cur.fetchall()


def _find_col(names, rows, predicate):
    """Name of the first non-id column whose distinct values satisfy predicate."""
    for j, name in enumerate(names):
        if name == "respondent_id":
            continue
        vals = {r[j] for r in rows if r[j] not in (None, "")}
        if vals and predicate(vals):
            return name
    return None


def _r0(names, rows):
    j = names.index("respondent_id")
    return next(r for r in rows if r[j] == UID0)


def test_four_tables_exist(con):
    assert _tables(con) >= {
        "qualifications", "technology",
        "challenges_priorities",
    }


def test_qualifications_readable(con, original_codes):
    names, rows = _dump(con, "qualifications")
    assert "respondent_id" in names
    assert _count(con, "qualifications") == 151
    # columns were renamed away from the cryptic codes
    assert set(names).isdisjoint(original_codes)

    r0 = _r0(names, rows)
    # revenue column: found by its data, must read as 'revenue' and hold Q1's value
    rev = _find_col(names, rows, lambda v: len(v) >= 3 and v <= REVENUE)
    assert rev and "revenue" in rev.lower(), f"no readable revenue column (got {rev!r})"
    assert r0[names.index(rev)] == "€10M - €50M"
    # industry column likewise
    ind = _find_col(names, rows, lambda v: INDUSTRIES <= v)
    assert ind and "industr" in ind.lower(), f"no readable industry column (got {ind!r})"
    assert r0[names.index(ind)] == "Financial Services"


def test_technology_readable(con, original_codes):
    names, rows = _dump(con, "technology")
    assert _count(con, "technology") == 151
    assert set(names).isdisjoint(original_codes)
    low = [n.lower() for n in names if n != "respondent_id"]
    assert any("vendor" in n for n in low), "expected a readable 'vendor' column"
    assert any("tool" in n for n in low), "expected a readable 'tool' column"
    # firmographics (revenue) must not have leaked into technology
    assert _find_col(names, rows, lambda v: len(v) >= 3 and v <= REVENUE) is None


def test_challenges_priorities_matrix(con):
    cols = _cols(con, "challenges_priorities")
    assert cols >= {
        "respondent_id",
        "Aligning data initiatives with business strategy",
        "Cost management", "Data quality", "Data governance implementation",
    }
    assert len(cols) == 24                                  # respondent_id + 23
    assert _count(con, "challenges_priorities") == 151

    row = con.execute(
        'SELECT "Cost management", '
        '"Aligning data initiatives with business strategy", "Data quality" '
        'FROM challenges_priorities WHERE respondent_id = ?', (UID0,)).fetchone()
    assert row == (20, 25, 0)                               # integers, Data quality not picked

    cur = con.execute("SELECT * FROM challenges_priorities")
    names = [d[0] for d in cur.description]
    id_pos = names.index("respondent_id")
    n_full = 0
    for r in cur.fetchall():
        total = sum(int(v) for j, v in enumerate(r) if j != id_pos)
        assert total in (0, 100), f"a row sums to {total}, expected 0 or 100"
        n_full += total == 100
    assert n_full == 149


def test_joins(con):
    def ids(t):
        return {r[0] for r in con.execute(f'SELECT respondent_id FROM "{t}"')}
    base = ids("qualifications")
    assert len(base) == 151
    assert ids("technology") == base
    assert ids("challenges_priorities") <= base
