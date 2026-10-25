"""FastAPI routes for Wind Forecast Intelligence."""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analysis import analyze
from .elexon import ElexonError, fetch_analysis_data
from .schemas import AnalysisResponse, HealthResponse

app = FastAPI(title="Wind Forecast Intelligence API", version="1.0.0")
allowed_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=False, allow_methods=["GET"], allow_headers=["*"])


async def get_analysis() -> dict:
    try:
        actuals, forecasts = await fetch_analysis_data()
    except ElexonError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return analyze(actuals, forecasts)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/overview", response_model=AnalysisResponse)
async def overview() -> dict:
    return await get_analysis()


@app.get("/api/series")
async def series() -> dict:
    result = await get_analysis()
    return {"scope": result["scope"], "series": result["records"]}


@app.get("/api/records")
async def records() -> dict:
    result = await get_analysis()
    return {"scope": result["scope"], "coverage": result["coverage"], "records": result["records"]}
