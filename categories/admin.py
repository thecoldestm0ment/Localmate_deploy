from functools import lru_cache
from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from categories.shared import get_llm, get_vectorstore
from categories.types import CategoryResult

CATEGORY_NAME = "admin"
ADMIN_FILTER = {"category": "admin"}
NO_DOCS_WARNING = "관련 문서를 충분히 찾지 못했습니다. 공식 안내 확인이 필요합니다."
GENERATION_ERROR_MESSAGE = "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
CLARIFY_CARD_QUESTION = (
    "어떤 카드를 잃어버리셨나요?\n1. 외국인등록증\n2. 은행 카드\n3. 교통카드/티머니\n4. 학생증"
)
ADMIN_KEYWORDS = [
    "외국인등록증",
    "외국인 등록증",
    "비자",
    "체류",
    "체류기간",
    "체류 자격",
    "체류자격",
    "출입국",
    "주소",
    "주소 변경",
    "주소변경",
    "이사",
    "전입",
    "등록증",
    "행정",
    "신고",
]


class ActionPlanSchema(BaseModel):
    first_checks: list[str] = Field(default_factory=list)
    todo_steps: list[str] = Field(default_factory=list)
    visit_or_online: list[str] = Field(default_factory=list)
    after_checks: list[str] = Field(default_factory=list)


class KoreanExpressionsSchema(BaseModel):
    office: str
    phone: str
    message: str


class AdminDraftSchema(BaseModel):
    action_plan: ActionPlanSchema
    checklist: list[str] = Field(default_factory=list)
    korean_expressions: KoreanExpressionsSchema


class AdminState(TypedDict):
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
    if has_any_keyword(text, ADMIN_KEYWORDS):
        return True

    loss_keywords = ["잃어버", "분실", "없어졌", "사라졌"]
    card_keywords = ["카드", "등록증", "신분증"]
    return has_any_keyword(text, loss_keywords) and has_any_keyword(text, card_keywords)


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


