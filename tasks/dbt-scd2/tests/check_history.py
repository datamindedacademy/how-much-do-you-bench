"""One version per real change, and a departure that closes the record.

The feed is a full extract with no change tracking: customer 1 never changes,
customer 2 changes tier once on day 2, customer 3 disappears on day 3. Anything
else in the history is the pipeline inventing changes or missing a departure.
"""

import sys

import duckdb

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {label}" + ("" if ok else f": {detail}"))
    if not ok:
        failures.append(label)


con = duckdb.connect("/app/warehouse.duckdb", read_only=True)

tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
check("snapshot exists", "customers_snapshot" in tables, str(sorted(tables)))

if "customers_snapshot" in tables:
    cols = {r[0].lower() for r in con.execute("DESCRIBE customers_snapshot").fetchall()}
    check("snapshot has scd columns", {"dbt_valid_from", "dbt_valid_to"} <= cols, str(sorted(cols)))

    rows = con.execute(
        "SELECT customer_id, count(*) FROM customers_snapshot GROUP BY 1 ORDER BY 1"
    ).fetchall()
    versions = dict(rows)

    # Customer 1 never changed. A row per ingest means the snapshot is keying on
    # the load timestamp rather than on the customer's own attributes.
    check("customer 1 has one version", versions.get(1) == 1, f"has {versions.get(1)}")

    # Customer 2 changed tier exactly once, so two versions: bronze-era and after.
    check("customer 2 has two versions", versions.get(2) == 2, f"has {versions.get(2)}")

    # Customer 2's old version must be closed, and the new one current.
    closed = con.execute(
        "SELECT count(*) FROM customers_snapshot "
        "WHERE customer_id = 2 AND dbt_valid_to IS NOT NULL"
    ).fetchone()[0]
    check("customer 2 history is closed off", closed == 1, f"{closed} closed rows")

    current_tier = con.execute(
        "SELECT tier FROM customers_snapshot "
        "WHERE customer_id = 2 AND dbt_valid_to IS NULL"
    ).fetchall()
    check("customer 2 current tier is gold", current_tier == [("gold",)], str(current_tier))

    # Customer 3 left the feed. Either representation is fine -- the record is
    # closed, or a row marks the deletion -- as long as nothing still reads as
    # current and active.
    open_and_active = con.execute(
        "SELECT count(*) FROM customers_snapshot "
        "WHERE customer_id = 3 AND dbt_valid_to IS NULL"
        # dbt_is_deleted comes back as VARCHAR on duckdb, so it is compared as
        # text rather than coalesced against a boolean.
        + (
            " AND lower(coalesce(CAST(dbt_is_deleted AS VARCHAR), 'false')) <> 'true'"
            if "dbt_is_deleted" in cols
            else ""
        )
    ).fetchone()[0]
    check(
        "customer 3 is no longer current",
        open_and_active == 0,
        f"{open_and_active} rows still current for a customer who left the feed",
    )

con.close()
sys.exit(1 if failures else 0)
