import logging
import os
import re
from dataclasses import replace
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from categories import CATEGORY_REGISTRY, CategoryHandlerSpec, admin, medical, traffic
from categories.shared import get_llm
from categories.types import CategoryResult

logger = logging.getLogger(__name__)

DEFAULT_QUESTION = "외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?"
TOP_LEVEL_CLARIFICATION_QUESTION = (
    "행정 문의인지, 의료 문의인지, 교통 문의인지 조금 더 알려주세요."
)

ROUTER_MODE_ENV = "LOCALMATE_ROUTER"
RULE_ROUTER_MODE = "rule"

ANSWER_MODE_DEFAULT = "default"
ANSWER_MODE_SUMMARY = "summary"
ANSWER_MODE_CHECKLIST = "checklist_only"
ANSWER_MODE_EXPRESSION = "expression_only"
ANSWER_MODE_DETAIL = "detail"
QUESTION_MODE_NEW = "new"
QUESTION_MODE_FOLLOW_UP = "follow_up"
FOLLOW_UP_WITHOUT_CONTEXT_QUESTION = (
    "아직 이어갈 이전 질문이 없어요. 먼저 새 질문으로 상황을 알려주세요.\n"
    "(There is no previous question to continue from. Please start with a new question first.)"
)

URGENT_MEDICAL_KEYWORDS = (
    "응급", "응급실", "119", "기절", "호흡곤란", "숨이 안", "피가 많이",
    "가슴 통증", "심한 통증", "갑자기 아파", "emergency", "emergency room",
)

CHECKLIST_HINTS = (
    "준비물만", "준비물 만", "체크리스트만", "체크리스트만 줘",
    "준비물 다시", "체크리스트 다시",
)
SUMMARY_HINTS = ("짧게", "간단히", "요약", "다시 요약")
EXPRESSION_HINTS = (
    "문장만", "표현만", "한국어 문장만", "영어 문장만", "뭐라고 말",
    "뭐라고 물어", "전화로 뭐라고", "기관에 뭐라고", "기사한테 뭐라고",
    "기사님한테 뭐라고", "어떻게 말",
)
DETAIL_HINTS = ("더 자세히", "상세히", "자세하게", "자세히 알려")
FOLLOW_UP_HINTS = CHECKLIST_HINTS + SUMMARY_HINTS + EXPRESSION_HINTS + DETAIL_HINTS + (
    "다시 알려", "방금", "이전", "그거",
)

CATEGORY_LABELS = {
    "admin": "행정",
    "medical": "의료",
    "traffic": "교통",
}

CATEGORY_MODULE_MAP = {
    "행정": admin,
    "의료": medical,
    "교통": traffic,
}

SAFETY_FALLBACKS = {
    "admin": "체류자격과 개인 상황에 따라 절차와 필요 서류가 달라질 수 있어요. 공식 안내를 꼭 확인해주세요.",
    "medical": "저는 진단이나 처방을 할 수 없어요. 심한 증상이나 응급 상황이면 119 또는 응급실에 바로 문의해주세요.",
    "traffic": "실시간 도착 시간, 막차 시간, 요금은 변동될 수 있어요. 지도 앱이나 현장 안내기를 함께 확인해주세요.",
}


class LocalMateState(TypedDict, total=False):
    user_input: str
    cleaned_input: str
    question_mode: str
    answer_mode: str

    category: str | None
    sub_category: str | None
    route_reason: str
    routed_input: str

    previous_category: str | None
    previous_sub_category: str | None
    previous_answer_summary: str | None
    chat_history: list[dict[str, Any]]

    selected_handler: CategoryHandlerSpec | None
    category_result: CategoryResult
    final_answer: str
    sources: list[str]
    needs_clarification: bool
    clarifying_question: str | None


class RouterSchema(BaseModel):
    category: Literal["행정", "의료", "교통", "미분류"] = Field(
        description="사용자 질문의 최종 목적에 맞는 카테고리"
    )
    reason: str = Field(description="분류 근거")


