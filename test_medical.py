import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

DB_DIR = Path("chroma_db")
EMBEDDING_MODEL = "models/gemini-embedding-001"

# 의료 파트 전용 테스트 케이스 리스트
TEST_CASES = [
    {"category": "medical", "query": "이가 너무 아파요 어디로 가야 돼요?"},
    {"category": "medical", "query": "병원 가면 돈 많이 드나요?"},
    {"category": "medical", "query": "못 걷겠어요 살려주세요 구급차 외국인도 무료인가요?"},
    {"category": "medical", "query": "건강 보험 고지서가 나왔어요 어떻게 해야 돼요?"}
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

    print("\n" + "#" * 60)
    print("[의료 파트 전용 하드코딩 RAG 검색 테스트 시작]")
    print("#" * 60 + "\n")

    for case in TEST_CASES:
        print("=" * 60)
        print(f"category: {case['category']}")
        print(f"query: {case['query']}")
        print("-" * 60)

        # 의료 카테고리 필터링 및 유사도 검색 수행
        docs = vectorstore.similarity_search(
            case["query"],
            k=3,
            filter={"category": case["category"]},
        )
        
        if not docs:
            print("검색 결과가 없습니다.\n")
            continue

        for index, doc in enumerate(docs, start=1):
            # 글자 수 제한 없이 마크다운 청크 원문을 그대로 할당합니다.
            preview = doc.page_content
            
            print(f"[결과 {index}]")
            print(f"source: {doc.metadata.get('source', 'unknown')}")
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