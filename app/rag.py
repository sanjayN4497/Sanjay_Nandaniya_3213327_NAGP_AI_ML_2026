from __future__ import annotations

import re
import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
VECTOR_DIR = ROOT / "data" / "chroma"


def parse_document(path: Path) -> Document:
    content = path.read_text(encoding="utf-8")
    matched = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, flags=re.DOTALL)
    if not matched:
        raise ValueError(f"Knowledge document is missing front matter: {path.name}")
    metadata = dict(re.findall(r'^([\w_]+):\s*"?(.*?)"?$', matched.group(1), flags=re.MULTILINE))
    return Document(page_content=matched.group(2), metadata={**metadata, "filename": path.name})


class SingaporeKnowledgeBase:
    def __init__(self) -> None:
        self.store: Chroma | None = None

    def initialize(self) -> None:
        if self.store:
            return
        documents = [parse_document(path) for path in sorted(KNOWLEDGE_DIR.glob("*.md"))]
        if len(documents) < 3:
            raise RuntimeError("At least three knowledge-base documents are required.")
        chunks = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120).split_documents(documents)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is required to create Gemini embeddings.")
        embeddings = GoogleGenerativeAIEmbeddings(
            model=os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"),
            google_api_key=api_key,
        )
        self.store = Chroma.from_documents(chunks, embeddings, persist_directory=str(VECTOR_DIR), collection_name="singapore_travel")

    def retrieve(self, question: str) -> list[tuple[Document, float]]:
        self.initialize()
        assert self.store
        return self.store.similarity_search_with_relevance_scores(question, k=5)
