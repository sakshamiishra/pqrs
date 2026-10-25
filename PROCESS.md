# Overall process

## Scope and architecture

Wind Forecast Intelligence compares Elexon WINDFOR forecasts available at a proposed day-ahead decision cutoff with FUELHH actual wind generation. It is a decision-support view, not a procurement optimizer. The implementation uses React/Vite, FastAPI/HTTPX, pytest, Docker and Compose; no database or external dataset is used.

## Business interpretation

The app interprets January 2026 as the month of procurement decisions, not delivery. Decision dates are 1–31 January and covered delivery days are 2 January–1 February. The assignment does not specify a clock cutoff. Noon Europe/London on the preceding day is an explicit, configurable analytical assumption, not an official decision time. Forecast selection uses latest publishTime at or before that cutoff; delivery matching uses UTC startTime. Local delivery days are converted with Europe/London timezone rules.

## Responsibilities and contract

Codex implementation: backend, analysis, tests, Docker integration and shared docs. Frontend: React/Vite dashboard consuming the shared response contract. GET /api/overview returns scope, coverage, metrics and records; /api/series and /api/records provide narrower views. See backend/PROCESS.md and frontend/PROCESS.md.

## Milestones

- [x] Inspected workspace; backend and frontend directories were empty.
- [x] Implemented backend, dashboard, tests, Docker Compose and docs.
- [x] Backend tests pass (9 tests; one Starlette/httpx deprecation warning).
- [x] Vite production build succeeds (non-blocking >500 kB chunk-size advisory).
- [x] Docker Compose configuration validates with docker compose config.
- [x] Built and started both Docker Compose services; backend health and overview returned HTTP 200, production frontend returned HTTP 200, and browser rendering showed backend data.
- [x] Reviewed Elexon cadence documentation and the live January app data flow: WINDFOR starts are hourly at :00; FUELHH actuals are half-hourly at :00 and :30. Elexon does not prescribe an accuracy-metric resampling rule, so exact startTime matching remains in place and its 50% coverage limitation is documented.
- [ ] Confirm procurement cutoff with assignment/client contact.
- [ ] Verify live historical data coverage and deployed service behavior.
- [ ] Deploy and verify public links; prepare video and form submission.

## Deployment

Proposed: static React build on Vercel; FastAPI service on Render. No provider configuration, account access, public repository, deployment, video or form submission has been completed.

## Final checklist

- [ ] Confirm cutoff assumption or update it.
- [x] Verify historical forecasts and actuals through the live backend data flow; retain honest 50% exact-time coverage and document resolution mismatch.
- [x] Run tests/build and record observed results.
- [x] Start Docker Desktop and verify both images/build and Compose startup.
- [ ] Deploy; test frontend-to-backend from a private/incognito browser.
- [ ] Publish random-looking public repository, README link, unlisted video under 10 minutes, and submit supplied form.
