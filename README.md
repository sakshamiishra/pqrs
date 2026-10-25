# Wind Forecast Intelligence

A small decision-support dashboard for reviewing UK wind generation forecasts available at a proposed day-ahead procurement decision time. It compares selected Elexon forecasts with actual wind outturn; it does not calculate a procurement volume or recommendation.

## Data and method

The backend reads only Elexon's public WINDFOR and FUELHH dataset stream endpoints. FUELHH is filtered to fuelType == WIND. Forecasts are joined to actual values by normalized UTC startTime. For every delivery interval, the latest forecast with publishTime at or before the cutoff is selected; later publications are excluded.

The analysis covers decision dates 1–31 January 2026. The assignment says decisions are day-ahead but does not give a clock time. This app currently uses a fixed code-level assumption of 12:00 Europe/London on the day before delivery; it is not an official procurement or Elexon cutoff. Thus delivery days run from 2 January through 1 February 2026. UK local days are converted using Europe/London; delivery intervals are generated as 30-minute UTC steps within each local day, accounting for daylight-saving days.

Generation and forecast-error values are in MW. FUELHH actuals are average MW over half-hour intervals. Elexon's Wind Generation page describes WINDFOR as hourly; the inspected historical API response also had hourly forecast `startTime` values at `:00`. Elexon documents the source cadences and shows forecast versus outturn, but does not prescribe how to resample FUELHH for forecast-accuracy metrics. The app therefore retains an exact normalized UTC `startTime` join. Each matched forecast pairs with the FUELHH half-hour beginning at the hour; the `:30` half-hour remains unmatched. It does not interpolate, carry forecasts forward, or aggregate adjacent half-hour actuals into hourly values. Consequently, the observed January data produced 744 exact-time pairs from 1,488 expected half-hour intervals (50% coverage); these metrics describe only the matched half-hours beginning on the hour, not hourly-averaged outturn. Aggregating two half-hour average-MW actuals into an hourly actual is a possible alternative alignment, but it changes the comparison window, denominator, and resulting metrics; it is not applied without an authoritative metric definition. Forecast error is forecast minus actual: positive bias means over-forecasting. MAE is mean absolute error, and RMSE is the square root of mean squared error; both use valid exact-startTime matched pairs. WAPE is the sum of absolute errors divided by the sum of absolute actual generation, times 100, and is reported as a percentage; it is unavailable if the denominator is zero. Coverage is valid matched pairs divided by all 1,488 expected half-hour delivery intervals in the defined delivery window. Missing and invalid values are not converted to zero.

## Features

- KPI cards for MAE, RMSE, forecast bias, WAPE and coverage.
- Time series of selected forecast and actual wind generation plus interval error.
- Interval records with forecast publication time and error.
- Explicit cutoff, date window and unmatched-data counts.
- Loading, error and empty states with retry.

## Structure

The backend folder contains FastAPI, Elexon access, analysis, tests and a Dockerfile. The frontend folder contains React/Vite, UI, and a Dockerfile. Root files include Compose, README and overall PROCESS log; backend and frontend also have separate process logs.

## Local setup

Python 3.12 and Node.js 22 are recommended. From the project root:

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

In another terminal:

    cd frontend
    npm install
    npm run dev

Open http://localhost:5173. Set VITE_API_BASE_URL in frontend/.env.local if the API is not at http://localhost:8000. The backend supports CORS_ORIGINS as a comma-separated list. The local .venv is only for Mac development; requirements are separately installed into the Docker image.

## Docker

From the project root:

    docker compose up --build
    docker compose logs -f
    docker compose down

Open http://localhost:5173. API health is at http://localhost:8000/api/health.

## API

- GET /api/health — process health.
- GET /api/overview — scope, assumptions, coverage, metrics and interval records.
- GET /api/series — scope and chronological series records.
- GET /api/records — scope, coverage and detail records.

## Limitations and deployment

Historical completeness and actual data availability must be read from the live Elexon response; the dashboard has no embedded sample data. Elexon records cover wind farms visible to the system operator with operational metering; this may not represent every wind generator. A 15-minute in-memory cache is per backend process and is not shared between hosting instances.

The Elexon OpenAPI documents FUELHH as half-hourly generation outturn and WINDFOR as wind generation forecast; WINDFOR history is filtered by publication time and returns publication time, delivery startTime and generation. The official [Wind Generation page](https://bmrs.elexon.co.uk/wind-generation) specifies an hourly forecast horizon, says its chart compares forecast against actual Generation by Fuel Type outturn, and notes forecasts can be updated up to eight times daily. It does not state a resampling rule for accuracy metrics. See the [FUELHH stream schema](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream), [WINDFOR stream schema](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream), and [Elexon developer portal](https://developer.data.elexon.co.uk/).

The application is deployed as a static React/Vite frontend on Vercel and a FastAPI backend on Render:

- **Official dashboard:** [https://gbassignment.vercel.app/](https://gbassignment.vercel.app/)
- **Backend health endpoint:** [https://gbassignment-api.onrender.com/api/health](https://gbassignment-api.onrender.com/api/health)

`VITE_API_BASE_URL` sets the backend API origin used by the frontend when it is built; for this deployment, it should point to `https://gbassignment-api.onrender.com` (without an endpoint path). `CORS_ORIGINS` configures the frontend origins allowed by the backend and should include the deployed Vercel origin. The local Docker Compose configuration uses localhost values for local access; production uses the hosted URLs above. The health link identifies the backend health route; it does not imply that every API endpoint or the complete dashboard has been independently verified.

Render's free web services can spin down after 15 minutes without incoming traffic and restart when another request arrives, so the first request after inactivity may take longer. See [Render's free web service documentation](https://render.com/docs/free).

## AI tools

OpenAI Codex assisted during development with backend analysis and API implementation, test work, Docker integration, project documentation, and frontend implementation. The project was developed iteratively with AI assistance; this disclosure does not mean the application was generated automatically end-to-end. The available project notes do not establish use of other AI tools, so none are listed here. No external credentials or API keys are required by the selected Elexon endpoints.