ROUTER_PROMPT_TEMPLATE = """당신은 LocalMate의 상위 카테고리 라우터입니다.
사용자의 최종 목적을 보고 행정, 의료, 교통, 미분류 중 하나만 고르세요.

분류 기준:
- 행정: 외국인등록증, 주소 변경, 비자, 체류기간, 기관 방문, 행정 서류
- 의료: 증상, 병원 이용, 약국, 예방접종, 응급 상황, 건강보험, 의료비 납부, 건강 관련 문의
- 교통: 버스, 지하철, 택시, 교통카드, 환승, 막차, 길찾기, 이동 방법
- 미분류: 위 카테고리를 판단하기 어려운 질문

중요:
- 목적지가 병원이나 행정기관이어도 "가는 법", "버스", "택시"처럼 이동 방법을 묻는 질문은 교통입니다.
- 응급실, 119, 심한 통증처럼 긴급 의료 신호가 있으면 의료입니다.
- 건강보험 고지서, 의료비 청구서, 보험료 납부처럼 내용이 건강/의료와 관련된 서류나 절차는 "서류"나 "납부"라는 단어가 있어도 의료입니다. 행정으로 분류하지 마세요.
- 단어 하나만 보지 말고 문장 전체의 목적을 보세요.

사용자 질문:
{user_input}
"""


def normalize_text(text: str) -> str:
    return text.strip().lower()


def get_handler_for_module(module: object) -> CategoryHandlerSpec | None:
    for spec in CATEGORY_REGISTRY:
        if spec.module == module:
            return spec
    return None


def get_handler_for_category(category: str | None) -> CategoryHandlerSpec | None:
    if not category:
        return None
    for spec in CATEGORY_REGISTRY:
        if getattr(spec.module, "CATEGORY_NAME", None) == category:
            return spec
    return None


def route_urgent_medical(user_input: str) -> CategoryHandlerSpec | None:
    text = normalize_text(user_input)
    if any(keyword in text for keyword in URGENT_MEDICAL_KEYWORDS):
        return get_handler_for_module(medical)
    return None


def route_with_rules(user_input: str) -> CategoryHandlerSpec | None:
    matching_handlers = [
        spec
        for spec in CATEGORY_REGISTRY
        if spec.module.can_handle(user_input)
    ]
    if not matching_handlers:
        return None
    return max(matching_handlers, key=lambda spec: spec.priority)


def route_with_llm_intent(user_input: str) -> CategoryHandlerSpec | None:
    structured_llm = get_llm().with_structured_output(RouterSchema)
    prompt = ROUTER_PROMPT_TEMPLATE.format(user_input=user_input)

    try:
        response = structured_llm.invoke(prompt)
    except Exception:
        logger.debug("LLM intent router failed", exc_info=True)
        return None

    logger.debug(
        "AI intent router classified query",
        extra={
            "user_input": user_input,
            "category": response.category,
            "reason": response.reason,
        },
    )

    target_module = CATEGORY_MODULE_MAP.get(response.category)
    if target_module is None:
        return None
    return get_handler_for_module(target_module)


def route_user_input(user_input: str) -> CategoryHandlerSpec | None:
    urgent_handler = route_urgent_medical(user_input)
    if urgent_handler is not None:
        return urgent_handler

    if os.getenv(ROUTER_MODE_ENV, "").lower() == RULE_ROUTER_MODE:
        return route_with_rules(user_input)

    selected_handler = route_with_llm_intent(user_input)
    if selected_handler is not None:
        return selected_handler

    return route_with_rules(user_input)


def detect_answer_mode(user_input: str) -> str:
    text = normalize_text(user_input)
    if any(hint in text for hint in DETAIL_HINTS):
        return ANSWER_MODE_DETAIL
    if any(hint in text for hint in CHECKLIST_HINTS):
        return ANSWER_MODE_CHECKLIST
    if any(hint in text for hint in EXPRESSION_HINTS):
        return ANSWER_MODE_EXPRESSION
    if any(hint in text for hint in SUMMARY_HINTS):
        return ANSWER_MODE_SUMMARY
    return ANSWER_MODE_DEFAULT


def is_follow_up_request(user_input: str, answer_mode: str, context: dict[str, Any]) -> bool:
    if context.get("question_mode") == QUESTION_MODE_FOLLOW_UP:
        return True
    if context.get("question_mode") == QUESTION_MODE_NEW:
        return False
    if not context.get("previous_category"):
        return False
    if answer_mode != ANSWER_MODE_DEFAULT:
        return True

    text = normalize_text(user_input)
    return len(text) <= 40 and any(hint in text for hint in FOLLOW_UP_HINTS)


def is_generic_follow_up(user_input: str) -> bool:
    text = normalize_text(user_input)
    return len(text) <= 40 and any(hint in text for hint in FOLLOW_UP_HINTS)


