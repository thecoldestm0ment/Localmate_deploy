import os
import re
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

FAQ_ROOT = Path("data/faq")
DB_DIR = Path("chroma_db")
EMBEDDING_MODEL = "models/gemini-embedding-001"
SOURCE_METADATA_HEADER = "## source metadata"


def ensure_google_api_key() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(".env 파일에 GOOGLE_API_KEY를 설정해주세요.")


def parse_source_metadata(raw_content: str) -> tuple[str, dict[str, str]]:
    lines = raw_content.splitlines()
    body_lines: list[str] = []
    metadata_lines: list[str] = []
    in_metadata_section = False

    for line in lines:
        stripped = line.strip()
        if stripped.lower() == SOURCE_METADATA_HEADER:
            in_metadata_section = True
            continue

        if in_metadata_section:
            if stripped.startswith("## "):
                in_metadata_section = False
                body_lines.append(line)
                continue
            metadata_lines.append(line)
            continue

        body_lines.append(line)

    metadata: dict[str, str] = {}
    for line in metadata_lines:
        match = re.match(r"^\s*-\s*([A-Za-z_]+)\s*:\s*(.+?)\s*$", line)
        if match:
            metadata[match.group(1)] = match.group(2)

    body_content = "\n".join(body_lines).strip()
    return body_content, metadata


def guess_sub_category(path: Path) -> str:
    return path.stem.replace("_", " ")


def build_document(path: Path) -> Document | None:
    raw_content = path.read_text(encoding="utf-8").strip()
    if not raw_content:
        return None

    body_content, parsed_metadata = parse_source_metadata(raw_content)
    relative_source = path.relative_to(FAQ_ROOT).as_posix()
    path_parts = path.relative_to(FAQ_ROOT).parts
    category = parsed_metadata.get("category") or (path_parts[0] if len(path_parts) > 1 else "general")
    sub_category = parsed_metadata.get("sub_category") or guess_sub_category(path)

    return Document(
        page_content=body_content,
        metadata={
            "source": relative_source,
            "category": category,
            "sub_category": sub_category,
        },
    )


def load_markdown_documents() -> list[Document]:
    if not FAQ_ROOT.exists():
        raise RuntimeError(f"FAQ 폴더를 찾을 수 없습니다: {FAQ_ROOT}")

    documents: list[Document] = []
    for path in sorted(FAQ_ROOT.rglob("*.md")):
        document = build_document(path)
        if document is not None:
            documents.append(document)

    if not documents:
        raise RuntimeError("벡터 DB를 만들 문서가 없습니다. data/faq/**/*.md 파일을 확인해주세요.")

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