def fallback_bundle(sub_category: str) -> dict[str, object]:
    bundles = {
        "외국인등록증 분실": {
            "action_plan": {
                "first_checks": [
                    "외국인등록증을 마지막으로 본 장소와 시간을 다시 확인하세요.",
                    "분실이 맞는지 먼저 정리하세요.",
                ],
                "todo_steps": [
                    "출입국·외국인 관련 공식 안내에서 분실 신고나 재발급 절차를 확인하세요.",
                    "방문 예약이 필요한지 먼저 확인하세요.",
                    "여권, 사진, 본인 확인 자료를 준비하세요.",
                ],
                "visit_or_online": [
                    "공식 안내에서 방문 접수인지 온라인 확인이 가능한지 살펴보세요.",
                    "관할 기관과 준비물 목록을 다시 확인하세요.",
                ],
                "after_checks": [
                    "접수 후 새 등록증 수령 방법을 확인하세요.",
                    "추가 서류 요청이 있는지 다시 확인하세요.",
                ],
            },
            "checklist": [
                "여권",
                "외국인등록 관련 본인 확인 자료",
                "증명사진",
                "분실 경위 메모",
                "방문 예약 확인 내역",
            ],
            "korean_expressions": {
                "office": "외국인등록증을 잃어버렸어요. 어떻게 하면 될까요?",
                "phone": "안녕하세요. 외국인등록증 분실 후 절차를 문의드리고 싶습니다.",
                "message": "외국인등록증 분실 후 준비물과 절차를 알고 싶습니다.",
            },
        },
        "주소 변경": {
            "action_plan": {
                "first_checks": [
                    "이사한 날짜와 새 주소를 정확히 확인하세요.",
                    "주소 변경 신고 대상인지 공식 안내를 먼저 확인하세요.",
                ],
                "todo_steps": [
                    "관할 기관과 신고 기한을 확인하세요.",
                    "온라인 신청이 가능한지, 방문 예약이 필요한지 확인하세요.",
                    "여권과 거주지 확인 서류를 준비하세요.",
                ],
                "visit_or_online": [
                    "공식 안내에서 온라인 신청 가능 여부를 확인하세요.",
                    "직접 방문이 필요하면 예약 여부를 먼저 확인하세요.",
                ],
                "after_checks": [
                    "주소 정보가 정상 반영되었는지 확인하세요.",
                    "추가 제출 요청이 있는지 다시 확인하세요.",
                ],
            },
            "checklist": [
                "여권",
                "외국인등록 관련 신분 확인 자료",
                "새 주소 확인 서류",
                "거주 확인 자료",
                "방문 예약 확인 내역",
            ],
            "korean_expressions": {
                "office": "이사해서 주소 변경 신고가 필요한지 확인하고 싶어요.",
                "phone": "안녕하세요. 이사 후 주소 변경 신고 방법을 문의드리고 싶습니다.",
                "message": "주소 변경 신고 방법과 준비물을 알려주세요.",
            },
        },
        "체류기간 연장/비자": {
            "action_plan": {
                "first_checks": [
                    "현재 비자 종류와 체류기간 만료일을 확인하세요.",
                    "체류자격과 개인 상황에 따라 절차가 달라질 수 있는지 먼저 생각해 보세요.",
                ],
                "todo_steps": [
                    "공식 안내에서 체류기간 연장 절차를 확인하세요.",
                    "관할 출입국·외국인청 방문 예약 필요 여부를 확인하세요.",
                    "여권과 체류 관련 서류를 준비하세요.",
                ],
                "visit_or_online": [
                    "공식 채널에서 온라인 신청 가능 여부를 확인하세요.",
                    "방문이 필요하면 관할 기관과 준비물을 다시 확인하세요.",
                ],
                "after_checks": [
                    "접수 상태와 추가 서류 요청을 확인하세요.",
                    "처리 기준이나 일정은 공식 안내에서 다시 확인하세요.",
                ],
            },
            "checklist": [
                "여권",
                "외국인등록 관련 신분 확인 자료",
                "현재 체류자격 확인 자료",
                "체류기간 만료일 확인 자료",
                "상황별 추가 서류",
                "방문 예약 확인 내역",
            ],
            "korean_expressions": {
                "office": "비자 기간이 곧 끝나서 체류기간 연장 방법을 확인하고 싶어요.",
                "phone": "안녕하세요. 체류기간 만료 전에 확인할 절차를 문의드리고 싶습니다.",
                "message": "체류기간 연장 관련 준비물과 절차를 알고 싶습니다.",
            },
        },
        "기관 방문/예약": {
            "action_plan": {
                "first_checks": [
                    "어느 기관을 방문해야 하는지 먼저 확인하세요.",
                    "예약이 필요한지 공식 안내를 확인하세요.",
                ],
                "todo_steps": [
                    "방문 목적에 맞는 담당 기관을 확인하세요.",
                    "예약 방법과 준비물을 확인하세요.",
                    "필요한 신분 확인 자료를 준비하세요.",
                ],
                "visit_or_online": [
                    "온라인 예약이 가능한지 확인하세요.",
                    "방문 시간이 정해져 있는지 확인하세요.",
                ],
                "after_checks": [
                    "예약 내용과 방문 시간을 다시 확인하세요.",
                    "추가로 가져가야 하는 자료가 있는지 확인하세요.",
                ],
            },
            "checklist": [
                "여권",
                "방문 목적 관련 안내 내용",
                "예약 확인 내역",
                "본인 확인 자료",
            ],
            "korean_expressions": {
                "office": "방문 예약이 필요한지 확인하고 싶어요.",
                "phone": "안녕하세요. 기관 방문 예약 방법을 문의드리고 싶습니다.",
                "message": "방문 예약과 준비물을 안내해 주세요.",
            },
        },
    }
    default_bundle = {
        "action_plan": {
            "first_checks": ["질문과 관련된 공식 안내를 먼저 확인하세요."],
            "todo_steps": [
                "필요한 기관과 절차를 확인하세요.",
                "본인 상황에 맞는 준비물을 정리하세요.",
            ],
            "visit_or_online": ["방문 또는 온라인 가능 여부를 공식 안내에서 확인하세요."],
            "after_checks": ["처리 후 추가 확인이 필요한지 다시 살펴보세요."],
        },
        "checklist": [
            "여권",
            "본인 확인 자료",
            "방문 또는 신청 관련 안내 내용",
        ],
        "korean_expressions": {
            "office": "이 절차를 어떻게 확인하면 될까요?",
            "phone": "안녕하세요. 관련 절차를 문의드리고 싶습니다.",
            "message": "준비물과 절차를 안내해 주세요.",
        },
    }
    return bundles.get(sub_category, default_bundle)


