from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.assistant import TravelAssistant, Turn


ROOT = Path(__file__).resolve().parent.parent
# The project-local Gemini key and model must override stale shell/session values.
load_dotenv(ROOT / ".env", override=True)
app = FastAPI(title="AI Travel Planning Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.mount("/assets", StaticFiles(directory=ROOT / "public"), name="assets")
assistant = TravelAssistant()
sessions: dict[str, list[Turn]] = {}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    sessionId: str | None = None


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(ROOT / "public" / "index.html")


@app.get("/styles.css")
async def styles() -> FileResponse:
    return FileResponse(ROOT / "public" / "styles.css")


@app.get("/app.js")
async def script() -> FileResponse:
    return FileResponse(ROOT / "public" / "app.js", media_type="text/javascript")


@app.get("/api/health")
async def health() -> dict:
    return {"geminiConfigured": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))}


@app.post("/api/chat")
async def chat(payload: ChatRequest) -> dict:
    session_id = payload.sessionId if payload.sessionId and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", payload.sessionId) else str(uuid4())
    history = sessions.get(session_id, [])
    try:
        result = await assistant.answer(payload.message.strip(), history)
    except Exception as error:
        return JSONResponse(status_code=503, content={"error": str(error)})
    sessions[session_id] = (history + [Turn(role="user", content=payload.message.strip()), Turn(role="assistant", content=result["answer"])])[-16:]
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.getenv("PORT", "3000")), reload=True)
