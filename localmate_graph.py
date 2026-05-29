import os
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

load_dotenv()

DB_DIR = Path("chroma_db")
EMBEDDING_MODEL = "models/gemini-embedding-001"
CHAT_MODEL = "gemini-2.5-flash"
NO_DOCS_WARNING = "관련 문서를 충분히 찾지 못했습니다. 공식 안내 확인이 필요합니다."
CLARIFY_CARD_QUESTION = (
    "어떤 카드를 잃어버리셨나요? 외국인등록증, 은행 카드, 교통카드 중 어떤 것인지 알려주세요."
)


class ActionPlanSchema(BaseModel):
    first_checks: list[str] = Field(default_factory=list)
    todo_steps: list[str] = Field(default_factory=list)
    visit_or_online: list[str] = Field(default_factory=list)
    after_checks: list[str] = Field(default_factory=list)


class ChecklistSchema(BaseModel):
    items: list[str] = Field(default_factory=list)


class KoreanExpressionsSchema(BaseModel):
    office: str
    phone: str
    message: str


class LocalMateState(TypedDict):
    user_input: str
    category: str
    sub_category: str
    needs_clarification: bool
    clarifying_question: str
    retrieved_docs: list[Document]
    action_plan: dict[str, list[str]]
    checklist: list[str]
    korean_expressions: dict[str, str]
    warnings: list[str]
    sources: list[str]
    final_answer: str


def ensure_google_api_key() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(".env 파일에 GOOGLE_API_KEY를 설정해주세요.")


@lru_cache(maxsize=1)
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    ensure_google_api_key()
    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    if not DB_DIR.exists():
        raise RuntimeError("먼저 python build_vector_db.py를 실행해주세요.")
    return Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=get_embeddings(),
    )


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    ensure_google_api_key()
    return ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0.2,
    )


def invoke_structured(prompt: str, schema: type[BaseModel]) -> BaseModel:
    try:
        structured_llm = get_llm().with_structured_output(schema)
        return structured_llm.invoke(prompt)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(
            "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
        ) from exc


def normalize_text(text: str) -> str:
    return text.strip().lower()


