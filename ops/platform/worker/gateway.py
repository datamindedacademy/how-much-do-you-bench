"""Client for the LiteLLM gateway's key-management API.

A key is minted per rollout and retired after it, which is what makes token
counts attributable server-side. Anything the agent reports is self-reported by
the party being scored.

These routes need Postgres; without DATABASE_URL the proxy answers
/key/generate with "DB not connected".
"""

import os
from typing import Any

import requests

BASE = os.environ.get("GATEWAY_ADMIN_URL", "http://127.0.0.1:4000").rstrip("/")
MASTER_KEY = os.environ.get("LITELLM_MASTER_KEY", "sk-local-dev")
MODEL = os.environ.get("MODEL", "gemma")

TIMEOUT = 30
HEADERS = {"Authorization": f"Bearer {MASTER_KEY}"}


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"{BASE}{path}", json=payload, headers=HEADERS, timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def _get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        f"{BASE}{path}", params=params, headers=HEADERS, timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def mint_key(alias: str, rpm: int | None = None) -> dict:
    """One key per rollout, rate limited so a runaway loop cannot starve the queue."""
    payload: dict[str, Any] = {"key_alias": alias, "models": [MODEL]}
    if rpm is not None:
        payload["rpm_limit"] = rpm
    return _post("/key/generate", payload)


def _rows(key: str) -> list[dict]:
    """Every request this key made, newest first is not guaranteed."""
    rows = _get("/spend/logs", {"api_key": key})
    if isinstance(rows, dict):
        rows = rows.get("data", [])
    return rows


def usage_for_key(key: str) -> dict[str, int | float]:
    """Server-side token counts for one key, summed over its requests.

    /key/info carries spend but no token breakdown, so the per-request spend
    log is the source. Counts are the gateway's, not the agent's.
    """
    rows = _rows(key)

    return {
        "tokens_in": sum(int(r.get("prompt_tokens") or 0) for r in rows),
        "tokens_out": sum(int(r.get("completion_tokens") or 0) for r in rows),
        "spend_usd": round(sum(float(r.get("spend") or 0.0) for r in rows), 6),
        "requests": len(rows),
    }


def delete_key(key: str) -> None:
    _post("/key/delete", {"keys": [key]})
