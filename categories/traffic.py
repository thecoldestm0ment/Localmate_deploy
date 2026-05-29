import json
import re
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, StateGraph

from categories.shared import get_vectorstore
from categories.types import CategoryResult
from prompts.traffic_prompts import (
    TRAFFIC_ACTION_GUIDE_PROMPT,
    TRAFFIC_CARD_LOSS_QUESTION,
    TRAFFIC_CLASSIFICATION_PROMPT,
    TRAFFIC_EXPRESSION_PROMPT,
    TRAFFIC_FINAL_TEMPLATE,
    TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION,
    TRAFFIC_FIXED_PLACE_SECTION_TEMPLATE,
    TRAFFIC_GENERIC_CLARIFICATION_QUESTION,
    TRAFFIC_REALTIME_BUS_RESPONSE,
    TRAFFIC_ROUTE_CLARIFICATION_QUESTION,
    TRAFFIC_UNSUPPORTED_PLACE_QUESTION,
    TRAFFIC_WARNING_BULLETS,
    TRAFFIC_WARNING_PROMPT,
)

CATEGORY_NAME = "traffic"
TRAFFIC_FILTER = {"category": "traffic"}
PLACES_PATH = Path("data/places/ansan_fixed_places.json")
PRIMARY_SOURCE_BY_SUBCATEGORY = {
    "교통카드/결제": "traffic/transport_card.md",
    "버스 이용/환승": "traffic/bus_transfer.md",
    "택시 이용": "traffic/taxi_usage.md",
    "고정 장소 이동": "traffic/ansan_fixed_places_guide.md",
    "막차/야간 이동": "traffic/late_night_transport.md",
}
GENERATION_ERROR_MESSAGE = "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
NO_DOCS_WARNING = "관련 교통 문서를 충분히 찾지 못했습니다. 공식 안내를 함께 확인해주세요."
TRANSPORT_CARD_KEYWORDS = (
    "교통카드", "버스카드", "티머니",
    "캐시비", "t-money", "transportation card",
)
CARD_PAYMENT_KEYWORDS = ("충전", "잔액", "결제", "사용법")
BUS_KEYWORDS = ("버스", "bus", "환승", "하차", "정류장")
SUBWAY_KEYWORDS = ("지하철", "전철", "subway", "metro")
TAXI_KEYWORDS = ("택시", "taxi", "카카오택시")
LATE_NIGHT_KEYWORDS = ("막차", "첫차", "야간", "밤늦", "심야", "late night")
REALTIME_KEYWORDS = (
    "실시간", "몇 분 뒤", "언제 와",
    "도착 시간", "몇 시", "arrive", "arrival",
)
ROUTE_INTENT_KEYWORDS = (
    "어떻게 가", "가는 법", "가려면", "길찾기", "길 찾기",
    "이동", "가고 싶", "버스로", "지하철로", "전철로",
    "택시 타고", "타고 가", "how to get", "go to",
)
VAGUE_BUS_QUESTIONS = (
    "버스 타도 돼요?", "지하철 타도 돼요?", "전철 타도 돼요?",
)
GENERIC_CARD_KEYWORDS = ("카드", "등록증", "신분증", "card")
CARD_LOSS_KEYWORDS = ("잃어버", "분실", "없어졌", "사라졌", "lost")
TRAFFIC_MODE_KEYWORDS = (
    BUS_KEYWORDS + SUBWAY_KEYWORDS + TAXI_KEYWORDS + LATE_NIGHT_KEYWORDS
)
GENERAL_DESTINATION_HINTS = (
    "병원", "은행", "출입국", "사무소", "학교", "ERICA", "에리카",
)
TRANSIT_PAYMENT_CONTEXT = ("교통", "버스", "지하철", "티머니", "캐시비")
TRANSIT_ROUTE_KEYWORDS = BUS_KEYWORDS + SUBWAY_KEYWORDS


