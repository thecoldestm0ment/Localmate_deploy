# LocalMate

외국인 주민을 위한 행정, 의료, 교통 생활 안내 AI Agent입니다.

사용자가 자연어로 상황을 입력하면 LocalMate가 질문 의도를 분류하고, FAQ 문서를 기반으로 행동 안내, 준비물, 현장에서 사용할 한국어 표현, 주의사항을 제공합니다.

## 주요 기능

- 행정 / 의료 / 교통 카테고리별 생활 안내
- LangGraph 기반 단계별 Agent workflow
- Chroma Vector DB 기반 FAQ 검색
- 새 질문 / 후속 질문 대화 맥락 처리
- Streamlit 채팅 UI 제공

## 기술 스택

- Python 3.12
- LangChain, LangGraph
- Chroma
- Google Gemini
- Streamlit
- python-dotenv, Pydantic

## 실행 방법

Windows PowerShell 기준입니다.

1. 가상환경 생성 및 활성화

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 패키지 설치

```powershell
python -m pip install -U pip setuptools wheel
python -m pip install langchain langchain-core langchain-google-genai langgraph langchain-chroma langchain-text-splitters streamlit python-dotenv pydantic
```

3. `.env` 파일 생성

프로젝트 루트에 `.env` 파일을 만들고 Google API key를 설정합니다.

```dotenv
GOOGLE_API_KEY=your_google_api_key
```

4. Vector DB 생성

```powershell
python build_vector_db.py
```

5. Streamlit 앱 실행

```powershell
streamlit run app.py
```

## 테스트

Retriever 동작 확인:

```powershell
python test_retriever.py
```

교통 카테고리 회귀 테스트:

```powershell
python -m test.test_localmate_traffic
```

## 참고 사항

- FAQ 문서를 수정한 뒤에는 `python build_vector_db.py`를 다시 실행해야 합니다.
- `.env` 파일과 `chroma_db/`는 Git에 포함하지 않습니다.
- 의료 답변은 진단이나 처방을 대신하지 않습니다.
- 교통 답변은 실시간 위치, 요금, 막차 시간을 직접 조회하지 않습니다.
