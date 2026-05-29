# LocalMate 카테고리 분리 구조

외국인 주민이 질문을 입력하면 카테고리를 먼저 나누고, 각 카테고리 모듈이 독립적으로 답변을 생성하는 구조입니다.  
현재는 `localmate_graph.py`가 얇은 router 역할만 하고, 행정 로직은 `categories/admin.py`, 의료 로직은 `categories/medical.py`, 교통 로직은 `categories/traffic.py`에서 관리합니다.

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
├─ app.py
├─ build_vector_db.py
├─ localmate_graph.py
├─ README.md
├─ test_retriever.py
├─ categories/
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ medical.py
│  ├─ shared.py
│  ├─ traffic.py
│  └─ types.py
├─ prompts/
│  └─ traffic_prompts.py
├─ data/
│  ├─ faq/
│  │  ├─ admin/
│  │  ├─ medical/
│  │  └─ traffic/
│  └─ places/
│     └─ ansan_fixed_places.json
└─ chroma_db/
```

## 카테고리 분리 원칙

- `localmate_graph.py`는 `run_localmate(user_input: str) -> str` 진입점을 제공합니다.
- `categories/__init__.py`가 `CATEGORY_HANDLERS` registry를 관리합니다.
- 각 카테고리 모듈은 `can_handle()`와 `run_category()` 인터페이스를 구현합니다.
- 내부적으로 `run_category()`는 `CategoryResult`를 반환하고, router가 최종 사용자 응답 문자열을 꺼내 씁니다.
- 공용 Chroma DB는 하나만 사용하고, 각 카테고리는 metadata `category` filter로 자기 문서만 검색합니다.

## Traffic 카테고리 범위

traffic 카테고리는 실시간 길찾기 엔진이 아니라, 한국 교통 이용에 익숙하지 않은 외국인 주민을 위한 생활 안내 MVP입니다.

- 교통카드 구매, 충전, 잔액 확인, 기본 사용법
- 버스 탑승, 하차 태그, 환승 기본 안내
- 택시 이용과 기사님에게 말할 표현
- 막차와 야간 이동 시 무엇을 확인해야 하는지 안내
- 안산 고정 장소 예시 중심 이동 안내

현재 지원하는 고정 장소는 아래 3개입니다.

- 중앙역
- 한대앞역
- 한양대 ERICA

실시간 교통 API는 사용하지 않습니다.

- 정확한 버스 도착 시간 제공 안 함
- 정확한 막차 시간 제공 안 함
- 정확한 택시 요금 계산 안 함

정확한 경로와 실시간 정보는 지도 앱, 정류장 안내기, 역 안내판을 함께 확인해야 합니다.

## Vector DB 생성 방법

`build_vector_db.py`는 `data/faq/**/*.md` 문서를 재귀적으로 읽고, YAML frontmatter와 source metadata를 파싱합니다.

metadata에는 최소 아래 값을 저장합니다.

- `source`
- `category`
- `display_category`
- `sub_category`
- `region`
- `source_name`
- `source_url`
- `last_checked`

`source`는 `traffic/transport_card.md` 같은 `data/faq` 기준 상대 경로로 저장합니다.

embedding 모델은 반드시 `models/gemini-embedding-001`을 사용합니다.

```powershell
python build_vector_db.py
```

실행이 끝나면 문서 수와 청크 수를 출력합니다.

## Retriever 테스트 방법

```powershell
python test_retriever.py
```

현재 테스트 스크립트는 admin과 traffic query를 각각 category filter로 검색하고, `source`, `category`, `display_category`, `sub_category`, 문서 일부를 출력합니다.

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

## `chroma_db` 삭제 후 재생성해야 하는 경우

아래 상황에서는 기존 `chroma_db`를 삭제하고 다시 만들어야 합니다.

- embedding 모델이 바뀐 경우
- FAQ 문서 내용이 바뀐 경우
- metadata 구조가 바뀐 경우
- FAQ 폴더 구조가 바뀐 경우
- traffic 문서나 장소 데이터가 추가되거나 수정된 경우

문서를 추가한 뒤에는 아래처럼 기존 `chroma_db`를 삭제하고 다시 생성하세요.

```powershell
Remove-Item -Recurse -Force chroma_db
python build_vector_db.py
```

## 실행 순서

```powershell
Remove-Item -Recurse -Force chroma_db
python build_vector_db.py
python test_retriever.py
python localmate_graph.py
streamlit run app.py
```

## 현재 상태

- 행정 카테고리는 `categories/admin.py`에서 동작합니다.
- 의료 카테고리는 `categories/medical.py` 인터페이스와 placeholder 응답 구조만 준비되어 있습니다.
- 교통 카테고리는 `categories/traffic.py`에서 동작하며, 교통 문서는 `data/faq/traffic/`에 저장합니다.
- 안산 고정 장소 데이터는 `data/places/ansan_fixed_places.json`에서 관리합니다.

## 오류 안내

- `GOOGLE_API_KEY`가 없으면 `.env 파일에 GOOGLE_API_KEY를 설정해주세요.` 메시지를 출력합니다.
- `chroma_db`가 없으면 `먼저 python build_vector_db.py를 실행해주세요.` 메시지를 출력합니다.
- 모델 호출 실패 시 traceback 대신 사용자용 안내 메시지를 보여주도록 구성했습니다.