class TrafficState(TypedDict):
    user_input: str
    category: str
    sub_category: str
    needs_clarification: bool
    clarifying_question: str
    retrieved_docs: list[Document]
    sources: list[str]
    warnings: list[str]
    action_steps: list[str]
    checklist: list[str]
    expressions: list[str]
    origin: str
    destination: str
    mentioned_places: list[str]
    route_like: bool
    final_answer: str


def can_handle(user_input: str) -> bool:
    text = normalize_text(user_input)

    if is_generic_card_loss(text):
        return False

    if is_transport_card_question(text):
        return True

    if has_any_keyword(text, TRAFFIC_MODE_KEYWORDS):
        return True

    if has_supported_place_alias(text) and has_route_like_intent(text):
        return True

    if has_route_like_intent(text) and has_any_keyword(text, GENERAL_DESTINATION_HINTS):
        return True

    return False


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


@lru_cache(maxsize=1)
def get_graph():
    graph = StateGraph(TrafficState)
    graph.add_node("classify_traffic_node", classify_traffic_node)
    graph.add_node("clarification_check_node", clarification_check_node)
    graph.add_node("retrieve_node", retrieve_node)
    graph.add_node("place_check_node", place_check_node)
    graph.add_node("action_guide_node", action_guide_node)
    graph.add_node("expression_node", expression_node)
    graph.add_node("warning_node", warning_node)
    graph.add_node("final_node", final_node)

    graph.set_entry_point("classify_traffic_node")
    graph.add_edge("classify_traffic_node", "clarification_check_node")
    graph.add_conditional_edges(
        "clarification_check_node",
        route_after_clarification,
        {
            "final_node": "final_node",
            "retrieve_node": "retrieve_node",
        },
    )
    graph.add_edge("retrieve_node", "place_check_node")
    graph.add_conditional_edges(
        "place_check_node",
        route_after_place_check,
        {
            "final_node": "final_node",
            "action_guide_node": "action_guide_node",
        },
    )
    graph.add_edge("action_guide_node", "expression_node")
    graph.add_edge("expression_node", "warning_node")
    graph.add_edge("warning_node", "final_node")
    graph.add_edge("final_node", END)
    return graph.compile()


def build_initial_state(user_input: str) -> TrafficState:
    return TrafficState(
        user_input=user_input,
        category="교통",
        sub_category="",
        needs_clarification=False,
        clarifying_question="",
        retrieved_docs=[],
        sources=[],
        warnings=[],
        action_steps=[],
        checklist=[],
        expressions=[],
        origin="",
        destination="",
        mentioned_places=[],
        route_like=False,
        final_answer="",
    )


def classify_traffic_node(state: TrafficState) -> TrafficState:
    _ = TRAFFIC_CLASSIFICATION_PROMPT
    text = normalize_text(state["user_input"])
    route_like = has_route_like_intent(text)
    mentioned_places = find_supported_places(text)

    if is_generic_card_loss(text):
        sub_category = "애매함"
    elif has_any_keyword(text, LATE_NIGHT_KEYWORDS):
        sub_category = "막차/야간 이동"
    elif has_any_keyword(text, TAXI_KEYWORDS):
        sub_category = "택시 이용"
    elif is_transport_card_question(text):
        sub_category = "교통카드/결제"
    elif mentioned_places and route_like:
        sub_category = "고정 장소 이동"
    elif has_any_keyword(text, TRANSIT_ROUTE_KEYWORDS):
        sub_category = "버스 이용/환승"
    elif mentioned_places:
        sub_category = "고정 장소 이동"
    else:
        sub_category = "애매함"

    return {
        **state,
        "category": "교통",
        "sub_category": sub_category,
        "mentioned_places": mentioned_places,
        "route_like": route_like,
    }