def choose_handler(
    user_input: str,
    context: dict[str, Any],
    answer_mode: str,
) -> tuple[CategoryHandlerSpec | None, str]:
    if context.get("question_mode") == QUESTION_MODE_NEW:
        return route_user_input(user_input), user_input

    previous_handler = get_handler_for_category(context.get("previous_category"))

    if previous_handler and is_follow_up_request(user_input, answer_mode, context):
        current_handler = route_urgent_medical(user_input) or route_with_rules(user_input)
        if current_handler is None:
            return previous_handler, build_follow_up_query(user_input, context)

        current_category = getattr(current_handler.module, "CATEGORY_NAME", None)
        previous_category = getattr(previous_handler.module, "CATEGORY_NAME", None)
        if current_category == previous_category or is_generic_follow_up(user_input):
            return previous_handler, build_follow_up_query(user_input, context)

        return current_handler, user_input

    return route_user_input(user_input), user_input


def build_follow_up_query(user_input: str, context: dict[str, Any]) -> str:
    previous_category = context.get("previous_category") or ""
    previous_sub_category = context.get("previous_sub_category") or ""
    previous_summary = context.get("previous_answer_summary") or ""
    recent_history = context.get("chat_history") or []

    recent_lines = []
    for item in recent_history[-3:]:
        if isinstance(item, dict):
            query = item.get("user") or item.get("query") or ""
            answer = item.get("assistant") or item.get("answer_summary") or ""
            if query:
                recent_lines.append(f"사용자: {query}")
            if answer:
                recent_lines.append(f"LocalMate: {str(answer)[:180]}")

    parts = [
        f"이전 카테고리: {previous_category}",
        f"이전 세부 상황: {previous_sub_category}",
    ]
    if previous_summary:
        parts.append(f"이전 안내 요약: {previous_summary}")
    if recent_lines:
        parts.append("최근 대화:\n" + "\n".join(recent_lines))
    parts.append(f"이번 요청: {user_input}")
    return "\n".join(parts)


def context_from_state(state: LocalMateState) -> dict[str, Any]:
    return {
        "question_mode": state.get("question_mode"),
        "previous_category": state.get("previous_category"),
        "previous_sub_category": state.get("previous_sub_category"),
        "previous_answer_summary": state.get("previous_answer_summary"),
        "chat_history": state.get("chat_history") or [],
    }


def input_validate_node(state: LocalMateState) -> LocalMateState:
    cleaned_input = state.get("user_input", "").strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    question_mode = state.get("question_mode")
    updates: LocalMateState = {
        "cleaned_input": cleaned_input,
        "chat_history": state.get("chat_history") or [],
    }

    if question_mode == QUESTION_MODE_NEW:
        updates.update({
            "previous_category": None,
            "previous_sub_category": None,
            "previous_answer_summary": None,
        })

    return updates


def answer_mode_node(state: LocalMateState) -> LocalMateState:
    return {
        "answer_mode": detect_answer_mode(state["cleaned_input"]),
    }


def context_check_node(state: LocalMateState) -> LocalMateState:
    answer_mode = state.get("answer_mode", ANSWER_MODE_DEFAULT)
    context = context_from_state(state)
    if not should_require_previous_context(state["cleaned_input"], context, answer_mode):
        return {}

    result = CategoryResult.clarification(
        FOLLOW_UP_WITHOUT_CONTEXT_QUESTION,
        answer_mode=answer_mode,
        answer_summary=FOLLOW_UP_WITHOUT_CONTEXT_QUESTION,
    )
    return {
        "category_result": result,
        "category": result.category,
        "sub_category": result.sub_category,
        "needs_clarification": True,
        "clarifying_question": result.clarifying_question,
        "route_reason": "follow_up_without_context",
    }


def route_node(state: LocalMateState) -> LocalMateState:
    answer_mode = state.get("answer_mode", ANSWER_MODE_DEFAULT)
    selected_handler, routed_input = choose_handler(
        state["cleaned_input"],
        context_from_state(state),
        answer_mode,
    )

    if selected_handler is None:
        result = CategoryResult.clarification(
            TOP_LEVEL_CLARIFICATION_QUESTION,
            answer_mode=answer_mode,
            answer_summary=TOP_LEVEL_CLARIFICATION_QUESTION,
        )
        return {
            "category_result": result,
            "needs_clarification": True,
            "clarifying_question": result.clarifying_question,
            "route_reason": "top_level_clarification",
        }

    category = getattr(selected_handler.module, "CATEGORY_NAME", None)
    return {
        "selected_handler": selected_handler,
        "routed_input": routed_input,
        "category": category,
        "route_reason": f"routed_to_{category or 'unknown'}",
    }


