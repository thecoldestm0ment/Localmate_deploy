import os
from dataclasses import dataclass
from pathlib import Path
from textwrap import shorten

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from localmate_graph import run_localmate_result

DB_DIR = Path("chroma_db")
EMBEDDING_MODEL = "models/gemini-embedding-001"


@dataclass(frozen=True)
class LocalMateCase:
    name: str
    query: str
    category: str
    sub_category: str
    needs_clarification: bool
    contains: tuple[str, ...]


@dataclass(frozen=True)
class RetrieverCase:
    name: str
    category: str
    query: str
    expected_source: str
    expected_sub_category: str


def ensure_ready() -> None:
    load_dotenv()

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(".env 파일에 GOOGLE_API_KEY를 설정해주세요.")

    if not DB_DIR.exists():
        raise RuntimeError("먼저 python build_vector_db.py를 실행해주세요.")


def validate_localmate_case(case: LocalMateCase) -> list[str]:
    result = run_localmate_result(case.query)
    failures: list[str] = []

    if result.category != case.category:
        failures.append(f"category expected={case.category} actual={result.category}")

    if result.sub_category != case.sub_category:
        failures.append(
            f"sub_category expected={case.sub_category} actual={result.sub_category}"
        )

    if result.needs_clarification != case.needs_clarification:
        failures.append(
            "needs_clarification "
            f"expected={case.needs_clarification} actual={result.needs_clarification}"
        )

    for expected_text in case.contains:
        if expected_text not in result.answer:
            failures.append(f"missing text: {expected_text}")

    return failures


def run_localmate_cases(title: str, cases: list[LocalMateCase]) -> None:
    ensure_ready()
    passed = 0

    print(f"[{title}]")
    for case in cases:
        failures = validate_localmate_case(case)
        if failures:
            print(f"[FAIL] {case.name}")
            for failure in failures:
                print(f"  - {failure}")
            print(f"  query: {case.query}")
            print()
            continue

        passed += 1
        print(f"[PASS] {case.name}")

    print()
    print(f"summary: {passed}/{len(cases)} passed")

    if passed != len(cases):
        raise SystemExit(1)


def create_vectorstore() -> Chroma:
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    return Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embeddings,
    )


def validate_retriever_case(
    case: RetrieverCase,
    vectorstore: Chroma,
) -> list[str]:
    docs = vectorstore.similarity_search(
        case.query,
        k=3,
        filter={"category": case.category},
    )
    failures: list[str] = []

    if not docs:
        return [f"no docs returned for query: {case.query}"]

    top_doc = docs[0]
    if top_doc.metadata.get("category") != case.category:
        failures.append(
            "category mismatch "
            f"expected={case.category} actual={top_doc.metadata.get('category')}"
        )

    if case.expected_source not in [doc.metadata.get("source") for doc in docs]:
        failures.append(f"missing source: {case.expected_source}")

    if top_doc.metadata.get("sub_category") != case.expected_sub_category:
        failures.append(
            "sub_category mismatch "
            f"expected={case.expected_sub_category} "
            f"actual={top_doc.metadata.get('sub_category')}"
        )

    return failures


def print_retriever_results(
    case: RetrieverCase,
    vectorstore: Chroma,
) -> None:
    docs = vectorstore.similarity_search(
        case.query,
        k=3,
        filter={"category": case.category},
    )

    print("=" * 60)
    print(f"name: {case.name}")
    print(f"category: {case.category}")
    print(f"query: {case.query}")

    if not docs:
        print("검색 결과가 없습니다.")
        return

    for index, doc in enumerate(docs, start=1):
        preview = shorten(
            doc.page_content.replace("\n", " "),
            width=220,
            placeholder="...",
        )
        print(f"[결과 {index}]")
        print(f"source: {doc.metadata.get('source', 'unknown')}")
        print(f"category: {doc.metadata.get('category', 'unknown')}")
        print(f"display_category: {doc.metadata.get('display_category', 'unknown')}")
        print(f"sub_category: {doc.metadata.get('sub_category', 'unknown')}")
        print(f"content: {preview}")
        print()


def run_retriever_cases(title: str, cases: list[RetrieverCase]) -> None:
    ensure_ready()
    vectorstore = create_vectorstore()
    passed = 0

    print(f"[{title}]")
    for case in cases:
        failures = validate_retriever_case(case, vectorstore)
        print_retriever_results(case, vectorstore)
        if failures:
            print(f"[FAIL] {case.name}")
            for failure in failures:
                print(f"  - {failure}")
            print()
            continue

        passed += 1
        print(f"[PASS] {case.name}")
        print()

    print(f"summary: {passed}/{len(cases)} passed")

    if passed != len(cases):
        raise SystemExit(1)
