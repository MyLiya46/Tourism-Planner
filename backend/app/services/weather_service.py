from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import (
    AMAP_API_KEY,
    AMAP_BASE_URL,
    AMAP_TIMEOUT_SECONDS,
    REDIS_WEATHER_TTL_SECONDS,
)
from app.services.cache_service import get_cached_json, set_cached_json
from app.services.map_service import geocode_address


logger = logging.getLogger(__name__)


def _ensure_amap_api_key() -> None:
    """Ensure the AMap API key is configured."""
    if not AMAP_API_KEY:
        raise RuntimeError("Current environment is missing AMAP_API_KEY.")


def _build_client() -> httpx.Client:
    """Build a resilient HTTP client for AMap weather requests."""
    return httpx.Client(
        timeout=AMAP_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": "TourismPlanner/1.0"},
    )


def _request_amap_weather(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """Call the AMap weather API and return the JSON payload."""
    _ensure_amap_api_key()

    request_params = {
        "key": AMAP_API_KEY,
        **params,
    }

    payload: dict[str, Any] | None = None
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            with _build_client() as client:
                response = client.get(f"{AMAP_BASE_URL}{path}", params=request_params)
                response.raise_for_status()
                payload = response.json()
            break
        except httpx.RequestError as exc:
            last_error = exc
            logger.warning(
                "AMap weather request failed on attempt %s/%s: %s",
                attempt + 1,
                2,
                exc,
            )

    if payload is None:
        assert last_error is not None
        raise RuntimeError(f"AMap weather request failed: {last_error}") from last_error

    if payload.get("status") != "1":
        info = payload.get("info", "Unknown error")
        raise RuntimeError(f"AMap weather API call failed: {info}")

    return payload


def _normalize_cache_text(value: str | None) -> str:
    """Normalize text used in cache keys."""
    if value is None:
        return ""
    return value.strip().lower()


def get_weather_forecast(city: str) -> dict[str, Any]:
    """Get the weather forecast for the given city."""
    cache_key = f"weather:forecast:{_normalize_cache_text(city)}"
    cached_value = get_cached_json(cache_key)
    if cached_value is not None:
        logger.info("weather cache hit: city=%s", city)
        return cached_value
    logger.info("weather cache miss: city=%s", city)

    try:
        geocode = geocode_address(city, city=city)
    except Exception as exc:
        # Weather lookup can still succeed with the raw city name even if geocoding fails.
        logger.warning("weather geocode failed for city=%s: %s", city, exc)
        geocode = None

    city_code = geocode.get("adcode") if geocode is not None else city

    payload = _request_amap_weather(
        "/weather/weatherInfo",
        {
            "city": city_code or city,
            "extensions": "all",
        },
    )

    forecasts = payload.get("forecasts", [])
    if not forecasts:
        raise RuntimeError("No weather forecast data returned.")

    first = forecasts[0]
    casts = first.get("casts", [])

    days = [
        {
            "date": cast.get("date"),
            "week": cast.get("week"),
            "day_weather": cast.get("dayweather"),
            "night_weather": cast.get("nightweather"),
            "day_temp": cast.get("daytemp"),
            "night_temp": cast.get("nighttemp"),
            "day_wind": cast.get("daywind"),
            "night_wind": cast.get("nightwind"),
        }
        for cast in casts
    ]

    result = {
        "city": first.get("city") or city,
        "province": first.get("province"),
        "adcode": first.get("adcode"),
        "report_time": first.get("reporttime"),
        "days": days,
    }
    set_cached_json(cache_key, result, expire_seconds=REDIS_WEATHER_TTL_SECONDS)
    return result
