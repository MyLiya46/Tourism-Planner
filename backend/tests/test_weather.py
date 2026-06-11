from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient


CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.api.routes.weather as weather_route  # noqa: E402
import app.services.weather_service as weather_service  # noqa: E402


app = FastAPI()
app.include_router(weather_route.router)
client = TestClient(app)


def test_get_weather_forecast_returns_cached_value(monkeypatch) -> None:
    cached_payload = {
        "city": "Beijing",
        "province": "Beijing",
        "adcode": "110000",
        "report_time": "2026-06-11 09:00:00",
        "days": [{"date": "2026-06-11", "week": "4"}],
    }

    monkeypatch.setattr(weather_service, "get_cached_json", lambda key: cached_payload)
    monkeypatch.setattr(
        weather_service,
        "geocode_address",
        lambda address, city=None: (_ for _ in ()).throw(AssertionError("should not geocode on cache hit")),
    )

    result = weather_service.get_weather_forecast("Beijing")

    assert result == cached_payload


def test_get_weather_forecast_fetches_and_formats_result(monkeypatch) -> None:
    saved_cache = {}

    monkeypatch.setattr(weather_service, "get_cached_json", lambda key: None)
    monkeypatch.setattr(
        weather_service,
        "geocode_address",
        lambda address, city=None: {"adcode": "310000", "formatted_address": "Shanghai"},
    )
    monkeypatch.setattr(
        weather_service,
        "_request_amap_weather",
        lambda path, params: {
            "status": "1",
            "forecasts": [
                {
                    "city": "Shanghai",
                    "province": "Shanghai",
                    "adcode": "310000",
                    "reporttime": "2026-06-11 08:00:00",
                    "casts": [
                        {
                            "date": "2026-06-11",
                            "week": "4",
                            "dayweather": "Sunny",
                            "nightweather": "Cloudy",
                            "daytemp": "30",
                            "nighttemp": "23",
                            "daywind": "East",
                            "nightwind": "Southeast",
                        }
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(
        weather_service,
        "set_cached_json",
        lambda key, value, expire_seconds=None: saved_cache.update(
            {"key": key, "value": value, "expire_seconds": expire_seconds}
        ),
    )

    result = weather_service.get_weather_forecast("Shanghai")

    assert result["city"] == "Shanghai"
    assert result["province"] == "Shanghai"
    assert result["adcode"] == "310000"
    assert result["report_time"] == "2026-06-11 08:00:00"
    assert len(result["days"]) == 1
    assert result["days"][0] == {
        "date": "2026-06-11",
        "week": "4",
        "day_weather": "Sunny",
        "night_weather": "Cloudy",
        "day_temp": "30",
        "night_temp": "23",
        "day_wind": "East",
        "night_wind": "Southeast",
    }
    assert saved_cache["key"] == "weather:forecast:shanghai"
    assert saved_cache["value"] == result


def test_get_weather_forecast_falls_back_to_raw_city_when_geocode_fails(monkeypatch) -> None:
    requested_params = {}

    monkeypatch.setattr(weather_service, "get_cached_json", lambda key: None)
    monkeypatch.setattr(
        weather_service,
        "geocode_address",
        lambda address, city=None: (_ for _ in ()).throw(RuntimeError("mock geocode failed")),
    )

    def fake_request(path: str, params: dict) -> dict:
        requested_params.update(params)
        return {
            "status": "1",
            "forecasts": [
                {
                    "city": "北京市",
                    "province": "北京",
                    "adcode": "110000",
                    "reporttime": "2026-06-11 15:03:25",
                    "casts": [],
                }
            ],
        }

    monkeypatch.setattr(weather_service, "_request_amap_weather", fake_request)
    monkeypatch.setattr(weather_service, "set_cached_json", lambda key, value, expire_seconds=None: None)

    result = weather_service.get_weather_forecast("北京")

    assert requested_params["city"] == "北京"
    assert requested_params["extensions"] == "all"
    assert result["city"] == "北京市"


def test_weather_forecast_api_returns_success_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        weather_route,
        "get_weather_forecast",
        lambda city: {
            "city": city,
            "province": "Guangdong",
            "adcode": "440100",
            "report_time": "2026-06-11 10:00:00",
            "days": [
                {
                    "date": "2026-06-11",
                    "week": "4",
                    "day_weather": "Cloudy",
                    "night_weather": "Rain",
                    "day_temp": "29",
                    "night_temp": "25",
                    "day_wind": "South",
                    "night_wind": "South",
                }
            ],
        },
    )

    response = client.get("/weather/forecast", params={"city": "Guangzhou"})

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Guangzhou"
    assert data["province"] == "Guangdong"
    assert data["days"][0]["day_weather"] == "Cloudy"


def test_weather_forecast_api_returns_502_when_service_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        weather_route,
        "get_weather_forecast",
        lambda city: (_ for _ in ()).throw(RuntimeError("mock upstream failed")),
    )

    response = client.get("/weather/forecast", params={"city": "Guangzhou"})

    assert response.status_code == 502
    assert response.json()["detail"] == "mock upstream failed"
