# LocalMate 행정 MVP

외국인 주민이 행정 상황을 입력하면 관련 FAQ를 검색하고, 단계별 행동 안내와 준비물 체크리스트, 기관에서 사용할 한국어 표현까지 정리해 주는 RAG 기반 LangGraph 예제입니다.

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
│     ├─ admin_alien_card_loss.md
│     ├─ admin_address_change.md
│     └─ admin_visa_extension.md
├─ chroma_db/
├─ build_vector_db.py
├─ test_retriever.py
├─ localmate_graph.py
├─ app.py
└─ README.md
```

## Vector DB 생성 방법

`build_vector_db.py`는 `data/faq/*.md` 문서를 읽어 Chroma DB를 다시 만듭니다.
embedding 모델은 반드시 `models/gemini-embedding-001`을 사용합니다.

```powershell
python build_vector_db.py
```

실행이 끝나면 문서 수와 청크 수를 출력합니다.

## Retriever 테스트 방법

아래 명령으로 고정 query 3개에 대한 검색 결과를 확인할 수 있습니다.

```powershell
python test_retriever.py
```

각 query마다 top 3 결과의 `source`, `sub_category`, 문서 일부를 출력합니다.

## LangGraph 실행 방법

직접 콘솔에서 테스트하려면 아래 명령을 실행하세요.

```powershell
python localmate_graph.py
```

빈 입력이면 `외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?` 예시 질문을 사용합니다.

## Streamlit 실행 방법

```powershell
streamlit run app.py
```

앱에서 예시 질문 버튼을 눌러 입력을 채우고 `안내 받기`를 누르면 답변을 Markdown으로 확인할 수 있습니다.

## Embedding 모델 주의사항

- 이 프로젝트의 embedding 모델은 `models/gemini-embedding-001`로 고정합니다.
- 기존 코드에 `models/text-embedding-004`가 있었다면 모두 교체해야 합니다.
- embedding 모델이 바뀌면 기존 `chroma_db`를 그대로 재사용하면 안 됩니다.

## `chroma_db` 삭제 후 재생성해야 하는 경우

아래 상황에서는 기존 `chroma_db`를 삭제하고 다시 만들어야 합니다.

- embedding 모델이 바뀐 경우
- FAQ 문서 내용이 바뀐 경우
- metadata 구조가 바뀐 경우

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

## 오류 안내

- `GOOGLE_API_KEY`가 없으면 `.env 파일에 GOOGLE_API_KEY를 설정해주세요.` 메시지를 출력합니다.
- `chroma_db`가 없으면 `먼저 python build_vector_db.py를 실행해주세요.` 메시지를 출력합니다.
- 모델 호출 실패 시 traceback 대신 사용자용 안내 메시지를 보여주도록 구성했습니다.
