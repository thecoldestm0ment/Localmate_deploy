import json
import re
from functools import lru_cache
from pathlib import Path
from prompts.traffic_prompts import (
    TRAFFIC_CARD_LOSS_QUESTION,
    TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION,
    TRAFFIC_GENERIC_CLARIFICATION_QUESTION,
    TRAFFIC_REALTIME_BUS_RESPONSE,
    TRAFFIC_ROUTE_CLARIFICATION_QUESTION,
)

CATEGORY_NAME = "traffic"
ROUTE_PRIORITY = 30
DISPLAY_CATEGORY = "교통"
TRAFFIC_FILTER = {"category": "traffic"}
PLACES_PATH = (
    Path(__file__).resolve().parent.parent
    / "data/places/ansan_fixed_places.json"
)

SUB_TRANSPORT_CARD = "교통카드/결제"
SUB_BUS = "버스 이용/환승"
SUB_TAXI = "택시 이용"
SUB_FIXED_PLACE = "고정 장소 이동"
SUB_LATE_NIGHT = "막차/야간 이동"
SUB_AMBIGUOUS = "애매함"

NO_DOCS_WARNING = (
    "관련 교통 문서를 충분히 찾지 못했습니다. 공식 안내를 추가로 확인해주세요."
)
GENERATION_ERROR_MESSAGE = (
    "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
)

PRIMARY_SOURCE_BY_SUBCATEGORY = {
    SUB_TRANSPORT_CARD: "traffic/transport_card.md",
    SUB_BUS: "traffic/bus_transfer.md",
    SUB_TAXI: "traffic/taxi_usage.md",
    SUB_FIXED_PLACE: "traffic/ansan_fixed_places_guide.md",
    SUB_LATE_NIGHT: "traffic/late_night_transport.md",
}

TRANSPORT_CARD_KEYWORDS = (
    "교통카드",
    "버스카드",
    "티머니",
    "캐시비",
    "t-money",
    "transportation card",
)
CARD_PAYMENT_KEYWORDS = ("충전", "잔액", "결제", "사용법")
BUS_KEYWORDS = ("버스", "bus", "환승", "하차", "정류장")
SUBWAY_KEYWORDS = ("지하철", "전철", "subway", "metro")
TAXI_KEYWORDS = ("택시", "taxi", "카카오택시")
LATE_NIGHT_KEYWORDS = ("막차", "첫차", "야간", "밤늦", "심야", "late night")
REALTIME_KEYWORDS = (
    "실시간",
    "몇 분 뒤",
    "언제 와",
    "도착 시간",
    "몇 시",
    "arrive",
    "arrival",
)
ROUTE_INTENT_KEYWORDS = (
    "어떻게 가",
    "가는 법",
    "가려면",
    "길찾기",
    "길 찾기",
    "이동",
    "가고 싶",
    "버스로",
    "지하철로",
    "전철로",
    "택시 타고",
    "타고 가",
    "how to get",
    "go to",
)
VAGUE_BUS_QUESTIONS = (
    "버스 타도 돼요?",
    "지하철 타도 돼요?",
    "전철 타도 돼요?",
)
GENERIC_CARD_KEYWORDS = ("카드", "등록증", "신분증", "card")
CARD_LOSS_KEYWORDS = ("잃어버", "분실", "없어졌", "사라졌", "lost")
GENERAL_DESTINATION_HINTS = (
    "병원",
    "출입국사무소",
    "출입국",
    "은행",
    "학교",
    "한양대 erica",
    "에리카",
)
TRANSIT_PAYMENT_CONTEXT = ("교통", "버스", "지하철", "티머니", "캐시비")
TRANSIT_ROUTE_KEYWORDS = BUS_KEYWORDS + SUBWAY_KEYWORDS
TRAFFIC_MODE_KEYWORDS = (
    BUS_KEYWORDS + SUBWAY_KEYWORDS + TAXI_KEYWORDS + LATE_NIGHT_KEYWORDS
)


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


def has_supported_place_alias(text: str) -> bool:
    return bool(find_supported_places(text))


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
        destination = (
            destination
            .replace("버스로", "")
            .replace("지하철로", "")
            .replace("전철로", "")
            .strip()
        )
        if destination:
            return destination
    return ""


def can_handle_traffic(user_input: str) -> bool:
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


def analyze_traffic_input(user_input: str) -> dict[str, object]:
    text = normalize_text(user_input)
    route_like = has_route_like_intent(text)
    mentioned_places = find_supported_places(text)

    if is_generic_card_loss(text):
        return clarification_result(
            sub_category=SUB_AMBIGUOUS,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_CARD_LOSS_QUESTION,
        )

    if is_realtime_arrival_request(text):
        return clarification_result(
            sub_category=SUB_BUS,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_REALTIME_BUS_RESPONSE,
        )

    if has_any_keyword(text, LATE_NIGHT_KEYWORDS):
        sub_category = SUB_LATE_NIGHT
    elif has_any_keyword(text, TAXI_KEYWORDS):
        sub_category = SUB_TAXI
    elif is_transport_card_question(text):
        sub_category = SUB_TRANSPORT_CARD
    elif mentioned_places and route_like:
        sub_category = SUB_FIXED_PLACE
    elif has_any_keyword(text, TRANSIT_ROUTE_KEYWORDS):
        sub_category = SUB_BUS
    elif mentioned_places:
        sub_category = SUB_FIXED_PLACE
    else:
        sub_category = SUB_AMBIGUOUS

    if sub_category == SUB_AMBIGUOUS:
        return clarification_result(
            sub_category=sub_category,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_GENERIC_CLARIFICATION_QUESTION,
        )

    if sub_category == SUB_FIXED_PLACE and len(mentioned_places) == 0:
        return clarification_result(
            sub_category=sub_category,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_ROUTE_CLARIFICATION_QUESTION,
        )

    if sub_category == SUB_FIXED_PLACE and len(mentioned_places) == 1:
        return clarification_result(
            sub_category=sub_category,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION,
        )

    if (
        sub_category == SUB_BUS
        and user_input.strip() in VAGUE_BUS_QUESTIONS
    ):
        return clarification_result(
            sub_category=sub_category,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_GENERIC_CLARIFICATION_QUESTION,
        )

    if sub_category == SUB_BUS and route_like and len(mentioned_places) < 2:
        return clarification_result(
            sub_category=sub_category,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_ROUTE_CLARIFICATION_QUESTION,
        )

    return {
        "category": DISPLAY_CATEGORY,
        "sub_category": sub_category,
        "needs_clarification": False,
        "clarifying_question": "",
        "mentioned_places": mentioned_places,
        "route_like": route_like,
    }


def clarification_result(
    sub_category: str,
    route_like: bool,
    mentioned_places: list[str],
    question: str,
) -> dict[str, object]:
    return {
        "category": DISPLAY_CATEGORY,
        "sub_category": sub_category,
        "needs_clarification": True,
        "clarifying_question": question,
        "mentioned_places": mentioned_places,
        "route_like": route_like,
    }
