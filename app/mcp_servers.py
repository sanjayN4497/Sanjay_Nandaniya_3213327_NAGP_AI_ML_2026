from __future__ import annotations

import asyncio
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parent.parent


async def call_mcp_server(script_name: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call one local stdio MCP tool and return its JSON result."""
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "mcp_servers" / script_name)],
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            text = next((item.text for item in result.content if hasattr(item, "text")), None)
            if not text:
                raise RuntimeError("MCP tool returned no text content.")
            data = json.loads(text)
            if result.isError or data.get("error"):
                raise RuntimeError(str(data.get("error", "MCP tool failed.")))
            return data


async def get_weather(start_date: str, days: int = 3) -> dict[str, Any]:
    try:
        data = await call_mcp_server("weather_server.py", "get_singapore_weather", {"start_date": start_date, "days": days})
        return {"kind": "weather", "ok": True, "provider": data.get("provider"), "data": data}
    except Exception as error:
        return {"kind": "weather", "ok": False, "error": str(error)}


async def get_currency(amount: float, source: str, target: str) -> dict[str, Any]:
    try:
        data = await call_mcp_server("currency_server.py", "convert_currency", {"amount": amount, "source": source, "target": target})
        return {"kind": "currency", "ok": True, "provider": data.get("provider"), "data": data}
    except Exception as error:
        return {"kind": "currency", "ok": False, "error": str(error)}


def singapore_today() -> date:
    # Singapore is UTC+8 year-round.
    return (datetime.now(timezone.utc) + timedelta(hours=8)).date()


def next_monday() -> date:
    today = singapore_today()
    return today + timedelta(days=((7 - today.weekday()) % 7 or 7))


def weather_request(question: str) -> tuple[str, int] | None:
    lowered = question.lower()
    if not any(word in lowered for word in ("weather", "forecast", "rain", "rainy", "outdoor", "indoor", "tomorrow", "next week")):
        return None
    explicit_date = __import__("re").search(r"\b(20\d{2}-\d{2}-\d{2})\b", question)
    start = explicit_date.group(1) if explicit_date else str(
        next_monday() if "next week" in lowered else singapore_today() + timedelta(days=1) if "tomorrow" in lowered else singapore_today()
    )
    return start, 3 if any(text in lowered for text in ("three-day", "three day", "3-day", "3 day", "next week")) else 1


def currency_request(question: str) -> tuple[float, str, str] | None:
    import re

    upper = question.upper()
    codes = r"(INR|USD|SGD|EUR|GBP)"
    leading = re.search(rf"\b{codes}\s*([\d,]+(?:\.\d+)?)\s*(?:TO|INTO|IN)\s*{codes}\b", upper)
    if leading:
        return float(leading.group(2).replace(",", "")), leading.group(1), leading.group(3)
    trailing = re.search(rf"\b([\d,]+(?:\.\d+)?)\s*{codes}\s*(?:TO|INTO|IN)\s*{codes}\b", upper)
    if trailing:
        return float(trailing.group(1).replace(",", "")), trailing.group(2), trailing.group(3)
    return None
