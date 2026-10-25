from fastapi.testclient import TestClient

from app import elexon
from app import main
from app.main import app


def test_health_endpoint():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_elexon_client_accepts_stream_array_and_caches(monkeypatch):
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"startTime": "2026-01-02T00:00:00Z"}]

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params, headers):
            calls.append((url, params, headers))
            return Response()

    monkeypatch.setattr(elexon.httpx, "AsyncClient", Client)
    elexon._cache.clear()

    import asyncio
    params = {"settlementDateFrom": "2026-01-02", "settlementDateTo": "2026-02-01", "fuelType": "WIND"}
    first = asyncio.run(elexon.fetch_dataset("FUELHH", params))
    second = asyncio.run(elexon.fetch_dataset("FUELHH", params))
    assert first == second
    assert len(calls) == 1
    assert calls[0][0].endswith("/FUELHH/stream")


def test_elexon_rejects_unexpected_response(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"unexpected": "shape"}

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(elexon.httpx, "AsyncClient", Client)
    elexon._cache.clear()
    import asyncio
    try:
        asyncio.run(elexon.fetch_dataset("WINDFOR", {"publishDateTimeFrom": "2025-12-31T00:00:00Z"}))
        assert False, "expected ElexonError"
    except elexon.ElexonError:
        pass


def test_overview_contract_and_upstream_error(monkeypatch):
    async def empty_data():
        return [], []

    monkeypatch.setattr(main, "fetch_analysis_data", empty_data)
    response = TestClient(app).get("/api/overview")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"scope", "coverage", "metrics", "records"}
    assert payload["metrics"]["mae_mw"] is None

    async def unavailable():
        raise elexon.ElexonError("upstream unavailable")

    monkeypatch.setattr(main, "fetch_analysis_data", unavailable)
    response = TestClient(app).get("/api/overview")
    assert response.status_code == 502
    assert response.json()["detail"] == "upstream unavailable"