def category_graph_node(state: LocalMateState) -> LocalMateState:
    selected_handler = state.get("selected_handler")
    if selected_handler is None:
        result = CategoryResult.clarification(
            TOP_LEVEL_CLARIFICATION_QUESTION,
            answer_mode=state.get("answer_mode", ANSWER_MODE_DEFAULT),
            answer_summary=TOP_LEVEL_CLARIFICATION_QUESTION,
        )
        return {"category_result": result}

    result = selected_handler.module.run_category(
        state.get("routed_input") or state["cleaned_input"]
    )
    return {"category_result": result}


def normalize_answer_node(state: LocalMateState) -> LocalMateState:
    result = normalize_category_result(
        state["category_result"],
        state.get("answer_mode", ANSWER_MODE_DEFAULT),
    )
    return {
        "category_result": result,
        "category": result.category,
        "sub_category": result.sub_category,
        "sources": list(result.sources),
        "needs_clarification": result.needs_clarification,
        "clarifying_question": result.clarifying_question,
    }


def final_node(state: LocalMateState) -> LocalMateState:
    result = state.get("category_result")
    if result is None:
        result = CategoryResult.clarification(
            TOP_LEVEL_CLARIFICATION_QUESTION,
            answer_mode=state.get("answer_mode", ANSWER_MODE_DEFAULT),
            answer_summary=TOP_LEVEL_CLARIFICATION_QUESTION,
        )

    return {
        "category_result": result,
        "final_answer": result.answer,
        "category": result.category,
        "sub_category": result.sub_category,
        "sources": list(result.sources),
        "needs_clarification": result.needs_clarification,
        "clarifying_question": result.clarifying_question,
    }


def should_skip_to_final(state: LocalMateState) -> str:
    if state.get("category_result") is not None:
        return "final"
    return "continue"


def build_localmate_state_graph():
    graph = StateGraph(LocalMateState)
    graph.add_node("input_validate", input_validate_node)
    graph.add_node("answer_mode", answer_mode_node)
    graph.add_node("context_check", context_check_node)
    graph.add_node("route", route_node)
    graph.add_node("category_graph", category_graph_node)
    graph.add_node("normalize_answer", normalize_answer_node)
    graph.add_node("final", final_node)

    graph.set_entry_point("input_validate")
    graph.add_edge("input_validate", "answer_mode")
    graph.add_edge("answer_mode", "context_check")
    graph.add_conditional_edges(
        "context_check",
        should_skip_to_final,
        {"final": "final", "continue": "route"},
    )
    graph.add_conditional_edges(
        "route",
        should_skip_to_final,
        {"final": "final", "continue": "category_graph"},
    )
    graph.add_edge("category_graph", "normalize_answer")
    graph.add_edge("normalize_answer", "final")
    graph.add_edge("final", END)
    return graph.compile()


LOCALMATE_STATE_GRAPH = build_localmate_state_graph()


def run_localmate_result(
    user_input: str,
    context: dict[str, Any] | None = None,
) -> CategoryResult:
    context = context or {}
    initial_state: LocalMateState = {
        "user_input": user_input,
        "question_mode": context.get("question_mode"),
        "previous_category": context.get("previous_category"),
        "previous_sub_category": context.get("previous_sub_category"),
        "previous_answer_summary": context.get("previous_answer_summary"),
        "chat_history": context.get("chat_history") or [],
    }
    final_state = LOCALMATE_STATE_GRAPH.invoke(initial_state)
    result = final_state.get("category_result")
    if result is None:
        raise RuntimeError("안내를 생성하는 중 오류가 발생했습니다. 설정을 확인해주세요.")
    return result


def run_localmate(user_input: str, context: dict[str, Any] | None = None) -> str:
    return run_localmate_result(user_input, context=context).answer


def should_require_previous_context(
    user_input: str,
    context: dict[str, Any],
    answer_mode: str,
) -> bool:
    has_previous_context = bool(context.get("previous_category"))
    if has_previous_context:
        return False
    if context.get("question_mode") == QUESTION_MODE_FOLLOW_UP:
        return True
    if context.get("question_mode") == QUESTION_MODE_NEW:
        return False
    return answer_mode != ANSWER_MODE_DEFAULT or is_generic_follow_up(user_input)


