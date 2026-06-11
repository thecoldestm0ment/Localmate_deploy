# LocalMate

외국인 주민을 위한 지역 생활 적응 AI Agent입니다.

사용자의 질문을 `행정`, `의료`, `교통` 카테고리로 나누고, FAQ 문서를 검색한 뒤 상황별 행동 안내, 준비물, 사용할 한국어 표현, 주의사항을 제공합니다.

## 주요 기능

- LangGraph 기반 top-level workflow
- Chroma 기반 FAQ RAG 검색
- 행정 / 의료 / 교통 카테고리 분리
- 새 질문 / 후속 질문 대화 맥락 유지
- `summary`, `checklist_only`, `expression_only`, `detail` 답변 모드 지원
- Streamlit 채팅 UI
- 참고 문서는 사용자 답변 본문이 아니라 expander에서 확인

## 기술 스택

- Python 3.12
- LangChain
- LangGraph
- Chroma
- Google Gemini
- Streamlit
- Pydantic
- python-dotenv

## 프로젝트 구조

```text
langchain-practice/
├─ app.py
├─ build_vector_db.py
├─ localmate_graph.py
├─ test_retriever.py
├─ categories/
│  ├─ __init__.py
│  ├─ types.py
│  ├─ shared.py
│  ├─ response_format.py
│  ├─ admin.py
│  ├─ admin_rules.py
│  ├─ admin_content.py
│  ├─ admin_content_data.py
│  ├─ medical.py
│  ├─ medical_rules.py
│  ├─ medical_content.py
│  ├─ medical_content_data.py
│  ├─ traffic.py
│  ├─ traffic_rules.py
│  └─ traffic_content.py
├─ prompts/
│  ├─ admin_prompts.py
│  └─ traffic_prompts.py
├─ data/
│  ├─ faq/
│  │  ├─ admin/
│  │  ├─ medical/
│  │  └─ traffic/
│  └─ places/
│     └─ ansan_fixed_places.json
├─ test/
│  ├─ test_localmate.py
│  ├─ test_localmate_admin.py
│  ├─ test_localmate_medical.py
│  └─ test_localmate_traffic.py
└─ chroma_db/
```

## 환경 설정

Windows PowerShell 기준입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -U pip setuptools wheel
python -m pip install langchain langchain-core langchain-google-genai langgraph langchain-chroma langchain-text-splitters streamlit python-dotenv pydantic
```

`.env` 파일을 프로젝트 루트에 만듭니다.

```dotenv
GOOGLE_API_KEY=your_google_api_key
```

API key는 코드에 직접 넣지 않습니다.

## Vector DB 생성

FAQ 문서를 Chroma DB로 저장합니다.

```powershell
python build_vector_db.py
```

문서나 embedding 모델이 바뀌면 기존 DB를 삭제하고 다시 생성합니다.

```powershell
Remove-Item -Recurse -Force chroma_db
python build_vector_db.py
```

embedding 모델은 반드시 아래 모델을 사용합니다.

```text
models/gemini-embedding-001
```

## 실행 방법

Retriever 확인:

```powershell
python test_retriever.py
```

LangGraph 콘솔 실행:

```powershell
python localmate_graph.py
```

Streamlit 앱 실행:

```powershell
streamlit run app.py
```

전체 실행 순서:

```powershell
Remove-Item -Recurse -Force chroma_db
python build_vector_db.py
python test_retriever.py
python localmate_graph.py
streamlit run app.py
```

## LangGraph 흐름

`localmate_graph.py`는 최상위 workflow를 담당합니다.

```text
input_validate
→ answer_mode
→ context_check
→ route
→ category_graph
→ normalize_answer
→ final
→ END
```

역할:

- 입력 검증
- 답변 모드 판단
- 새 질문 / 후속 질문 맥락 확인
- 행정 / 의료 / 교통 라우팅
- 카테고리 handler 실행
- 최종 답변 포맷 정리

공개 함수:

```python
run_localmate(user_input: str, context: dict | None = None) -> str
run_localmate_result(user_input: str, context: dict | None = None) -> CategoryResult
```

## 카테고리 구조

각 카테고리는 같은 인터페이스를 사용합니다.

```python
can_handle(user_input: str) -> bool
run_category(user_input: str) -> CategoryResult
```

카테고리별 파일 책임:

- `*_rules.py`: 키워드, 분류 규칙, 세부 intent 판단
- `*_content.py`: 답변 내용, 체크리스트, 표현, 포맷팅
- `*.py`: 카테고리 진입점과 graph/handler
- `prompts/*.py`: LLM prompt

## Traffic 카테고리 범위

교통 카테고리는 실시간 길찾기 서비스가 아닙니다.

지원 범위:

- 교통카드 충전 / 사용
- 버스 승하차 / 하차 태그 / 환승
- 버스 번호와 정류장 확인 방법
- 택시 기사님에게 말할 표현
- 막차와 야간 이동 시 확인할 것
- 안산 고정 장소 중심 안내

지원하는 고정 장소:

- 중앙역
- 한대앞역
- 한양대 ERICA


정확한 정보는 지도 앱, 정류장 안내기, 역 안내판을 함께 확인해야 합니다.

## 테스트

카테고리 통합 테스트:

```powershell
python -m test.test_localmate
```

카테고리별 테스트:

```powershell
python -m test.test_localmate_admin
python -m test.test_localmate_medical
python -m test.test_localmate_traffic
```

Retriever 테스트:

```powershell
python test_retriever.py
python test_retriever_admin.py
python test_retriever_traffic.py
```

## 오류 안내

- `GOOGLE_API_KEY`가 없으면 `.env 파일에 GOOGLE_API_KEY를 설정해주세요.` 메시지가 나옵니다.
- `chroma_db`가 없으면 `먼저 python build_vector_db.py를 실행해주세요.` 메시지가 나옵니다.
- 모델/API 호출 실패 시 traceback 대신 사용자용 오류 메시지를 보여줍니다.

## 주의사항

- 행정/비자/체류 관련 내용은 법률 조언처럼 단정하지 않습니다.
- 의료 카테고리는 진단이나 처방을 하지 않습니다.
- 교통 카테고리는 실시간 위치, 요금, 막차 시간을 지어내지 않습니다.
- FAQ 문서를 수정한 뒤에는 `chroma_db`를 재생성해야 합니다.
