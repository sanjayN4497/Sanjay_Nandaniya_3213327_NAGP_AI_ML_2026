# Sample questions and expected response behaviour

These are response-shape examples. Weather and currency values are live MCP data and will differ at runtime.

## RAG-only

**Question:** Which neighbourhoods are suitable for cultural experiences?

**Response behaviour:** The assistant puts Chinatown, Little India and Geylang Serai in **Knowledge-base facts**, notes the food/cultural associations supported by the retrieved excerpts, then gives a labelled planning suggestion. It lists the matching Wikivoyage source link. No MCP tool is called.

## Currency MCP

**Question:** Convert INR 50,000 to SGD.

**Response behaviour:** The assistant retrieves a small amount of supporting Singapore context, calls `convert_currency` with `amount: 50000`, `from: INR`, `to: SGD`, and reports the returned amount, provider and rate date in **Current information (MCP)**. It does not treat a rate as knowledge-base content.

## Weather-aware combined response

**Question:** Plan a three-day Singapore itinerary for next week and adjust it according to the weather forecast.

**Response behaviour:** The assistant retrieves relevant RAG chunks about Marina Bay, cultural districts, outdoor locations, indoor alternatives and transport. It calls `get_singapore_weather` for the next Monday and three days. It then produces a day-wise recommendation; dates with material rain probability include an indoor fallback. The answer keeps weather values in **Current information (MCP)**, stable destination details in **Knowledge-base facts**, and labels the itinerary as **Recommendation**.

## Conversational context

**Turn 1:** I am travelling with two children and prefer cultural activities.

**Turn 2:** Now plan three days for next week.

**Response behaviour:** The second turn receives the first one in recent session history, uses the weather MCP tool, and preserves the family and cultural preferences when making recommendations.
