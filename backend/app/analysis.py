"""Forecast selection, interval matching, and accuracy metrics."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite, sqrt
from typing import Any, Iterable
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")
UTC = timezone.utc
DECISION_DATES_START = date(2026, 1, 1)
DECISION_DATES_END = date(2026, 1, 31)
DECISION_CUTOFF = time(12, 0)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def _records_for_interval(rows: Iterable[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], int]:
    """Deduplicate each delivery interval deterministically; latest publish wins."""
    chosen: dict[str, dict[str, Any]] = {}
    duplicates = 0
    for row in rows:
        start = parse_timestamp(row.get("startTime"))
        if start is None:
            continue
        key = start.isoformat()
        previous = chosen.get(key)
        if previous is not None:
            duplicates += 1
        current_publish = parse_timestamp(row.get("publishTime")) or datetime.min.replace(tzinfo=UTC)
        previous_publish = parse_timestamp(previous.get("publishTime")) if previous else None
        if previous is None or current_publish > (previous_publish or datetime.min.replace(tzinfo=UTC)) or (
            current_publish == previous_publish and repr(sorted(row.items())) < repr(sorted(previous.items()))
        ):
            chosen[key] = row
    return chosen, duplicates


def expected_intervals() -> list[dict[str, datetime | str]]:
    """Intervals on delivery days following January 2026 decision dates."""
    intervals: list[dict[str, datetime | str]] = []
    for day_offset in range((DECISION_DATES_END - DECISION_DATES_START).days + 1):
        decision_day = DECISION_DATES_START + timedelta(days=day_offset)
        delivery_day = decision_day + timedelta(days=1)
        cutoff = datetime.combine(decision_day, DECISION_CUTOFF, tzinfo=LONDON).astimezone(UTC)
        local_start = datetime.combine(delivery_day, time.min, tzinfo=LONDON).astimezone(UTC)
        local_end = datetime.combine(delivery_day + timedelta(days=1), time.min, tzinfo=LONDON).astimezone(UTC)
        instant = local_start
        period = 1
        while instant < local_end:
            intervals.append({
                "startTime": instant,
                "decisionDate": decision_day.isoformat(),
                "deliveryDate": delivery_day.isoformat(),
                "settlementPeriod": period,
                "cutoff": cutoff,
            })
            instant += timedelta(minutes=30)
            period += 1
    return intervals


def analyze(actual_rows: list[dict[str, Any]], forecast_rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected = expected_intervals()
    actual_candidates = [r for r in actual_rows if str(r.get("fuelType", "")).upper() == "WIND"]
    actual_by_time, actual_duplicates = _records_for_interval(actual_candidates)
    forecasts_by_time: dict[str, list[dict[str, Any]]] = defaultdict(list)
    malformed_forecasts = 0
    for row in forecast_rows:
        delivery = parse_timestamp(row.get("startTime"))
        publication = parse_timestamp(row.get("publishTime"))
        if delivery is None or publication is None:
            malformed_forecasts += 1
            continue
        forecasts_by_time[delivery.isoformat()].append(row)

    rows: list[dict[str, Any]] = []
    forecast_duplicates = 0
    actual_only = forecast_only = invalid_actual = invalid_forecast = 0
    invalid_error_pairs = 0
    for interval in expected:
        instant = interval["startTime"]
        assert isinstance(instant, datetime)
        key = instant.isoformat()
        candidates = forecasts_by_time.get(key, [])
        forecast_duplicates += max(0, len(candidates) - len({parse_timestamp(r.get("publishTime")) for r in candidates}))
        cutoff = interval["cutoff"]
        assert isinstance(cutoff, datetime)
        eligible = [r for r in candidates if (parse_timestamp(r.get("publishTime")) or datetime.max.replace(tzinfo=UTC)) <= cutoff]
        eligible.sort(key=lambda r: (parse_timestamp(r.get("publishTime")) or datetime.min.replace(tzinfo=UTC), repr(sorted(r.items()))))
        selected = eligible[-1] if eligible else None
        actual = actual_by_time.get(key)
        forecast_value = _number(selected.get("generation")) if selected else None
        actual_value = _number(actual.get("generation")) if actual else None
        if actual and actual_value is None:
            invalid_actual += 1
        if selected and forecast_value is None:
            invalid_forecast += 1
        difference = forecast_value - actual_value if forecast_value is not None and actual_value is not None else None
        error = difference if difference is not None and isfinite(difference) else None
        if forecast_value is not None and actual_value is not None and error is None:
            invalid_error_pairs += 1
        if actual_value is not None and forecast_value is None:
            actual_only += 1
        if forecast_value is not None and actual_value is None:
            forecast_only += 1
        published = parse_timestamp(selected.get("publishTime")) if selected else None
        rows.append({
            "decision_date": interval["decisionDate"],
            "delivery_date": interval["deliveryDate"],
            "delivery_time": instant.isoformat().replace("+00:00", "Z"),
            "settlement_period": interval["settlementPeriod"],
            "cutoff_utc": cutoff.isoformat().replace("+00:00", "Z"),
            "forecast_publish_time": published.isoformat().replace("+00:00", "Z") if published else None,
            "forecast_mw": forecast_value,
            "actual_mw": actual_value,
            "error_mw": error,
        })
    matched = [r for r in rows if r["forecast_mw"] is not None and r["actual_mw"] is not None and r["error_mw"] is not None]
    errors = [float(r["error_mw"]) for r in matched]
    actual_values = [abs(float(r["actual_mw"])) for r in matched]
    eligible_count = len(expected)
    error_scale = max((abs(error) for error in errors), default=0.0)
    actual_scale = max(actual_values, default=0.0)
    safe_mae = error_scale * (sum(abs(error) / error_scale for error in errors) / len(errors)) if errors and error_scale else (0.0 if errors else None)
    safe_rmse = error_scale * sqrt(sum((error / error_scale) ** 2 for error in errors) / len(errors)) if errors and error_scale else (0.0 if errors else None)
    safe_bias = error_scale * (sum(error / error_scale for error in errors) / len(errors)) if errors and error_scale else (0.0 if errors else None)
    safe_wape = (
        (error_scale / actual_scale)
        * (sum(abs(error) / error_scale for error in errors) / sum(value / actual_scale for value in actual_values))
        * 100
        if errors and error_scale and actual_scale
        else (0.0 if errors and actual_scale else None)
    )
    safe_wape = safe_wape if safe_wape is None or isfinite(safe_wape) else None
    metrics: dict[str, float | None] = {
        "mae_mw": safe_mae if safe_mae is None or isfinite(safe_mae) else None,
        "rmse_mw": safe_rmse if safe_rmse is None or isfinite(safe_rmse) else None,
        "bias_mw": safe_bias if safe_bias is None or isfinite(safe_bias) else None,
        "wape_percent": safe_wape,
    }
    return {
        "scope": {
            "decision_dates_from": DECISION_DATES_START.isoformat(),
            "decision_dates_to": DECISION_DATES_END.isoformat(),
            "delivery_dates_from": "2026-01-02",
            "delivery_dates_to": "2026-02-01",
            "timezone": "Europe/London",
            "cutoff_local": "12:00 on the decision date",
            "cutoff_assumption": "The assignment specifies day-ahead decisions but no clock time. Noon Europe/London on the preceding day is a configurable analytical assumption, not an official procurement cutoff.",
            "units": "Generation is reported in MW. FUELHH actuals are half-hour average MW; the inspected WINDFOR publication has hourly startTime observations.",
            "coverage_definition": "Valid exact-startTime forecast/actual pairs divided by all 1,488 expected half-hour delivery intervals on delivery days following January 2026 decision dates. Elexon documents hourly WINDFOR and half-hourly FUELHH, but does not prescribe a metric resampling rule; this dashboard therefore uses only identical startTime values. In the inspected responses, forecasts start on the hour, so each matched forecast pairs with the FUELHH half-hour beginning at that hour and the :30 half-hour is unmatched. No interpolation, carry-forward or adjacent-half-hour aggregation is applied; metrics describe only exact-time pairs, not hourly-averaged outturn.",
        },
        "coverage": {
            "eligible_intervals": eligible_count,
            "matched_intervals": len(matched),
            "percent": len(matched) / eligible_count * 100 if eligible_count else None,
            "actual_only": actual_only,
            "forecast_only": forecast_only,
            "missing_both": sum(1 for r in rows if r["actual_mw"] is None and r["forecast_mw"] is None),
            "invalid_actual_values": invalid_actual,
            "invalid_forecast_values": invalid_forecast,
            "invalid_error_pairs": invalid_error_pairs,
            "malformed_forecast_records": malformed_forecasts,
            "duplicate_actual_records": actual_duplicates,
            "duplicate_forecast_publications": forecast_duplicates,
        },
        "metrics": metrics,
        "records": rows,
    }
