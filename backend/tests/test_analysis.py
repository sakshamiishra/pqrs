from app.analysis import analyze, expected_intervals
import json

def ts(i=0):
    return expected_intervals()[i]["startTime"].isoformat().replace("+00:00", "Z")

def test_latest_forecast_before_cutoff_wins():
    start = ts()
    result = analyze([{"startTime": start, "fuelType": "WIND", "generation": 100}], [
        {"startTime": start, "publishTime": "2026-01-01T11:00:00Z", "generation": 80},
        {"startTime": start, "publishTime": "2026-01-01T11:59:00Z", "generation": 90},
        {"startTime": start, "publishTime": "2026-01-01T12:01:00Z", "generation": 99},
    ])
    assert result["records"][0]["forecast_mw"] == 90
    assert result["records"][0]["error_mw"] == -10

def test_wind_filter_matching_and_metrics():
    a, b = ts(0), ts(1)
    result = analyze(
        [{"startTime": a, "fuelType": "GAS", "generation": 900},
         {"startTime": a, "fuelType": "WIND", "generation": 100},
         {"startTime": b, "fuelType": "WIND", "generation": 100}],
        [{"startTime": a, "publishTime": "2026-01-01T11:00:00Z", "generation": 110},
         {"startTime": b, "publishTime": "2026-01-01T11:00:00Z", "generation": 110}],
    )
    assert result["metrics"] == {"mae_mw": 10.0, "rmse_mw": 10.0, "bias_mw": 10.0, "wape_percent": 10.0}
    assert result["coverage"]["matched_intervals"] == 2
    json.dumps(result, allow_nan=False)

def test_duplicates_missing_invalid_empty_and_zero_wape():
    start = ts()
    actual = [{"startTime": start, "fuelType": "WIND", "generation": 0},
              {"startTime": start, "fuelType": "WIND", "generation": 1}]
    result = analyze(actual, [{"startTime": start, "publishTime": "2026-01-01T11:00:00Z", "generation": 0}])
    assert result["coverage"]["duplicate_actual_records"] == 1
    assert result["metrics"]["wape_percent"] is None
    missing = analyze([{"startTime": start, "fuelType": "WIND", "generation": None}],
                      [{"startTime": start, "publishTime": "2026-01-01T11:00:00Z", "generation": "bad"}])
    assert missing["metrics"]["mae_mw"] is None
    assert missing["coverage"]["matched_intervals"] == 0
    assert analyze([], [])["metrics"]["rmse_mw"] is None
    json.dumps(missing, allow_nan=False)

def test_january_decisions_cover_following_delivery_days():
    values = expected_intervals()
    assert values[0]["deliveryDate"] == "2026-01-02"
    assert values[-1]["deliveryDate"] == "2026-02-01"
    assert len(values) == 31 * 48
    result = analyze([], [])
    assert "hourly" in result["scope"]["units"]
    assert "exact-startTime" in result["scope"]["coverage_definition"]

def test_extreme_finite_inputs_never_emit_infinity():
    start = ts()
    result = analyze(
        [{"startTime": start, "fuelType": "WIND", "generation": -1e308}],
        [{"startTime": start, "publishTime": "2026-01-01T11:00:00Z", "generation": 1e308}],
    )
    assert result["records"][0]["error_mw"] is None
    assert result["metrics"]["mae_mw"] is None
    json.dumps(result, allow_nan=False)