def clarification_check_node(state: TrafficState) -> TrafficState:
    text = normalize_text(state["user_input"])

    if is_generic_card_loss(text):
        return set_clarification(state, TRAFFIC_CARD_LOSS_QUESTION)

    if is_realtime_arrival_request(text):
        return set_clarification(state, TRAFFIC_REALTIME_BUS_RESPONSE)

    if state["sub_category"] == "애매함":
        return set_clarification(state, TRAFFIC_GENERIC_CLARIFICATION_QUESTION)

    if state["sub_category"] == "고정 장소 이동":
        if len(state["mentioned_places"]) == 1:
            return set_clarification(state, TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION)
        if len(state["mentioned_places"]) == 0:
            return set_clarification(state, TRAFFIC_ROUTE_CLARIFICATION_QUESTION)

    if state["sub_category"] == "버스 이용/환승":
        if state["user_input"].strip() in VAGUE_BUS_QUESTIONS:
            return set_clarification(state, TRAFFIC_GENERIC_CLARIFICATION_QUESTION)
        if state["route_like"] and len(state["mentioned_places"]) < 2:
            return set_clarification(state, TRAFFIC_ROUTE_CLARIFICATION_QUESTION)

    return state


def route_after_clarification(state: TrafficState) -> str:
    return "final_node" if state["needs_clarification"] else "retrieve_node"


def retrieve_node(state: TrafficState) -> TrafficState:
    try:
        docs = get_vectorstore().similarity_search(
            state["user_input"],
            k=3,
            filter=TRAFFIC_FILTER,
        )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(GENERATION_ERROR_MESSAGE) from exc

    warnings = list(state["warnings"])
    if not docs:
        warnings.append(NO_DOCS_WARNING)

    sources: list[str] = []
    primary_source = PRIMARY_SOURCE_BY_SUBCATEGORY.get(state["sub_category"])
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


def place_check_node(state: TrafficState) -> TrafficState:
    text = state["user_input"]
    mentioned_places = state["mentioned_places"]
    origin = state["origin"]
    destination = state["destination"]

    if len(mentioned_places) >= 2:
        origin = mentioned_places[0]
        destination = mentioned_places[1]
    elif len(mentioned_places) == 1:
        destination = mentioned_places[0]

    if state["sub_category"] == "고정 장소 이동":
        if not destination:
            return set_clarification(state, TRAFFIC_UNSUPPORTED_PLACE_QUESTION)
        if not origin:
            return set_clarification(state, TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION)

    if state["sub_category"] == "택시 이용" and not destination:
        destination = extract_destination_phrase(text)

    return {
        **state,
        "origin": origin,
        "destination": destination,
    }


def route_after_place_check(state: TrafficState) -> str:
    return "final_node" if state["needs_clarification"] else "action_guide_node"