def normalize_text(text: str) -> str:
    return text.strip().lower()


def has_any_keyword(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def build_initial_state(user_input: str) -> AdminState:
    return AdminState(
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


def classify_admin_node(state: AdminState) -> AdminState:
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


def route_after_classify(state: AdminState) -> str:
    return "final_node" if state["needs_clarification"] else "retrieve_node"


def retrieve_node(state: AdminState) -> AdminState:
    if state["needs_clarification"]:
        return state

    try:
        docs = get_vectorstore().similarity_search(
            state["user_input"],
            k=3,
            filter=ADMIN_FILTER,
        )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(GENERATION_ERROR_MESSAGE) from exc

    warnings = list(state["warnings"])
    if not docs:
        warnings.append(NO_DOCS_WARNING)

    sources: list[str] = []
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
        return "관련 문서를 찾지 못했습니다. 공식 안내를 확인해야 한다는 점만 조심스럽게 안내하세요."

    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        sub_category = doc.metadata.get("sub_category", "unknown")
        parts.append(f"[source={source} | sub_category={sub_category}]\n{doc.page_content}")
    return "\n\n".join(parts)


def plan_node(state: AdminState) -> AdminState:
    context = format_context(state["retrieved_docs"])
    prompt = f"""
당신은 외국인 주민을 위한 행정 생활 안내 도우미입니다.
아래 사용자 질문과 FAQ 문맥만 바탕으로 쉬운 한국어 행동 안내, 준비물 체크리스트, 기관에서 쓸 표현을 작성하세요.

중요 규칙:
- 문서에 없는 수수료, 처리기간, 기관명, 결과를 단정하지 마세요.
- 법률 조언처럼 쓰지 마세요.
- 체류자격과 개인 상황에 따라 달라질 수 있다는 점을 전제로 쓰세요.
- 각 항목은 짧고 바로 행동할 수 있게 작성하세요.
- checklist는 3개 이상 6개 이하로 작성하세요.
- JSON 스키마에 맞게 작성하세요.

사용자 질문:
{state["user_input"]}

상황 분류:
행정 / {state["sub_category"]}

문맥:
{context}
""".strip()

    try:
        result = invoke_structured(prompt, AdminDraftSchema)
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
        bundle = fallback_bundle(state["sub_category"])

    return {
        **state,
        "action_plan": bundle["action_plan"],
        "checklist": bundle["checklist"][:6],
        "korean_expressions": bundle["korean_expressions"],
    }


def checklist_node(state: AdminState) -> AdminState:
    items = list(state["checklist"])
    if not items:
        items = fallback_bundle(state["sub_category"])["checklist"]

    return {
        **state,
        "checklist": items[:6],
    }


def expression_node(state: AdminState) -> AdminState:
    expressions = dict(state["korean_expressions"])
    if not all(expressions.values()):
        expressions = fallback_bundle(state["sub_category"])["korean_expressions"]

    return {
        **state,
        "korean_expressions": expressions,
    }


def warning_node(state: AdminState) -> AdminState:
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


def final_node(state: AdminState) -> AdminState:
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
    graph = StateGraph(AdminState)
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
