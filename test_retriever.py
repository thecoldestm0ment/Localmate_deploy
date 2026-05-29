import os
from pathlib import Path
from textwrap import shorten

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

DB_DIR = Path("chroma_db")
EMBEDDING_MODEL = "models/gemini-embedding-001"
TEST_QUERIES = [
    "외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?",
    "이사했는데 주소 변경 신고를 해야 하나요?",
    "비자 기간이 곧 끝나요. 뭘 해야 해요?",
]


def main() -> None:
    load_dotenv()

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(".env 파일에 GOOGLE_API_KEY를 설정해주세요.")

    if not DB_DIR.exists():
        print("먼저 python build_vector_db.py를 실행해주세요.")
        raise SystemExit(1)

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embeddings,
    )

    for query in TEST_QUERIES:
        print("=" * 60)
        print(f"query: {query}")

        docs = vectorstore.similarity_search(query, k=3, filter={"category": "admin"})
        if not docs:
            print("검색 결과가 없습니다.")
            continue

        for index, doc in enumerate(docs, start=1):
            preview = shorten(doc.page_content.replace("\n", " "), width=220, placeholder="...")
            print(f"[결과 {index}]")
            print(f"source: {doc.metadata.get('source', 'unknown')}")
            print(f"category: {doc.metadata.get('category', 'unknown')}")
            print(f"sub_category: {doc.metadata.get('sub_category', 'unknown')}")
            print(f"content: {preview}")
            print()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)
    except Exception:
        print("retriever 테스트 중 오류가 발생했습니다. 설정과 벡터 DB 상태를 확인해주세요.")
        raise SystemExit(1)