def action_guide_node(state: TrafficState) -> TrafficState:
    _ = TRAFFIC_ACTION_GUIDE_PROMPT
    sub_category = state["sub_category"]

    action_steps_map = {
        "교통카드/결제": [
            "편의점이나 역 안내 공간에서 교통카드를 구매하거나 충전할 수 있는지 확인하세요.",
            "버스나 지하철을 타기 전에 교통카드 잔액을 먼저 확인하세요.",
            "충전 수단이 현금인지 카드인지 현장에서 다시 확인하세요.",
        ],
        "버스 이용/환승": [
            "타려는 버스 방향과 정류장 이름을 먼저 확인하세요.",
            "버스를 탈 때 카드를 찍고, 내릴 때도 다시 찍는지 기억하세요.",
            "환승이 필요하면 정류장 안내기나 지도 앱에서 어느 정류장에서 내려야 하는지 확인하세요.",
        ],
        "택시 이용": [
            "목적지 이름을 짧고 분명하게 말할 수 있게 준비하세요.",
            "출발 전에 카드 결제가 가능한지 먼저 물어보세요.",
            "도착할 때 원하는 위치에서 내려달라고 짧게 말하세요.",
        ],
        "고정 장소 이동": [
            f"출발지 {state['origin']}와 목적지 {state['destination']}를 다시 확인하세요.",
            "실시간 노선과 도착 시간은 지도 앱이나 정류장 안내기에서 확인하세요.",
            "버스, 지하철, 택시 중 현재 가장 쉬운 이동 수단을 선택하세요.",
        ],
        "막차/야간 이동": [
            "막차 시간은 지도 앱, 역 안내판, 정류장 안내기에서 먼저 확인하세요.",
            "밤늦은 시간에는 밝고 사람이 있는 장소에서 기다리세요.",
            "막차를 놓쳤다면 택시나 다른 이동수단이 가능한지 확인하세요.",
        ],
    }

    checklist_map = {
        "교통카드/결제": [
            "교통카드 종류",
            "충전 가능 장소",
            "교통카드 잔액",
            "충전할 결제 수단",
        ],
        "버스 이용/환승": [
            "출발지",
            "목적지",
            "교통카드 잔액",
            "버스 운행 여부",
            "하차 태그 필요 여부",
        ],
        "택시 이용": [
            "목적지 이름",
            "한국어 장소명",
            "카드 결제 가능 여부",
            "내릴 위치",
            "영수증 필요 여부",
        ],
        "고정 장소 이동": [
            "출발지",
            "목적지",
            "교통카드 잔액",
            "버스/지하철 운행 여부",
            "막차 시간",
        ],
        "막차/야간 이동": [
            "현재 위치",
            "목적지",
            "막차 시간",
            "대체 이동수단",
            "안전한 대기 장소",
        ],
    }

    return {
        **state,
        "action_steps": action_steps_map.get(sub_category, ["공식 안내를 먼저 확인하세요."]),
        "checklist": checklist_map.get(sub_category, ["출발지", "목적지", "교통카드 잔액"]),
    }


def expression_node(state: TrafficState) -> TrafficState:
    _ = TRAFFIC_EXPRESSION_PROMPT
    destination = state["destination"] or "목적지"
    taxi_destination = format_taxi_destination(destination)
    bus_destination = destination if destination else "목적지"

    expression_map = {
        "교통카드/결제": [
            "교통카드 하나 주세요.",
            "교통카드 충전하고 싶어요.",
            "잔액 확인해 주세요.",
        ],
        "버스 이용/환승": [
            f"이 버스가 {bus_destination}에 가나요?",
            "여기서 내려야 하나요?",
            "환승하려면 어디로 가야 해요?",
        ],
        "택시 이용": [
            taxi_destination,
            "카드 결제 가능해요?",
            "여기서 내려주세요.",
        ],
        "고정 장소 이동": [
            f"{state['origin']}에서 {state['destination']}에 가고 싶어요.",
            f"이 버스가 {state['destination']}에 가나요?",
            "어디에서 타야 해요?",
        ],
        "막차/야간 이동": [
            "막차가 끝났나요?",
            "택시를 어디서 탈 수 있어요?",
            "안전하게 기다릴 수 있는 곳이 어디예요?",
        ],
    }

    return {
        **state,
        "expressions": expression_map.get(state["sub_category"], ["교통 이용 방법을 안내해 주세요."]),
    }


def warning_node(state: TrafficState) -> TrafficState:
    _ = TRAFFIC_WARNING_PROMPT
    warnings = list(TRAFFIC_WARNING_BULLETS)

    for warning in state["warnings"]:
        if warning not in warnings:
            warnings.append(warning)

    return {
        **state,
        "warnings": warnings,
    }


