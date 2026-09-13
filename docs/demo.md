# Short demonstration

Run `python -m uvicorn app.main:app --reload --port 3000`, open `http://localhost:3000`, and demonstrate the following in one browser session.

1. **RAG:** Ask, “Which neighbourhoods are suitable for cultural experiences?” Show the knowledge-base section and the Wikivoyage source link.
2. **Weather MCP:** Ask, “What is the forecast for the next three days?” Show the `MCP: weather via Open-Meteo` status and the current-information section.
3. **Currency MCP:** Ask, “Convert INR 50,000 to SGD.” Show the `MCP: currency via Frankfurter` status, returned conversion and rate date.
4. **Combined RAG + MCP:** Ask, “Plan a three-day Singapore itinerary for next week and adjust it according to the weather forecast.” Show the source links, live weather result and the day-wise recommendation with indoor alternatives.
5. **Conversation context:** First state, “I am travelling with two children and prefer cultural activities.” Then ask, “Now plan three days for next week.” Show that the recommendation retains the family and cultural preferences.

If a live provider is unavailable, show the tool-failure message. The application deliberately does not fabricate current weather or conversion values.
