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

INTENT_BUS_ROUTE_CHECK = "bus_route_check"
INTENT_BUS_TAP_OFF_TRANSFER = "bus_tap_off_transfer"
INTENT_TRANSPORT_CARD_CHARGE = "transport_card_charge"
INTENT_TRANSPORT_CARD_USAGE = "transport_card_usage"
INTENT_TAXI_EXPRESSION = "taxi_expression"
INTENT_FIXED_PLACE_ROUTE = "fixed_place_route"
INTENT_LATE_NIGHT = "late_night_transport"

SUB_BUS_ROUTE_CHECK = "버스 경로 확인"
SUB_BUS_TAP_OFF_TRANSFER = "하차 태그·환승"
SUB_TRANSPORT_CARD_CHARGE = "교통카드 충전"
SUB_TRANSPORT_CARD_USAGE = "교통카드 사용"
SUB_TAXI_EXPRESSION = "택시 표현"
SUB_FIXED_PLACE = "고정 장소 이동"
SUB_LATE_NIGHT = "막차/야간 이동"
SUB_AMBIGUOUS = "애매함"

# Backward-compatible aliases used by categories.traffic and older imports.
SUB_BUS = SUB_BUS_ROUTE_CHECK
SUB_TAXI = SUB_TAXI_EXPRESSION
SUB_TRANSPORT_CARD = SUB_TRANSPORT_CARD_CHARGE

INTENT_BY_SUBCATEGORY = {
    SUB_BUS_ROUTE_CHECK: INTENT_BUS_ROUTE_CHECK,
    SUB_BUS_TAP_OFF_TRANSFER: INTENT_BUS_TAP_OFF_TRANSFER,
    SUB_TRANSPORT_CARD_CHARGE: INTENT_TRANSPORT_CARD_CHARGE,
    SUB_TRANSPORT_CARD_USAGE: INTENT_TRANSPORT_CARD_USAGE,
    SUB_TAXI_EXPRESSION: INTENT_TAXI_EXPRESSION,
    SUB_FIXED_PLACE: INTENT_FIXED_PLACE_ROUTE,
    SUB_LATE_NIGHT: INTENT_LATE_NIGHT,
}

PRIMARY_SOURCE_BY_SUBCATEGORY = {
    SUB_BUS_ROUTE_CHECK: "traffic/bus_transfer.md",
    SUB_BUS_TAP_OFF_TRANSFER: "traffic/traffic_tap_off_transfer.md",
    SUB_TRANSPORT_CARD_CHARGE: "traffic/transport_card.md",
    SUB_TRANSPORT_CARD_USAGE: "traffic/transport_card.md",
    SUB_TAXI_EXPRESSION: "traffic/taxi_usage.md",
    SUB_FIXED_PLACE: "traffic/ansan_fixed_places_guide.md",
    SUB_LATE_NIGHT: "traffic/late_night_transport.md",
}

NO_DOCS_WARNING = (
    "관련 교통 문서를 충분히 찾지 못했습니다. 현장 안내나 공식 안내를 함께 확인해주세요."
)
GENERATION_ERROR_MESSAGE = (
    "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
)

