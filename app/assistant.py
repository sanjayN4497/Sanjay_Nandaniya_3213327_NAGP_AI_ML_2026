from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI

from app.mcp_servers import currency_request, get_currency, get_weather, weather_request
from app.prompts import TRAVEL_ANSWER_PROMPT
from app.rag import SingaporeKnowledgeBase


@dataclass
class Turn:
    role: Literal["user", "assistant"]
    content: str


def format_history(history: list[Turn]) -> str:
    return "\n".join(f"{turn.role}: {turn.content}" for turn in history[-8:]) or "No earlier conversation."


def format_knowledge(results: list[tuple]) -> str:
    return "\n\n".join(f"[{index}] {document.metadata['title']}\n{document.page_content}" for index, (document, _) in enumerate(results, 1))


def format_current_info(results: list[dict]) -> str:
    if not results:
        return "No MCP tool was needed for this request."
    return "\n\n".join(
        f"{item['kind'].upper()} from {item['provider']}: {item['data']}" if item["ok"] else f"{item['kind'].upper()} MCP TOOL FAILED: {item['error']}"
        for item in results
    )


def response_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        values: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                values.append(item["text"])
            elif isinstance(getattr(item, "text", None), str):
                values.append(item.text)
        if values:
            return "\n".join(values)
    return str(content)


class TravelAssistant:
    def __init__(self) -> None:
        self.knowledge_base = SingaporeKnowledgeBase()
        self.model = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            temperature=0.2,
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        )

    async def answer(self, question: str, history: list[Turn]) -> dict:
        if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
            raise RuntimeError("GOOGLE_API_KEY is required to generate Gemini embeddings and answers. Add it to .env and restart the application.")
        weather = weather_request(question)
        currency = currency_request(question)
        retrieved, weather_result, currency_result = await asyncio.gather(
            asyncio.to_thread(self.knowledge_base.retrieve, question),
            get_weather(*weather) if weather else self._empty_result(),
            get_currency(*currency) if currency else self._empty_result(),
        )
        current_info = [item for item in (weather_result, currency_result) if item]
        chain = TRAVEL_ANSWER_PROMPT | self.model
        response = await chain.ainvoke(
            {
                "question": question,
                "history": format_history(history),
                "knowledge": format_knowledge(retrieved),
                "mcp_results": format_current_info(current_info),
            }
        )
        sources = list({document.metadata["url"]: {"title": document.metadata["title"], "url": document.metadata["url"]} for document, _ in retrieved}.values())
        return {"answer": response_text(response.content), "sources": sources, "currentInfo": current_info}

    @staticmethod
    async def _empty_result() -> None:
        return None
