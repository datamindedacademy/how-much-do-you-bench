#!/bin/bash
# The reference implementation, embedded so the oracle needs nothing alongside it.
set -euo pipefail

cat > /app/normalize.py <<'REFERENCE_EOF'
"""Reference solution: normalize the wide survey export into 4 SQLite tables.

The wide tables (qualifications, technology, deepdive) get readable snake_case
column names summarized from the question text instead of the cryptic codes.
"""
from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path

QUAL = {f"Q{i}" for i in range(1, 16)}                      # Q1–Q15
TECH = {"Q16", "Q17", "Q18", "Q19", "Q24", "Q25a", "Q25b", "Q26", "Q27", "Q28", "Q29"}
DROP = {"StartDate", "EndDate", "UID", "PID", "Respondent_Status"}

# Deep-dive answer columns: "{loopN}_Q{21|22|23}{First|Sec|Third}_{opt}". The loop
# index N picks the challenge; the block is the slot; the challenge name is piped
# into Q20First_N / Q20SecHidden_N / Q20ThirdHidden_N.
_ANSCOL = re.compile(r"^(\d+)_Q(21|22|23)(First|Sec|Third)_\d+(?:_1)?$")
_SLOT = {"First": "First", "Sec": "Second", "Third": "Third"}
_HIDDEN = {"First": "Q20First", "Sec": "Q20SecHidden", "Third": "Q20ThirdHidden"}
_QLABEL = {"21": "approaches_tried", "22": "impact", "23": "price"}

# Stop-words dropped when summarizing a question into a short column name.
_STOP = {
    "a", "an", "the", "of", "to", "in", "for", "and", "or", "is", "are", "was",
    "were", "do", "does", "did", "you", "your", "yours", "org", "organization",
    "organizations", "organisation", "organisations", "what", "which", "who",
    "how", "with", "on", "at", "by", "this", "that", "these", "those", "be",
    "as", "it", "its", "from", "when", "where", "their", "they", "them", "s",
    "best", "describes", "following", "please", "select", "all", "apply", "up",
}


def _load(csv_path):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1], rows[2:]                       # codes, questions, data


def _group(code: str) -> str:
    c = re.sub(r"^\d+_", "", code)
    m = re.match(r"(Hidden[A-Za-z0-9]+|Q\d+[a-z]?[A-Za-z]*)", c)
    return m.group(1) if m else c


def _slug(text: str) -> str:
    text = re.sub(r"\[.*?\]", " ", text)                   # drop [Field-1] piping
    text = re.sub(r"[^0-9A-Za-z]+", " ", text).lower()
    return "_".join(text.split())


def _summary(text: str, maxwords: int) -> str:
    words = [w for w in _slug(text).split("_") if w and w not in _STOP]
    return "_".join(words[:maxwords]) or "field"


def _readable_name(code: str, question: str) -> str:
    """A short, readable snake_case name summarizing the question."""
    q = question.replace("\n", " ")
    for junk in ("Selected Choice", "Select all that apply", "Select up to 3"):
        q = q.replace(junk, " ")
    parts = [p.strip() for p in q.split(" - ") if p.strip()]
    stem = parts[0] if parts else code
    option = parts[-1] if len(parts) > 1 else ""

    name = _summary(stem, 6)
    if option and option != stem:
        name += "__" + _summary(option, 4)
    if code.endswith("_TEXT"):
        name += "_other"

    # Disambiguate the looped deep-dive blocks (1_/2_/... and First/Sec/Third).
    loop = re.match(r"^(\d+)_", code)
    block = re.search(r"(First|Sec|Third)", code)
    tag = ""
    if loop:
        tag += f"loop{loop.group(1)}_"
    if block:
        tag += {"First": "c1", "Sec": "c2", "Third": "c3"}[block.group(1)] + "_"
    return tag + name


