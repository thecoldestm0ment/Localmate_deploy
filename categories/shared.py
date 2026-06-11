import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DB_DIR = PROJECT_ROOT / "chroma_db"
EMBEDDING_MODEL = "models/gemini-embedding-001"
CHAT_MODEL = "gemini-2.5-flash"
MISSING_API_KEY_MESSAGE = ".env 파일에 GOOGLE_API_KEY를 설정해주세요."
MISSING_DB_MESSAGE = "먼저 python build_vector_db.py를 실행해주세요."


def ensure_google_api_key() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(MISSING_API_KEY_MESSAGE)


@lru_cache(maxsize=1)
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    ensure_google_api_key()
    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    if not DB_DIR.exists():
        raise RuntimeError(MISSING_DB_MESSAGE)
    return Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=get_embeddings(),
    )


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    ensure_google_api_key()
    return ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0.2,
    )


def build_metadata_filter(category: str, sub_category: str | None = None) -> dict:
    if not sub_category:
        return {"category": category}
    return {
        "$and": [
            {"category": category},
            {"sub_category": sub_category},
        ]
    }


def similarity_search_relevant(
    query: str,
    category: str,
    sub_category: str,
    k: int = 3,
) -> list[Document]:
    vectorstore = get_vectorstore()
    exact_docs = vectorstore.similarity_search(
        query,
        k=k,
        filter=build_metadata_filter(category, sub_category),
    )
    if exact_docs:
        return exact_docs

    category_docs = vectorstore.similarity_search(
        query,
        k=k,
        filter=build_metadata_filter(category),
    )
    return [
        doc
        for doc in category_docs
        if doc.metadata.get("sub_category") == sub_category
    ]
