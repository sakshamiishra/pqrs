# Backend process

## Design

FastAPI exposes health, overview, series and records endpoints. app/elexon.py fetches the specified FUELHH and WINDFOR stream routes with bounded date parameters, an HTTP timeout and a 15-minute process-local cache. FUELHH uses settlementDateFrom/To and fuelType=WIND; WINDFOR uses publishDateTimeFrom/To to retrieve superseded historical forecasts, starting 31 December for the first January decision. app/analysis.py normalizes timestamps to UTC, selects the latest eligible forecast, matches intervals and calculates metrics. No database or persistent cache is used.

## Assumption and data handling

Decision dates are 1–31 January 2026; delivery runs 2 January–1 February. Since no clock cutoff is supplied, 12:00 Europe/London on each preceding day is explicitly an analytical assumption, not an official decision time. Each local delivery day is enumerated in half-hour UTC steps. Missing/invalid values remain null; duplicates use a deterministic timestamp/value ordering and are counted. Coverage denominator is all 31×48 expected half-hour intervals.

Elexon's official Wind Generation page describes WINDFOR as hourly while the dataset documentation identifies FUELHH as half-hourly. The inspected live January data has WINDFOR startTime values on the hour, so exact UTC startTime matching pairs each forecast with the FUELHH half-hour beginning at that hour; the :30 half-hour remains unmatched. Elexon does not document a resampling rule for accuracy metrics. No interpolation, carry-forward, or aggregation of adjacent actual half-hours is applied. The resulting 744/1,488 (50%) coverage and matched-point metric scope are disclosed in the API/UI and README.

## Files and verification

- app/analysis.py: selection, matching, counts and metrics.
- app/elexon.py: HTTP client and in-memory cache. FUELHH uses settlementDateFrom/To with fuelType=WIND; WINDFOR uses publication-time bounds from 31 Dec 2025 through the final decision cutoff.
- app/main.py and app/schemas.py: routes, CORS and response schema.
- tests/test_analysis.py: focused mocked-data tests.
- requirements.txt, Dockerfile, .dockerignore: environment and container setup.

Verification: backend pytest passed (9 tests), including cutoff selection, after-cutoff exclusion, wind-only matching, duplicate handling, missing/invalid values, metrics, zero denominator, empty input, JSON safety, health/overview contracts, and upstream error mapping. The FastAPI TestClient emitted a Starlette deprecation warning for httpx. Docker Compose config, image builds, and service startup succeeded. The live backend health and overview endpoints returned HTTP 200; overview contained 1,488 actuals, 744 forecasts, 744 exact-time pairs and 50% coverage. Host port 8000 initially also had the prior native Uvicorn process and port 5173 the prior Vite process; both duplicates were stopped so those URLs now route to Compose.

## Remaining

- Resolve the accuracy methodology if an authoritative metric alignment rule becomes available; exact-time metrics currently represent only the :00-start half-hour sample.
- Verify provider CORS and deployment settings.
