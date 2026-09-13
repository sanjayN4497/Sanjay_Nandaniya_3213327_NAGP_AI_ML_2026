from __future__ import annotations

from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("currency-conversion-mcp")


@mcp.tool()
async def convert_currency(amount: float, source: str, target: str) -> dict:
    """Convert a monetary amount using the latest exchange rate from Frankfurter."""
    try:
        source, target = source.upper(), target.upper()
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if source == target:
            return {"amount": amount, "from": source, "to": target, "converted_amount": amount, "rate": 1, "provider": "Frankfurter", "retrieved_at": datetime.now(timezone.utc).isoformat()}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://api.frankfurter.dev/v1/latest", params={"base": source, "symbols": target})
            response.raise_for_status()
            payload = response.json()
        rate = payload.get("rates", {}).get(target)
        if not rate:
            raise ValueError(f"No conversion rate was returned for {source} to {target}.")
        return {"amount": amount, "from": source, "to": target, "converted_amount": round(amount * rate, 2), "rate": rate, "rate_date": payload.get("date"), "provider": "Frankfurter", "retrieved_at": datetime.now(timezone.utc).isoformat()}
    except Exception as error:
        return {"error": str(error)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
