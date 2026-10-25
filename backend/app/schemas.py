"""Typed response models for the dashboard API."""

from typing import Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class AnalysisResponse(BaseModel):
    scope: dict[str, Any]
    coverage: dict[str, Any]
    metrics: dict[str, float | None]
    records: list[dict[str, Any]]
