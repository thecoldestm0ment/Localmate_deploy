import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

FAQ_DIR = Path("data/faq")
DB_DIR = Path("chroma_db")
EMBEDDING_MODEL = "models/gemini-embedding-001"
FAQ_METADATA = {
    "admin_alien_card_loss.md": {
        "category": "행정",
        "sub_category": "외국인등록증 분실",
    },
    "admin_address_change.md": {
        "category": "행정",
        "sub_category": "주소 변경",
    },
    "admin_visa_extension.md": {
        "category": "행정",
        "sub_category": "체류기간 연장/비자",
    },
}


def ensure_google_api_key() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(".env 파일에 GOOGLE_API_KEY를 설정해주세요.")


def load_markdown_documents() -> list[Document]:
    documents: list[Document] = []

    if not FAQ_DIR.exists():
        raise RuntimeError(f"FAQ 폴더를 찾을 수 없습니다: {FAQ_DIR}")

    for path in sorted(FAQ_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        metadata = FAQ_METADATA.get(
            path.name,
            {"category": "행정", "sub_category": "기타 행정"},
        )
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": path.name,
                    "category": metadata["category"],
                    "sub_category": metadata["sub_category"],
                },
            )
        )

    if not documents:
        raise RuntimeError("벡터 DB를 만들 문서가 없습니다. data/faq/*.md 파일을 확인해주세요.")

    return documents


def rebuild_vector_db(documents: list[Document]) -> int:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
    )
    chunks = splitter.split_documents(documents)

    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(DB_DIR),
    )
    return len(chunks)


def main() -> None:
    load_dotenv()
    ensure_google_api_key()

    documents = load_markdown_documents()
    chunk_count = rebuild_vector_db(documents)

    print(f"문서 수: {len(documents)}")
    print(f"청크 수: {chunk_count}")
    print(f"저장 위치: {DB_DIR}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)
    except Exception:
        print("벡터 DB 생성 중 오류가 발생했습니다. 설정과 네트워크 상태를 확인해주세요.")
        raise SystemExit(1)