def normalize_category_result(result: CategoryResult, answer_mode: str) -> CategoryResult:
    raw_answer = result.raw_answer or result.answer
    if result.needs_clarification:
        summary = summarize_text(result.answer)
        return replace(
            result,
            answer=strip_source_section(result.answer),
            answer_mode=answer_mode,
            answer_summary=summary,
            raw_answer=raw_answer,
        )

    formatted_answer = format_answer_for_mode(result, answer_mode)
    return replace(
        result,
        answer=formatted_answer,
        answer_mode=answer_mode,
        answer_summary=summarize_text(formatted_answer),
        raw_answer=raw_answer,
    )


def format_answer_for_mode(result: CategoryResult, answer_mode: str) -> str:
    parsed = parse_markdown_sections(result.answer)
    sections = [section for section in parsed["sections"] if not is_source_section(section)]
    display_category = CATEGORY_LABELS.get(result.category or "", result.category or "미분류")
    classification = f"{display_category} / {result.sub_category or '-'}"
    expression_section = find_section(sections, "expression")

    content = ExtractedContent(
        intro=compact_body(parsed["intro"], max_items=2),
        action=find_section_body(sections, "action"),
        checklist=find_section_body(sections, "checklist"),
        expression=expression_section["body"] if expression_section else "",
        expression_title=clean_expression_title(expression_section),
        warning=find_section_body(sections, "warning") or get_safety_fallback(result.category),
    )

    if answer_mode == ANSWER_MODE_DETAIL:
        return build_detail_answer(classification, content, sections)
    if answer_mode == ANSWER_MODE_SUMMARY:
        return build_summary_answer(classification, content)
    if answer_mode == ANSWER_MODE_CHECKLIST:
        return build_focus_answer(
            classification=classification,
            title="준비물",
            body=content.checklist,
            warning=content.warning,
        )
    if answer_mode == ANSWER_MODE_EXPRESSION:
        return build_focus_answer(
            classification=classification,
            title=content.expression_title,
            body=content.expression,
            warning=content.warning,
        )
    return build_default_answer(classification, content)


class ExtractedContent:
    def __init__(
        self,
        intro: str,
        action: str,
        checklist: str,
        expression: str,
        expression_title: str,
        warning: str,
    ) -> None:
        self.intro = intro
        self.action = action
        self.checklist = checklist
        self.expression = expression
        self.expression_title = expression_title
        self.warning = warning


def parse_markdown_sections(answer: str) -> dict[str, Any]:
    lines = strip_source_section(answer).splitlines()
    intro_lines: list[str] = []
    sections: list[dict[str, str]] = []
    current_heading: str | None = None
    current_body: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_heading is None:
                intro_lines = current_body
            else:
                sections.append({
                    "heading": current_heading.strip(),
                    "body": "\n".join(current_body).strip(),
                })
            current_heading = line.removeprefix("## ").strip()
            current_body = []
        else:
            current_body.append(line)

    if current_heading is None:
        intro_lines = current_body
    else:
        sections.append({
            "heading": current_heading.strip(),
            "body": "\n".join(current_body).strip(),
        })

    return {
        "intro": "\n".join(intro_lines).strip(),
        "sections": sections,
    }


def strip_source_section(answer: str) -> str:
    pattern = r"\n?##\s*(참고\s*문서|참고한\s*문서)[\s\S]*$"
    return re.sub(pattern, "", answer).strip()


def is_source_section(section: dict[str, str]) -> bool:
    heading = section["heading"].replace(" ", "")
    body = section["body"]
    if "참고문서" in heading or "참고한문서" in heading:
        return True
    return ".md" in body and ("admin/" in body or "traffic/" in body or "medical/" in body)


def build_default_answer(classification: str, content: ExtractedContent) -> str:
    parts = []
    if content.intro:
        parts.append(content.intro)

    parts.extend([
        f"**상황 분류:** {classification}",
        "**지금 할 일**\n" + compact_body(content.action, max_items=4),
    ])
    if content.checklist:
        parts.append("**준비물**\n" + compact_body(content.checklist, max_items=5))
    if content.expression:
        parts.append(f"**{content.expression_title}**\n" + compact_body(content.expression, max_items=3))
    if content.warning:
        parts.append("**주의**\n" + compact_body(content.warning, max_items=2))
    return "\n\n".join(part for part in parts if part.strip()).strip()


