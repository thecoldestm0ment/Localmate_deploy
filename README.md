# LocalMate 카테고리 분리 구조

외국인 주민이 질문을 입력하면 카테고리를 먼저 나누고, 각 카테고리 모듈이 독립적으로 답변을 생성하는 구조입니다.  
현재는 `localmate_graph.py`가 얇은 라우터 역할만 하고, 행정 로직은 `categories/admin.py`, 의료 로직은 `categories/medical.py`에서 관리합니다.

## 환경 설정

- 운영 환경: Windows PowerShell
- Python: 3.12
- 가상환경 예시: `D:\dev\langchain-practice\.venv`
- API key는 `.env`의 `GOOGLE_API_KEY`를 사용합니다.

## 패키지 설치

```powershell
python -m pip install -U pip setuptools wheel
python -m pip install langchain langchain-core langchain-google-genai langgraph langchain-chroma langchain-text-splitters streamlit python-dotenv pydantic
```

## `.env` 작성 예시

```dotenv
GOOGLE_API_KEY=your_google_api_key
```

## 프로젝트 구조

```text
langchain-practice/
├─ .env
├─ .gitignore
├─ data/
│  └─ faq/
│     ├─ admin/
│     │  ├─ admin_alien_card_loss.md
│     │  ├─ admin_address_change.md
│     │  └─ admin_visa_extension.md
│     └─ medical/
├─ chroma_db/
├─ categories/
│  ├─ __init__.py
│  ├─ shared.py
│  ├─ admin.py
│  └─ medical.py
├─ build_vector_db.py
├─ test_retriever.py
├─ localmate_graph.py
├─ app.py
└─ README.md
```

## 카테고리 분리 원칙

- `localmate_graph.py`는 `run_localmate(user_input: str) -> str` 진입점만 제공합니다.
- `categories/admin.py`와 `categories/medical.py`는 각각 `can_handle()`와 `run_category()` 인터페이스를 구현합니다.
- 공용 설정은 `categories/shared.py`에만 둡니다.
- 카테고리별 프롬프트, 그래프, 포맷팅은 각 파일 안에서 독립적으로 관리합니다.

## Vector DB 생성 방법

`build_vector_db.py`는 `data/faq/**/*.md` 문서를 재귀적으로 읽고, 문서 위치를 바탕으로 `category`, `source`, `sub_category` metadata를 저장합니다.

- `source`: `admin/admin_address_change.md` 같은 상대 경로
- `category`: `admin`, `medical` 같은 machine value
- `sub_category`: 문서의 `source metadata` 섹션 또는 파일명 기반 값

embedding 모델은 반드시 `models/gemini-embedding-001`을 사용합니다.

```powershell
python build_vector_db.py
```

실행이 끝나면 문서 수와 청크 수를 출력합니다.

## Retriever 테스트 방법

```powershell
python test_retriever.py
```

현재 테스트 스크립트는 행정 query 3개를 `category=admin` 필터로 검색하고, `source`, `category`, `sub_category`, 문서 일부를 출력합니다.

## LangGraph 실행 방법

```powershell
python localmate_graph.py
```

빈 입력이면 `외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?` 예시 질문을 사용합니다.

## Streamlit 실행 방법

```powershell
streamlit run app.py
```

앱은 계속 `run_localmate()`만 호출하므로, 카테고리별 구현이 분리되어도 UI 코드는 크게 바뀌지 않습니다.

## Embedding 모델 주의사항

- 이 프로젝트의 embedding 모델은 `models/gemini-embedding-001`로 고정합니다.
- 기존 코드에 `models/text-embedding-004`가 있었다면 모두 교체해야 합니다.
- embedding 모델이 바뀌면 기존 `chroma_db`를 그대로 재사용하면 안 됩니다.

## `chroma_db` 삭제 후 재생성해야 하는 경우

아래 상황에서는 기존 `chroma_db`를 삭제하고 다시 만들어야 합니다.

- embedding 모델이 바뀐 경우
- FAQ 문서 내용이 바뀐 경우
- metadata 구조가 바뀐 경우
- FAQ 폴더 구조가 바뀐 경우

`build_vector_db.py`는 실행 시 기존 `chroma_db`를 삭제하고 새로 생성합니다.

## 실행 순서

```powershell
python -m pip install -U pip setuptools wheel
python -m pip install langchain langchain-core langchain-google-genai langgraph langchain-chroma langchain-text-splitters streamlit python-dotenv pydantic

python build_vector_db.py
python test_retriever.py
python localmate_graph.py
streamlit run app.py
```

## 현재 상태

- 행정 카테고리는 `categories/admin.py`에서 동작합니다.
- 의료 카테고리는 `categories/medical.py` 인터페이스와 라우팅만 준비되어 있고, 실제 세부 로직은 팀원이 이어서 구현할 수 있도록 분리되어 있습니다.

## 오류 안내

- `GOOGLE_API_KEY`가 없으면 `.env 파일에 GOOGLE_API_KEY를 설정해주세요.` 메시지를 출력합니다.
- `chroma_db`가 없으면 `먼저 python build_vector_db.py를 실행해주세요.` 메시지를 출력합니다.
- 모델 호출 실패 시 traceback 대신 사용자용 안내 메시지를 보여주도록 구성했습니다.