TRANSPORT_CARD_KEYWORDS = (
    "교통카드", "버스카드", "티머니", "캐시비", "t-money",
    "transportation card",
)
CARD_CHARGE_KEYWORDS = ("충전", "잔액", "구매", "사다", "어디서 충전")
CARD_USAGE_KEYWORDS = (
    "어디에 찍", "어디 찍", "찍는", "찍어요", "찍나요", "찍었는데",
    "태그", "단말기", "안 돼", "안되", "인식", "잔액 부족",
)
BUS_KEYWORDS = ("버스", "bus", "정류장", "노선")
SUBWAY_KEYWORDS = ("지하철", "전철", "subway", "metro")
TAXI_KEYWORDS = ("택시", "taxi", "카카오택시")
LATE_NIGHT_KEYWORDS = (
    "막차", "첫차", "야간버스", "심야버스", "늦은 시간 버스",
    "늦은 시간 택시", "late night bus",
)
REALTIME_KEYWORDS = (
    "실시간", "몇 분 뒤", "언제 와", "도착 시간", "몇시에", "arrive", "arrival",
)
ROUTE_INTENT_KEYWORDS = (
    "어떻게 가", "가는 법", "가려면", "길찾기", "길 찾기", "이동",
    "가고 싶", "버스로", "지하철로", "전철로", "택시 타고", "타고 가",
    "how to get", "go to",
)
BUS_ROUTE_CHECK_KEYWORDS = (
    "가나요", "가요", "정류장", "노선", "어디에서 내려", "몇 번 버스",
    "몇번 버스", "타면", "타고",
)
TAP_OFF_CONTEXT_KEYWORDS = (
    "내릴 때", "내리면서", "버스에서 내릴", "버스 내릴", "하차", "하차할 때",
)
TAP_OFF_ACTION_KEYWORDS = (
    "카드", "교통카드", "찍", "태그", "하차 태그", "환승", "안 찍",
)
VAGUE_BUS_QUESTIONS = ("버스 타도 돼요?", "지하철 타도 돼요?", "전철 타도 돼요?")
GENERIC_CARD_KEYWORDS = ("카드", "등록증", "신분증", "card")
CARD_LOSS_KEYWORDS = ("잃어버", "분실", "없어졌", "사라졌", "lost")
GENERAL_DESTINATION_HINTS = (
    "병원", "출입국사무소", "출입국", "은행", "학교", "한양대 erica", "에리카",
)

TRANSIT_PAYMENT_CONTEXT = (
    "교통", "버스", "지하철", "전철", "티머니", "캐시비",
)
TRANSIT_ROUTE_KEYWORDS = BUS_KEYWORDS + SUBWAY_KEYWORDS
TRAFFIC_MODE_KEYWORDS = (
    BUS_KEYWORDS + SUBWAY_KEYWORDS + TAXI_KEYWORDS + LATE_NIGHT_KEYWORDS
)


def normalize_text(text: str) -> str:
    return text.strip().lower()