def build_detail_answer(
    classification: str,
    content: ExtractedContent,
    sections: list[dict[str, str]],
) -> str:
    parts = []
    if content.intro:
        parts.append(content.intro)
    parts.append(f"**상황 분류:** {classification}")

    for section in sections:
        if is_classification_section(section):
            continue
        body = compact_body(section["body"], max_items=6)
        if body:
            parts.append(f"**{clean_heading(section['heading'])}**\n{body}")

    if content.warning and not any(section_matches_role(section, "warning") for section in sections):
        parts.append("**주의**\n" + compact_body(content.warning, max_items=3))
    return "\n\n".join(parts).strip()


def build_summary_answer(classification: str, content: ExtractedContent) -> str:
    summary = content.action or content.intro
    parts = [
        f"**상황 분류:** {classification}",
        "**요약**\n" + compact_body(summary, max_items=3),
    ]
    if content.warning:
        parts.append("**꼭 확인할 점**\n" + compact_body(content.warning, max_items=2))
    return "\n\n".join(parts).strip()


def build_focus_answer(
    classification: str,
    title: str,
    body: str,
    warning: str,
) -> str:
    if not body:
        body = "이전 답변에서 해당 항목을 충분히 찾지 못했습니다. 공식 안내나 담당 기관에 한 번 더 확인해주세요."

    parts = [
        f"**상황 분류:** {classification}",
        f"**{title}**\n{compact_body(body, max_items=6)}",
    ]
    if warning:
        parts.append("**주의**\n" + compact_body(warning, max_items=2))
    return "\n\n".join(parts).strip()


def find_section_body(sections: list[dict[str, str]], role: str) -> str:
    section = find_section(sections, role)
    if section:
        return section["body"]

    non_classification = [section for section in sections if not is_classification_section(section)]
    if not non_classification:
        return ""

    if role == "warning":
        return non_classification[-1]["body"] if len(non_classification) >= 4 else ""

    fallback_index = {
        "action": 0,
        "checklist": 1,
        "expression": 2,
    }.get(role, 0)

    try:
        return non_classification[fallback_index]["body"]
    except IndexError:
        return ""


def find_section(sections: list[dict[str, str]], role: str) -> dict[str, str] | None:
    for section in sections:
        if section_matches_role(section, role):
            return section
    return None


def clean_expression_title(section: dict[str, str] | None) -> str:
    if not section:
        return "사용할 수 있는 한국어"
    heading = clean_heading(section["heading"])
    return heading or "사용할 수 있는 한국어"


def section_matches_role(section: dict[str, str], role: str) -> bool:
    heading = section["heading"].replace(" ", "")
    body = section["body"]
    if role == "action":
        return any(token in heading for token in ("해야", "확인", "방법", "행동", "안내", "할일"))
    if role == "checklist":
        return "체크" in heading or "준비물" in heading or "□" in body
    if role == "expression":
        return any(token in heading for token in ("한국어", "문장", "표현", "말"))
    if role == "warning":
        return "주의" in heading or "확인할점" in heading
    return False


def is_classification_section(section: dict[str, str]) -> bool:
    heading = section["heading"].replace(" ", "")
    body = section["body"]
    return "상황분류" in heading or bool(re.match(r"^(행정|의료|교통)\s*/", body.strip()))


def clean_heading(heading: str) -> str:
    return heading.strip() or "안내"


def compact_body(body: str, max_items: int = 4) -> str:
    lines = [line.rstrip() for line in body.splitlines()]
    items: list[str] = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^(\d+\.|-|□)", stripped):
            if current:
                items.append(" ".join(current).strip())
            current = [stripped]
        elif current:
            current.append(stripped)
        else:
            items.append(stripped)

    if current:
        items.append(" ".join(current).strip())

    return "\n".join(items[:max_items]).strip()


def get_safety_fallback(category: str | None) -> str:
    return SAFETY_FALLBACKS.get(category or "", "상황에 따라 절차가 달라질 수 있으니 공식 안내를 확인해주세요.")


def summarize_text(answer: str, limit: int = 220) -> str:
    text = re.sub(r"#+\s*", "", answer)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def main() -> None:
    try:
        user_input = input(
            "질문을 입력해주세요. 빈 입력이면 예시 질문을 사용합니다: "
        ).strip()
    except EOFError:
        user_input = ""

    if not user_input:
        user_input = DEFAULT_QUESTION

    print(run_localmate(user_input))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)
