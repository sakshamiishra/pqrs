"""HTTP access to the two specified Elexon dataset stream endpoints."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_cache_lock = asyncio.Lock()
CACHE_SECONDS = 900
TIMEOUT_SECONDS = 45


class ElexonError(RuntimeError):
    pass


async def fetch_dataset(dataset: str, params: dict[str, str]) -> list[dict[str, Any]]:
    key = dataset + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    async with _cache_lock:
        cached = _cache.get(key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(f"{BASE_URL}/{dataset}/stream", params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ElexonError(f"Elexon {dataset} request failed or returned invalid JSON") from exc
    if isinstance(body, dict):
        body = body.get("data")
    if not isinstance(body, list) or any(not isinstance(item, dict) for item in body):
        raise ElexonError(f"Elexon {dataset} returned an unexpected response shape")
    async with _cache_lock:
        _cache[key] = (time.monotonic() + CACHE_SECONDS, body)
    return body


async def fetch_analysis_data() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # FUELHH supports settlement-date filtering; WINDFOR history is queried by
    # publication time. Include 31 Dec because that day's publications may be
    # eligible for the first (2 Jan) delivery day.
    actual_params = {
        "settlementDateFrom": "2026-01-02",
        "settlementDateTo": "2026-02-01",
        "fuelType": "WIND",
    }
    forecast_params = {
        "publishDateTimeFrom": "2025-12-31T00:00:00Z",
        "publishDateTimeTo": "2026-01-31T12:00:00Z",
    }
    return await asyncio.gather(
        fetch_dataset("FUELHH", actual_params),
        fetch_dataset("WINDFOR", forecast_params),
    )