def has_any_keyword(text: str, keywords: list[str] | tuple[str, ...]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def has_bus_number(text: str) -> bool:
    return bool(re.search(r"\b\d{2,5}\b", text))


def is_generic_card_loss(text: str) -> bool:
    return (
        has_any_keyword(text, GENERIC_CARD_KEYWORDS)
        and has_any_keyword(text, CARD_LOSS_KEYWORDS)
        and not has_any_keyword(text, TRANSPORT_CARD_KEYWORDS)
    )


def is_transport_card_question(text: str) -> bool:
    return has_any_keyword(text, TRANSPORT_CARD_KEYWORDS) or (
        has_any_keyword(text, CARD_USAGE_KEYWORDS + CARD_CHARGE_KEYWORDS)
        and has_any_keyword(text, TRANSIT_PAYMENT_CONTEXT)
    )


def is_transport_card_charge_question(text: str) -> bool:
    return is_transport_card_question(text) and has_any_keyword(text, CARD_CHARGE_KEYWORDS)


def is_transport_card_usage_question(text: str) -> bool:
    return is_transport_card_question(text) and has_any_keyword(text, CARD_USAGE_KEYWORDS)


def is_tap_off_transfer_question(text: str) -> bool:
    return (
        has_any_keyword(text, TAP_OFF_CONTEXT_KEYWORDS)
        and has_any_keyword(text, TAP_OFF_ACTION_KEYWORDS)
    )


def is_bus_route_check_question(text: str) -> bool:
    if not has_any_keyword(text, BUS_KEYWORDS):
        return False
    return (
        has_bus_number(text)
        or has_any_keyword(text, BUS_ROUTE_CHECK_KEYWORDS)
        or has_route_like_intent(text)
    )


def has_route_like_intent(text: str) -> bool:
    return has_any_keyword(text, ROUTE_INTENT_KEYWORDS)


def extract_route_points(user_input: str) -> tuple[str, str]:
    text = user_input.strip()
    patterns = [
        r"(?P<origin>.+?)(?:에서|부터)\s*(?P<destination>.+?)(?:까지)?\s*(?:어떻게\s*가|가는\s*법|가려면|가고\s*싶|이동)",
        r"출발지(?:는|:)?\s*(?P<origin>.+?)\s*(?:목적지(?:는|:)?|도착지(?:는|:)?)\s*(?P<destination>.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        origin = clean_route_point(match.group("origin"))
        destination = clean_route_point(match.group("destination"))
        if origin and destination:
            return origin, destination
    return "", ""


def clean_route_point(value: str) -> str:
    value = value.strip(" .!?\"'")
    value = re.sub(r"(버스|지하철|전철|택시)(?:로|타고)?$", "", value).strip()
    return value.strip(" .!?\"'")


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
    normalized = re.sub(r"^택시\s*기사님에게\s*", "", normalized)
    normalized = re.sub(r"^기사님에게\s*", "", normalized)

    patterns = [
        r"(?P<destination>.+?)(?:으로|로)\s*가달라고",
        r"(?P<destination>.+?)(?:으로|로)\s*가고\s*싶",
        r"(?P<destination>.+?)(?:으로|로)\s*택시",
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
    origin, destination = extract_route_points(user_input)

    if is_generic_card_loss(text):
        return False

    if is_tap_off_transfer_question(text):
        return True

    if is_transport_card_question(text):
        return True

    if has_any_keyword(text, TRAFFIC_MODE_KEYWORDS):
        return True

    if has_supported_place_alias(text) and has_route_like_intent(text):
        return True

    if has_route_like_intent(text) and origin and destination:
        return True

    if has_route_like_intent(text) and has_any_keyword(text, GENERAL_DESTINATION_HINTS):
        return True

    return False


def analyze_traffic_input(user_input: str) -> dict[str, object]:
    text = normalize_text(user_input)
    route_like = has_route_like_intent(text)
    mentioned_places = find_supported_places(text)
    origin, destination = extract_route_points(user_input)

    if is_generic_card_loss(text):
        return clarification_result(
            sub_category=SUB_AMBIGUOUS,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_CARD_LOSS_QUESTION,
        )

    if is_realtime_arrival_request(text):
        return clarification_result(
            sub_category=SUB_BUS_ROUTE_CHECK,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_REALTIME_BUS_RESPONSE,
        )

    if has_any_keyword(text, LATE_NIGHT_KEYWORDS):
        sub_category = SUB_LATE_NIGHT
    elif has_any_keyword(text, TAXI_KEYWORDS):
        sub_category = SUB_TAXI_EXPRESSION
    elif is_tap_off_transfer_question(text):
        sub_category = SUB_BUS_TAP_OFF_TRANSFER
    elif is_transport_card_usage_question(text):
        sub_category = SUB_TRANSPORT_CARD_USAGE
    elif is_transport_card_charge_question(text) or is_transport_card_question(text):
        sub_category = SUB_TRANSPORT_CARD_CHARGE
    elif origin and destination and route_like:
        sub_category = SUB_FIXED_PLACE
    elif mentioned_places and route_like:
        sub_category = SUB_FIXED_PLACE
    elif is_bus_route_check_question(text):
        sub_category = SUB_BUS_ROUTE_CHECK
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

    if sub_category == SUB_FIXED_PLACE and not (origin and destination) and len(mentioned_places) == 1:
        return clarification_result(
            sub_category=sub_category,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION,
        )

    if (
        sub_category == SUB_BUS_ROUTE_CHECK
        and user_input.strip() in VAGUE_BUS_QUESTIONS
    ):
        return clarification_result(
            sub_category=sub_category,
            route_like=route_like,
            mentioned_places=mentioned_places,
            question=TRAFFIC_GENERIC_CLARIFICATION_QUESTION,
        )

    if (
        sub_category == SUB_BUS_ROUTE_CHECK
        and route_like
        and not has_bus_number(text)
        and len(mentioned_places) < 2
    ):
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
        "origin": origin,
        "destination": destination,
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
