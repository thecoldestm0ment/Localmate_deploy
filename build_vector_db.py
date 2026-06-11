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
DEFAULT_REGION_BY_CATEGORY = {"traffic": "ansan"}
DEFAULT_SOURCE_NAME = "LocalMate internal FAQ"
DEFAULT_SOURCE_URL = "local"
DEFAULT_LAST_CHECKED = "unknown"
DISPLAY_CATEGORY_BY_CATEGORY = {
    "admin": "행정",
    "medical": "의료",
    "traffic": "교통",
}
CATEGORY_ALIASES = {
    "행정": "admin",
    "의료": "medical",
    "교통": "traffic",
}
ALLOWED_SUBCATEGORIES_BY_CATEGORY = {
    "admin": {
        "외국인등록증 분실",
        "주소 변경",
        "체류기간 연장/비자",
        "기관 방문/예약",
        "기타 행정",
    },
    "medical": {
        "일반 진료/약국",
        "야간/응급",
        "건강보험 고지서/보험료",
        "보건소/예방접종",
        "의료비/보험 자격 문의",
    },
    "traffic": {
        "버스 경로 확인",
        "하차 태그·환승",
        "교통카드 충전",
        "교통카드 사용",
        "택시 표현",
        "고정 장소 이동",
        "막차/야간 이동",
    },
}
REQUIRED_METADATA_KEYS = ("source", "category", "sub_category")


def ensure_google_api_key() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(".env 파일에 GOOGLE_API_KEY를 설정해주세요.")


def parse_yaml_frontmatter(raw_content: str) -> tuple[str, dict[str, str]]:
    lines = raw_content.splitlines()
    if not lines or lines[0].strip() != "---":
        return raw_content, {}

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        return raw_content, {}

    metadata: dict[str, str] = {}
    for line in lines[1:closing_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    body_content = "\n".join(lines[closing_index + 1 :]).strip()
    return body_content, metadata


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


def normalize_category(raw_value: str) -> str:
    value = raw_value.strip()
    return CATEGORY_ALIASES.get(value, value.lower())


def guess_sub_category(path: Path) -> str:
    return path.stem.replace("_", " ")


def infer_category(path: Path) -> str:
    relative_parts = path.relative_to(FAQ_ROOT).parts
    return relative_parts[0] if len(relative_parts) > 1 else "general"


def build_metadata(path: Path, raw_metadata: dict[str, str]) -> dict[str, str]:
    relative_source = path.relative_to(FAQ_ROOT).as_posix()
    category = normalize_category(raw_metadata.get("category", infer_category(path)))
    display_category = raw_metadata.get("display_category")
    region = raw_metadata.get("region")

    return {
        "source": relative_source,
        "category": category,
        "display_category": display_category
        or DISPLAY_CATEGORY_BY_CATEGORY.get(category, category),
        "sub_category": raw_metadata.get("sub_category") or guess_sub_category(path),
        "region": region or DEFAULT_REGION_BY_CATEGORY.get(category, "general"),
        "source_name": raw_metadata.get("source_name") or DEFAULT_SOURCE_NAME,
        "source_url": raw_metadata.get("source_url") or DEFAULT_SOURCE_URL,
        "last_checked": raw_metadata.get("last_checked") or DEFAULT_LAST_CHECKED,
    }


def build_document(path: Path) -> Document | None:
    raw_content = path.read_text(encoding="utf-8").strip()
    if not raw_content:
        return None

    without_frontmatter, frontmatter_metadata = parse_yaml_frontmatter(raw_content)
    body_content, source_metadata = parse_source_metadata(without_frontmatter)
    combined_metadata = {**source_metadata, **frontmatter_metadata}

    return Document(
        page_content=body_content,
        metadata=build_metadata(path, combined_metadata),
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

    validate_documents(documents)
    return documents


def validate_documents(documents: list[Document]) -> None:
    seen_sources: set[str] = set()
    errors: list[str] = []

    for document in documents:
        metadata = document.metadata
        source = str(metadata.get("source", "")).strip()
        category = str(metadata.get("category", "")).strip()
        sub_category = str(metadata.get("sub_category", "")).strip()

        for key in REQUIRED_METADATA_KEYS:
            if not str(metadata.get(key, "")).strip():
                errors.append(f"{source or 'unknown'}: missing metadata `{key}`")

        if source in seen_sources:
            errors.append(f"{source}: duplicate source metadata")
        elif source:
            seen_sources.add(source)

        allowed_subcategories = ALLOWED_SUBCATEGORIES_BY_CATEGORY.get(category)
        if allowed_subcategories is None:
            errors.append(f"{source}: unsupported category `{category}`")
        elif sub_category not in allowed_subcategories:
            errors.append(
                f"{source}: unsupported sub_category `{sub_category}` "
                f"for category `{category}`"
            )

    if errors:
        message = "FAQ metadata validation failed:\n" + "\n".join(
            f"- {error}" for error in errors
        )
        raise RuntimeError(message)


def rebuild_vector_db(documents: list[Document]) -> int:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
    )
    chunks = splitter.split_documents(documents)
    add_chunk_indexes(chunks)

    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(DB_DIR),
    )
    return len(chunks)


def add_chunk_indexes(chunks: list[Document]) -> None:
    counts_by_source: dict[str, int] = {}
    for chunk in chunks:
        source = str(chunk.metadata.get("source", "unknown"))
        chunk_index = counts_by_source.get(source, 0)
        chunk.metadata = {
            **chunk.metadata,
            "chunk_index": str(chunk_index),
        }
        counts_by_source[source] = chunk_index + 1


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
