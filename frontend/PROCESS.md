# Frontend process

## Design

React/Vite single-page dashboard consumes GET /api/overview from the shared backend contract. Recharts renders generation profile and signed interval error. KPI values, records and coverage are always backend results; no fabricated fallback data is included. VITE_API_BASE_URL configures the API origin and falls back to http://localhost:8000 for local Vite runs.

## Interface

The page presents the decision and delivery windows, MAE, RMSE, signed bias, WAPE, coverage, forecast-versus-actual chart, error chart, detail table, cutoff explanation, and unmatched interval counts. It includes loading, empty and retryable error states and responsive styling.

## Files and verification

- src/ui/Dashboard.jsx: data loading, metrics and dashboard sections.
- src/style.css: responsive visual styles.
- src/main.jsx, index.html, vite.config.js: app entry and Vite.
- Dockerfile, nginx.conf, .dockerignore: production static image.

Verification: npm install completed with 0 reported vulnerabilities. npm run build succeeded; Vite emitted a non-blocking advisory that the combined minified JS chunk is over 500 kB (561.34 kB).

Local startup verification: Docker Compose frontend returned production Nginx HTML and hashed assets with HTTP 200 on port 5173; the previous Vite dev process was stopped to avoid port conflict. The refreshed browser rendered the live backend metrics and the exact-time cadence note. Backend API at localhost:8000 returned health and overview HTTP 200 with CORS configured for the dashboard origin.

## Remaining

- Run npm installation/build and fix issues.
- Check visual behavior against live backend once data is available.
- Set the production API URL and backend CORS origin during deployment.