def has_any_keyword(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def build_initial_state(user_input: str) -> LocalMateState:
    return LocalMateState(
        user_input=user_input,
        category="행정",
        sub_category="",
        needs_clarification=False,
        clarifying_question="",
        retrieved_docs=[],
        action_plan={
            "first_checks": [],
            "todo_steps": [],
            "visit_or_online": [],
            "after_checks": [],
        },
        checklist=[],
        korean_expressions={"office": "", "phone": "", "message": ""},
        warnings=[],
        sources=[],
        final_answer="",
    )


def classify_admin_node(state: LocalMateState) -> LocalMateState:
    text = normalize_text(state["user_input"])
    loss_keywords = ["잃어버", "분실", "없어졌", "사라졌"]
    specific_alien_card_keywords = ["외국인등록증", "외국인 등록증", "alien registration card", "arc"]
    generic_card_keywords = ["카드", "등록증", "신분증"]
    address_keywords = ["주소 변경", "주소변경", "주소", "이사", "전입"]
    visa_keywords = ["비자", "체류기간", "체류 기간", "체류자격", "체류 자격", "연장", "만료", "체류"]
    visit_keywords = ["예약", "방문"]

    if has_any_keyword(text, specific_alien_card_keywords) and has_any_keyword(text, loss_keywords):
        sub_category = "외국인등록증 분실"
        needs_clarification = False
        clarifying_question = ""
    elif (
        has_any_keyword(text, generic_card_keywords)
        and has_any_keyword(text, loss_keywords)
        and not has_any_keyword(text, specific_alien_card_keywords + ["은행", "교통"])
    ):
        sub_category = "애매함"
        needs_clarification = True
        clarifying_question = CLARIFY_CARD_QUESTION
    elif has_any_keyword(text, address_keywords):
        sub_category = "주소 변경"
        needs_clarification = False
        clarifying_question = ""
    elif has_any_keyword(text, visa_keywords):
        sub_category = "체류기간 연장/비자"
        needs_clarification = False
        clarifying_question = ""
    elif has_any_keyword(text, visit_keywords):
        sub_category = "기관 방문/예약"
        needs_clarification = False
        clarifying_question = ""
    else:
        sub_category = "기타 행정"
        needs_clarification = False
        clarifying_question = ""

    return {
        **state,
        "category": "행정",
        "sub_category": sub_category,
        "needs_clarification": needs_clarification,
        "clarifying_question": clarifying_question,
    }


def route_after_classify(state: LocalMateState) -> str:
    return "final_node" if state["needs_clarification"] else "retrieve_node"


def retrieve_node(state: LocalMateState) -> LocalMateState:
    if state["needs_clarification"]:
        return state

    try:
        docs = get_vectorstore().similarity_search(state["user_input"], k=3)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(
            "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
        ) from exc

    warnings = list(state["warnings"])
    if not docs:
        warnings.append(NO_DOCS_WARNING)

    sources = []
    for doc in docs:
        source = doc.metadata.get("source")
        if source and source not in sources:
            sources.append(source)

    return {
        **state,
        "retrieved_docs": docs,
        "warnings": warnings,
        "sources": sources,
    }


def format_context(docs: list[Document]) -> str:
    if not docs:
        return "관련 문서를 찾지 못했습니다. 확인된 문서가 없으므로 매우 조심스럽게 일반 안내만 작성해야 합니다."

    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        sub_category = doc.metadata.get("sub_category", "unknown")
        parts.append(f"[source={source} | sub_category={sub_category}]\n{doc.page_content}")
    return "\n\n".join(parts)


def plan_node(state: LocalMateState) -> LocalMateState:
    context = format_context(state["retrieved_docs"])
    prompt = f"""
당신은 외국인 주민을 위한 행정 생활 안내 도우미입니다.
아래 사용자 질문과 FAQ 문맥만 바탕으로 쉬운 한국어 행동 안내를 작성하세요.

중요 규칙:
- 문서에 없는 수수료, 처리기간, 기관명, 결과를 단정하지 마세요.
- 법률 조언처럼 쓰지 마세요.
- 체류자격과 개인 상황에 따라 달라질 수 있다는 점을 전제로 쓰세요.
- 각 항목은 짧고 바로 행동할 수 있게 작성하세요.
- JSON 스키마에 맞게 작성하세요.

사용자 질문:
{state["user_input"]}

상황 분류:
행정 / {state["sub_category"]}

문맥:
{context}
""".strip()

    result = invoke_structured(prompt, ActionPlanSchema)
    return {
        **state,
        "action_plan": {
            "first_checks": result.first_checks or [],
            "todo_steps": result.todo_steps or [],
            "visit_or_online": result.visit_or_online or [],
            "after_checks": result.after_checks or [],
        },
    }


def checklist_node(state: LocalMateState) -> LocalMateState:
    context = format_context(state["retrieved_docs"])
    prompt = f"""
당신은 외국인 주민을 위한 행정 생활 안내 도우미입니다.
아래 문맥을 바탕으로 준비물 체크리스트를 3개 이상 6개 이하로 정리하세요.

중요 규칙:
- 문서에 있는 준비물과 문맥에서 자연스럽게 추론되는 수준만 사용하세요.
- 확실하지 않은 서류는 '추가로 요청될 수 있는 서류'처럼 조심스럽게 쓰세요.
- 각 항목은 짧은 명사구로 작성하세요.
- JSON 스키마에 맞게 작성하세요.

사용자 질문:
{state["user_input"]}

상황 분류:
행정 / {state["sub_category"]}

문맥:
{context}
""".strip()

    result = invoke_structured(prompt, ChecklistSchema)
    items = [item.strip() for item in result.items if item.strip()]

    if not items:
        items = ["여권", "본인 확인 자료", "방문 전 확인한 안내 내용"]

    return {
        **state,
        "checklist": items[:6],
    }


def expression_node(state: LocalMateState) -> LocalMateState:
    context = format_context(state["retrieved_docs"])
    prompt = f"""
당신은 외국인 주민이 기관에서 바로 사용할 수 있는 쉬운 한국어 문장을 만드는 도우미입니다.
문맥과 사용자 질문을 참고해서 아래 3가지 문장을 만드세요.

중요 규칙:
- 짧고 쉬운 한국어로 쓰세요.
- 문서에 없는 사실을 단정하지 마세요.
- 기관 방문 문장, 전화 문의 문장, 문자/이메일 문장을 각각 한 문장씩 작성하세요.
- JSON 스키마에 맞게 작성하세요.

사용자 질문:
{state["user_input"]}

상황 분류:
행정 / {state["sub_category"]}

문맥:
{context}
""".strip()

    result = invoke_structured(prompt, KoreanExpressionsSchema)
    return {
        **state,
        "korean_expressions": {
            "office": result.office.strip(),
            "phone": result.phone.strip(),
            "message": result.message.strip(),
        },
    }


def warning_node(state: LocalMateState) -> LocalMateState:
    warnings = [
        "체류자격과 개인 상황에 따라 절차가 달라질 수 있습니다.",
        "방문 전 공식 안내를 꼭 확인해주세요.",
        "긴급하거나 법적 문제가 있으면 담당 기관에 직접 문의해주세요.",
    ]

    for warning in state["warnings"]:
        if warning not in warnings:
            warnings.append(warning)

    return {
        **state,
        "warnings": warnings,
    }


def format_bullets(items: list[str]) -> str:
    if not items:
        return "- 확인이 필요한 정보가 있습니다."
    return "\n".join(f"- {item}" for item in items)


def format_numbered(items: list[str]) -> str:
    if not items:
        return "1. 공식 안내를 먼저 확인해주세요."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def format_checkboxes(items: list[str]) -> str:
    if not items:
        return "□ 준비물을 다시 확인해주세요."
    return "\n".join(f"□ {item}" for item in items)


def format_sources(sources: list[str]) -> str:
    if not sources:
        return "- 관련 문서를 찾지 못했습니다."
    return "\n".join(f"- {source}" for source in sources)


def final_node(state: LocalMateState) -> LocalMateState:
    if state["needs_clarification"]:
        return {
            **state,
            "final_answer": state["clarifying_question"],
        }

    action_plan = state["action_plan"]
    final_answer = "\n".join(
        [
            "## 상황 분류",
            f"행정 / {state['sub_category']}",
            "",
            "## 먼저 확인할 것",
            format_bullets(action_plan.get("first_checks", [])),
            "",
            "## 해야 할 일",
            format_numbered(action_plan.get("todo_steps", [])),
            "",
            "## 방문/온라인 확인",
            format_bullets(action_plan.get("visit_or_online", [])),
            "",
            "## 처리 후 확인할 것",
            format_bullets(action_plan.get("after_checks", [])),
            "",
            "## 준비물 체크리스트",
            format_checkboxes(state["checklist"]),
            "",
            "## 기관에서 사용할 한국어",
            f'- 기관에서 말할 문장:\n  "{state["korean_expressions"].get("office", "")}"',
            f'- 전화로 물어볼 문장:\n  "{state["korean_expressions"].get("phone", "")}"',
            f'- 문자/이메일 문장:\n  "{state["korean_expressions"].get("message", "")}"',
            "",
            "## 주의사항",
            format_bullets(state["warnings"]),
            "",
            "## 참고 문서",
            format_sources(state["sources"]),
        ]
    )

    return {
        **state,
        "final_answer": final_answer,
    }


def build_graph():
    graph = StateGraph(LocalMateState)
    graph.add_node("classify_admin_node", classify_admin_node)
    graph.add_node("retrieve_node", retrieve_node)
    graph.add_node("plan_node", plan_node)
    graph.add_node("checklist_node", checklist_node)
    graph.add_node("expression_node", expression_node)
    graph.add_node("warning_node", warning_node)
    graph.add_node("final_node", final_node)

    graph.set_entry_point("classify_admin_node")
    graph.add_conditional_edges(
        "classify_admin_node",
        route_after_classify,
        {
            "retrieve_node": "retrieve_node",
            "final_node": "final_node",
        },
    )
    graph.add_edge("retrieve_node", "plan_node")
    graph.add_edge("plan_node", "checklist_node")
    graph.add_edge("checklist_node", "expression_node")
    graph.add_edge("expression_node", "warning_node")
    graph.add_edge("warning_node", "final_node")
    graph.add_edge("final_node", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_graph():
    return build_graph()


def run_localmate(user_input: str) -> str:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    try:
        result = get_graph().invoke(build_initial_state(cleaned_input))
        return result["final_answer"]
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(
            "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
        ) from exc


def main() -> None:
    default_question = "외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?"

    try:
        user_input = input("질문을 입력해주세요. 빈 입력이면 예시 질문을 사용합니다: ").strip()
    except EOFError:
        user_input = ""

    if not user_input:
        user_input = default_question

    print(run_localmate(user_input))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)
