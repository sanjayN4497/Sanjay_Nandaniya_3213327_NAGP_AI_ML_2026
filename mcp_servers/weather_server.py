from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("singapore-weather-mcp")
SINGAPORE = {"latitude": 1.3521, "longitude": 103.8198, "timezone": "Asia/Singapore"}
WEATHER_LABELS = {0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "rime fog", 51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle", 61: "slight rain", 63: "moderate rain", 65: "heavy rain", 80: "rain showers", 81: "moderate rain showers", 82: "violent rain showers", 95: "thunderstorm"}


def singapore_today() -> date:
    return (datetime.now(timezone.utc) + timedelta(hours=8)).date()


@mcp.tool()
async def get_singapore_weather(start_date: str | None = None, days: int = 3) -> dict:
    """Get Singapore daily weather forecast from Open-Meteo for dates within the next 16 days."""
    try:
        start = date.fromisoformat(start_date) if start_date else singapore_today()
        if not 1 <= days <= 7:
            raise ValueError("Days must be between 1 and 7.")
        forecast_days = (start - singapore_today()).days + days
        if not 1 <= forecast_days <= 16:
            raise ValueError("Open-Meteo provides a maximum 16-day forecast. Choose dates within that window.")
        params = {**SINGAPORE, "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max", "forecast_days": forecast_days}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            payload = response.json()
        daily = payload.get("daily", {})
        dates = daily.get("time", [])
        first = dates.index(start.isoformat())
        result = []
        for index in range(first, first + days):
            result.append({"date": dates[index], "conditions": WEATHER_LABELS.get(daily["weather_code"][index], f"weather code {daily['weather_code'][index]}"), "temperature_c": {"min": daily["temperature_2m_min"][index], "max": daily["temperature_2m_max"][index]}, "precipitation_probability_max": daily["precipitation_probability_max"][index]})
        return {"destination": "Singapore", "provider": "Open-Meteo", "retrieved_at": datetime.now(timezone.utc).isoformat(), "daily": result}
    except Exception as error:
        return {"error": str(error)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