def final_node(state: TrafficState) -> TrafficState:
    if state["needs_clarification"]:
        return {
            **state,
            "final_answer": state["clarifying_question"],
        }

    place_section = ""
    if state["sub_category"] == "고정 장소 이동" and state["origin"] and state["destination"]:
        place_section = (
            TRAFFIC_FIXED_PLACE_SECTION_TEMPLATE.format(
                origin=state["origin"],
                destination=state["destination"],
            )
            + "\n\n"
        )

    final_answer = TRAFFIC_FINAL_TEMPLATE.format(
        sub_category=state["sub_category"],
        action_steps=format_numbered(state["action_steps"]),
        checklist=format_checkboxes(state["checklist"]),
        expressions=format_expression_bullets(state["expressions"]),
        place_section=place_section,
        warnings=format_bullets(state["warnings"]),
        sources=format_sources(state["sources"]),
    ).strip()

    return {
        **state,
        "final_answer": final_answer,
    }


def normalize_text(text: str) -> str:
    return text.strip().lower()


def has_any_keyword(text: str, keywords: list[str] | tuple[str, ...]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def is_generic_card_loss(text: str) -> bool:
    return (
        has_any_keyword(text, GENERIC_CARD_KEYWORDS)
        and has_any_keyword(text, CARD_LOSS_KEYWORDS)
        and not has_any_keyword(text, TRANSPORT_CARD_KEYWORDS)
    )


def is_transport_card_question(text: str) -> bool:
    return has_any_keyword(text, TRANSPORT_CARD_KEYWORDS) or (
        has_any_keyword(text, CARD_PAYMENT_KEYWORDS)
        and has_any_keyword(text, TRANSIT_PAYMENT_CONTEXT)
    )


def has_route_like_intent(text: str) -> bool:
    return has_any_keyword(text, ROUTE_INTENT_KEYWORDS)


def is_realtime_arrival_request(text: str) -> bool:
    return (
        has_any_keyword(text, REALTIME_KEYWORDS)
        and has_any_keyword(text, TRANSIT_ROUTE_KEYWORDS)
    )


@lru_cache(maxsize=1)
def load_fixed_places() -> list[dict[str, object]]:
    payload = json.loads(PLACES_PATH.read_text(encoding="utf-8"))
    return payload.get("places", [])


def has_supported_place_alias(text: str) -> bool:
    return len(find_supported_places(text)) > 0


def find_supported_places(text: str) -> list[str]:
    normalized_text = normalize_text(text)
    mentions: list[tuple[int, str]] = []

    for place in load_fixed_places():
        place_name = str(place["name"])
        best_index = None
        for alias in place.get("aliases", []):
            index = normalized_text.find(str(alias).lower())
            if index != -1 and (best_index is None or index < best_index):
                best_index = index
        if best_index is not None:
            mentions.append((best_index, place_name))

    mentions.sort(key=lambda item: item[0])
    return [name for _, name in mentions]


def extract_destination_phrase(user_input: str) -> str:
    normalized = user_input.strip()
    normalized = re.sub(r"^택시 기사님에게\s*", "", normalized)
    normalized = re.sub(r"^기사님에게\s*", "", normalized)

    patterns = [
        r"(?P<destination>.+?)(?:으로|로)\s*가달라고",
        r"(?P<destination>.+?)(?:으로|로)\s*가고 싶",
        r"(?P<destination>.+?)(?:에|으로|로)\s*택시",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if not match:
            continue
        destination = match.group("destination").strip(" .!?\"'")
        destination = destination.replace("버스로", "").replace("지하철로", "").replace("전철로", "").strip()
        if destination:
            return destination
    return ""


def format_taxi_destination(destination: str) -> str:
    if destination == "한양대 ERICA":
        return "한양대 ERICA 정문으로 가주세요."
    if destination:
        if destination.endswith("역"):
            return f"{destination}으로 가주세요."
        return f"{destination}로 가주세요."
    return "목적지로 가주세요."


def set_clarification(state: TrafficState, question: str) -> TrafficState:
    return {
        **state,
        "needs_clarification": True,
        "clarifying_question": question,
    }


def format_numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def format_checkboxes(items: list[str]) -> str:
    return "\n".join(f"□ {item}" for item in items)


def format_expression_bullets(items: list[str]) -> str:
    return "\n".join(f"- “{item}”" for item in items)


def format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def format_sources(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)
