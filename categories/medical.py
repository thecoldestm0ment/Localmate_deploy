from functools import lru_cache
from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from categories.medical_content import (
    build_final_answer, format_context,
    get_fallback_bundle, get_primary_source,
    merge_medical_warnings,
)
from categories.medical_rules import (
    MEDICAL_FILTER,
    MEDICAL_KEYWORDS,
    CATEGORY_NAME,
    DISPLAY_CATEGORY,
    GENERATION_ERROR_MESSAGE,
    NO_DOCS_WARNING,
    ROUTE_PRIORITY,
    classify_medical_input,
    has_any_keyword,
    is_ambiguous_medical_input,
    normalize_text,
)
from categories.shared import get_llm, get_vectorstore
from categories.types import CategoryResult
from prompts.medical_prompts import render_medical_plan_prompt


# LLM의 구조화된 출력을 받기 위한 Pydantic 스키마 정의
class ActionPlanSchema(BaseModel):
    first_checks: list[str] = Field(default_factory=list)
    todo_steps: list[str] = Field(default_factory=list)
    visit_or_online: list[str] = Field(default_factory=list)
    after_checks: list[str] = Field(default_factory=list)


class KoreanExpressionsSchema(BaseModel):
    office: str
    phone: str
    message: str


class MedicalDraftSchema(BaseModel):
    action_plan: ActionPlanSchema
    checklist: list[str] = Field(default_factory=list)
    korean_expressions: KoreanExpressionsSchema


# LangGraph 내부에서 데이터를 전달할 상태 구조 정의
class MedicalState(TypedDict):
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


def can_handle(user_input: str) -> bool:
    text = normalize_text(user_input)
    return has_any_keyword(text, MEDICAL_KEYWORDS) or is_ambiguous_medical_input(text)


def run_category(user_input: str) -> CategoryResult:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    try:
        result = get_graph().invoke(build_initial_state(cleaned_input))
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(GENERATION_ERROR_MESSAGE) from exc

    if result["needs_clarification"]:
        return CategoryResult.clarification(
            result["clarifying_question"],
            category=CATEGORY_NAME,
            sub_category=result["sub_category"],
            warnings=result["warnings"],
        )

    return CategoryResult.success(
        result["final_answer"],
        category=CATEGORY_NAME,
        sub_category=result["sub_category"],
        sources=result["sources"],
        warnings=result["warnings"],
    )


def invoke_structured(prompt: str, schema: type[BaseModel]) -> BaseModel:
    try:
        structured_llm = get_llm().with_structured_output(schema)
        return structured_llm.invoke(prompt)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(GENERATION_ERROR_MESSAGE) from exc


def build_initial_state(user_input: str) -> MedicalState:
    return {
        "user_input": user_input,
        "category": DISPLAY_CATEGORY,
        "sub_category": "",
        "needs_clarification": False,
        "clarifying_question": "",
        "retrieved_docs": [],
        "action_plan": {
            "first_checks": [],
            "todo_steps": [],
            "visit_or_online": [],
            "after_checks": [],
        },
        "checklist": [],
        "korean_expressions": {"office": "", "phone": "", "message": ""},
        "warnings": [],
        "sources": [],
        "final_answer": "",
    }


def classify_medical_node(state: MedicalState) -> MedicalState:
    return {
        **state,
        **classify_medical_input(state["user_input"]),
    }


def route_after_classify(state: MedicalState) -> str:
    return "final_node" if state["needs_clarification"] else "retrieve_node"


def retrieve_node(state: MedicalState) -> MedicalState:
    if state["needs_clarification"]:
        return state

    try:
        docs = get_vectorstore().similarity_search(
            state["user_input"],
            k=3,
            filter=MEDICAL_FILTER,
        )
    except RuntimeError:
        raise
    except Exception:
        docs = []

    warnings = list(state["warnings"])
    if not docs:
        warnings.append(NO_DOCS_WARNING)

    sources: list[str] = []
    primary_source = get_primary_source(state["sub_category"])
    if primary_source:
        sources.append(primary_source)

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


def plan_node(state: MedicalState) -> MedicalState:
    prompt = render_medical_plan_prompt(
        user_input=state["user_input"],
        sub_category=state["sub_category"],
        context=format_context(state["retrieved_docs"]),
    )

    try:
        result = invoke_structured(prompt, MedicalDraftSchema)
        bundle = {
            "action_plan": {
                "first_checks": result.action_plan.first_checks or [],
                "todo_steps": result.action_plan.todo_steps or [],
                "visit_or_online": result.action_plan.visit_or_online or [],
                "after_checks": result.action_plan.after_checks or [],
            },
            "checklist": [item.strip() for item in result.checklist if item.strip()],
            "korean_expressions": {
                "office": result.korean_expressions.office.strip(),
                "phone": result.korean_expressions.phone.strip(),
                "message": result.korean_expressions.message.strip(),
            },
        }
    except RuntimeError as exc:
        if str(exc) != GENERATION_ERROR_MESSAGE:
            raise
        bundle = get_fallback_bundle(state["sub_category"])

    return {
        **state,
        "action_plan": bundle["action_plan"],
        "checklist": list(bundle["checklist"])[:6],
        "korean_expressions": dict(bundle["korean_expressions"]),
    }


def checklist_node(state: MedicalState) -> MedicalState:
    items = list(state["checklist"])
    if not items:
        fallback = get_fallback_bundle(state["sub_category"])
        items = list(fallback["checklist"])

    return {
        **state,
        "checklist": items[:6],
    }


def expression_node(state: MedicalState) -> MedicalState:
    expressions = dict(state["korean_expressions"])
    if not all(expressions.values()):
        fallback = get_fallback_bundle(state["sub_category"])
        expressions = dict(fallback["korean_expressions"])

    return {
        **state,
        "korean_expressions": expressions,
    }


def warning_node(state: MedicalState) -> MedicalState:
    return {
        **state,
        "warnings": merge_medical_warnings(
            state["warnings"],
            sub_category=state["sub_category"],
            user_input=state["user_input"],
        ),
    }


def final_node(state: MedicalState) -> MedicalState:
    if state["needs_clarification"]:
        return {
            **state,
            "final_answer": state["clarifying_question"],
        }

    return {
        **state,
        "final_answer": build_final_answer(
            sub_category=state["sub_category"],
            action_plan=state["action_plan"],
            checklist=state["checklist"],
            korean_expressions=state["korean_expressions"],
            warnings=state["warnings"],
            sources=state["sources"],
        ),
    }


def build_graph():
    graph = StateGraph(MedicalState)
    graph.add_node("classify_medical_node", classify_medical_node)
    graph.add_node("retrieve_node", retrieve_node)
    graph.add_node("plan_node", plan_node)
    graph.add_node("checklist_node", checklist_node)
    graph.add_node("expression_node", expression_node)
    graph.add_node("warning_node", warning_node)
    graph.add_node("final_node", final_node)

    graph.set_entry_point("classify_medical_node")
    graph.add_conditional_edges(
        "classify_medical_node",
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