def _unique(names):
    seen, out = {}, []
    for n in names:
        if n in seen:
            seen[n] += 1
            out.append(f"{n}_{seen[n]}")
        else:
            seen[n] = 1
            out.append(n)
    return out


def _write_wide(con, table, codes, questions, data, uid, member_idx):
    names = _unique(["respondent_id"]
                    + [_readable_name(codes[i], questions[i]) for i in member_idx])
    cols = ", ".join(f'"{n}"' for n in names)
    con.execute(f'DROP TABLE IF EXISTS "{table}"')
    con.execute(f'CREATE TABLE "{table}" ({cols})')
    ph = ", ".join("?" * len(names))
    con.executemany(
        f'INSERT INTO "{table}" VALUES ({ph})',
        ([r[uid]] + [r[i] for i in member_idx] for r in data),
    )


def build_database(csv_path, db_path) -> None:
    codes, questions, data = _load(csv_path)
    code_index = {c: i for i, c in enumerate(codes)}
    uid = code_index["UID"]

    qual_idx, tech_idx, chal = [], [], []
    for i, c in enumerate(codes):
        if c in DROP:
            continue
        if c.startswith("Q20a"):
            if not c.endswith("_TEXT"):
                bcode = "Q20b" + c[len("Q20a"):]
                bi = code_index.get(bcode)
                chal.append((i, questions[i].split(" - ")[-1].strip(), bi))
            continue
        if c.startswith("Q20b"):
            continue                                        # folded into the matrix
        g = _group(c)
        if g in QUAL:
            qual_idx.append(i)
        elif g in TECH:
            tech_idx.append(i)
        # other helper / deep-dive columns are handled by the melt below

    Path(db_path).unlink(missing_ok=True)
    con = sqlite3.connect(str(db_path))
    try:
        _write_wide(con, "qualifications", codes, questions, data, uid, qual_idx)
        _write_wide(con, "technology", codes, questions, data, uid, tech_idx)

        # Priority matrix: one row per respondent, one INTEGER column per
        # challenge (named by the challenge text), each row summing to 100.
        names = ["respondent_id"] + [label for _i, label, _bi in chal]
        coldefs = '"respondent_id" TEXT, ' + ", ".join(
            f'"{label}" INTEGER' for _i, label, _bi in chal)
        con.execute("DROP TABLE IF EXISTS challenges_priorities")
        con.execute(f"CREATE TABLE challenges_priorities ({coldefs})")
        ph = ", ".join("?" * len(names))
        matrix = [
            [r[uid]] + [int(r[bi]) if bi is not None and r[bi].strip() else 0
                        for _i, _label, bi in chal]
            for r in data
        ]
        con.executemany(f"INSERT INTO challenges_priorities VALUES ({ph})", matrix)

        # Deep-dive: tidy (respondent_id, slot, challenge, question, answer), one
        # row per non-empty follow-up answer cell.
        con.execute("DROP TABLE IF EXISTS challenges_priorities_deepdive")
        con.execute("CREATE TABLE challenges_priorities_deepdive "
                    "(respondent_id TEXT, slot TEXT, challenge TEXT, "
                    "question TEXT, answer TEXT)")
        dd_rows = []
        for r in data:
            rid = r[uid]
            for i, c in enumerate(codes):
                m = _ANSCOL.match(c)
                if not m:
                    continue
                answer = r[i].strip()
                if not answer:
                    continue
                loop_n, qnum, block = m.group(1), m.group(2), m.group(3)
                hi = code_index.get(f"{_HIDDEN[block]}_{loop_n}")
                challenge = r[hi].strip() if hi is not None else ""
                dd_rows.append((rid, _SLOT[block], challenge, _QLABEL[qnum], answer))
        con.executemany(
            "INSERT INTO challenges_priorities_deepdive VALUES (?, ?, ?, ?, ?)",
            dd_rows)
        con.commit()
    finally:
        con.close()
REFERENCE_EOF
