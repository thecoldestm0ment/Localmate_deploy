from categories.response_format import (
    format_bullets,
    format_checkboxes,
    format_numbered,
    format_sources,
)
from categories.traffic_rules import (
    PRIMARY_SOURCE_BY_SUBCATEGORY,
    SUB_BUS,
    SUB_FIXED_PLACE,
    SUB_LATE_NIGHT,
    SUB_TAXI,
    SUB_TRANSPORT_CARD,
)
from prompts.traffic_prompts import (
    TRAFFIC_FINAL_TEMPLATE,
    TRAFFIC_FIXED_PLACE_SECTION_TEMPLATE,
    TRAFFIC_WARNING_BULLETS,
)


def get_primary_source(sub_category: str) -> str | None:
    return PRIMARY_SOURCE_BY_SUBCATEGORY.get(sub_category)


def build_action_steps(
    sub_category: str,
    origin: str,
    destination: str,
) -> list[str]:
    action_steps_map = {
        SUB_TRANSPORT_CARD: [
            "편의점이나 역 안내 공간에서 교통카드 구매나 충전이 가능한지 확인해주세요.",
            "버스나 지하철을 타기 전에 교통카드 잔액을 먼저 확인해주세요.",
            "충전 수단이 현금인지 카드인지 현장에서 다시 확인해주세요.",
        ],
        SUB_BUS: [
            "타려는 버스 방향과 정류장 이름을 먼저 확인해주세요.",
            "버스를 탈 때 카드를 찍고, 내릴 때도 다시 찍는지 기억해주세요.",
            "환승이 필요하면 정류장 안내기나 직원에게 어디로 가야 하는지 확인해주세요.",
        ],
        SUB_TAXI: [
            "목적지 이름을 짧고 분명하게 말할 수 있게 준비해주세요.",
            "출발 전에 카드 결제가 가능한지 먼저 물어보세요.",
            "내리고 싶은 위치에 가까워지면 기사님께 미리 말해주세요.",
        ],
        SUB_FIXED_PLACE: [
            f"출발지 {origin}과 목적지 {destination}를 다시 확인해주세요.",
            "실시간 노선과 도착 시간은 지도 앱이나 정류장 안내기에서 확인해주세요.",
            "버스, 지하철, 택시 중 지금 가장 이용하기 쉬운 수단을 선택해주세요.",
        ],
        SUB_LATE_NIGHT: [
            "막차 시간은 지하철역 안내판이나 정류장 안내기에서 먼저 확인해주세요.",
            "밤늦은 시간에는 밝고 사람이 있는 곳에서 기다려주세요.",
            "막차를 놓쳤다면 택시나 다른 이동수단이 가능한지 확인해주세요.",
        ],
    }
    return action_steps_map.get(sub_category, ["공식 안내를 먼저 확인해주세요."])


def build_checklist(sub_category: str) -> list[str]:
    checklist_map = {
        SUB_TRANSPORT_CARD: [
            "교통카드 종류",
            "충전 가능 장소",
            "교통카드 잔액",
            "충전할 결제 수단",
        ],
        SUB_BUS: [
            "출발지",
            "목적지",
            "교통카드 잔액",
            "버스/지하철 운행 여부",
            "하차 태그 필요 여부",
        ],
        SUB_TAXI: [
            "목적지 이름",
            "기사님께 보여줄 장소명",
            "카드 결제 가능 여부",
            "내릴 위치",
            "영수증 필요 여부",
        ],
        SUB_FIXED_PLACE: [
            "출발지",
            "목적지",
            "교통카드 잔액",
            "버스/지하철 운행 여부",
            "막차 시간",
        ],
        SUB_LATE_NIGHT: [
            "현재 위치",
            "목적지",
            "막차 시간",
            "대체 이동수단",
            "안전한 대기 장소",
        ],
    }
    return checklist_map.get(sub_category, ["출발지", "목적지", "교통카드 잔액"])


def build_expressions(
    sub_category: str,
    origin: str,
    destination: str,
) -> list[str]:
    destination_text = destination or "목적지"

    expression_map = {
        SUB_TRANSPORT_CARD: [
            "교통카드 하나 주세요.",
            "교통카드 충전하고 싶어요.",
            "잔액 확인해 주세요.",
        ],
        SUB_BUS: [
            f"이 버스가 {destination_text}에 가나요?",
            "여기서 내려야 하나요?",
            "환승하려면 어디로 가야 해요?",
        ],
        SUB_TAXI: [
            format_taxi_destination(destination_text),
            "카드 결제 가능해요?",
            "여기서 내려주세요.",
        ],
        SUB_FIXED_PLACE: [
            f"{origin}에서 {destination_text} 가고 싶어요.",
            f"이 버스가 {destination_text}에 가나요?",
            "어디에서 타야 해요?",
        ],
        SUB_LATE_NIGHT: [
            "막차가 끝났나요?",
            "택시를 어디서 탈 수 있어요?",
            "안전하게 기다릴 수 있는 곳이 어디예요?",
        ],
    }
    return expression_map.get(sub_category, ["교통 이용 방법을 안내해주세요."])


def build_warnings(extra_warnings: list[str]) -> list[str]:
    warnings = list(TRAFFIC_WARNING_BULLETS)
    for warning in extra_warnings:
        if warning not in warnings:
            warnings.append(warning)
    return warnings


def build_final_answer(
    sub_category: str,
    action_steps: list[str],
    checklist: list[str],
    expressions: list[str],
    warnings: list[str],
    sources: list[str],
    origin: str,
    destination: str,
) -> str:
    place_section = ""
    if sub_category == SUB_FIXED_PLACE and origin and destination:
        place_section = (
            TRAFFIC_FIXED_PLACE_SECTION_TEMPLATE.format(
                origin=origin,
                destination=destination,
            )
            + "\n\n"
        )

    return TRAFFIC_FINAL_TEMPLATE.format(
        sub_category=sub_category,
        action_steps=format_numbered(action_steps),
        checklist=format_checkboxes(checklist),
        expressions=format_bullets(expressions, empty_text="- 확인이 필요한 표현이 있습니다."),
        place_section=place_section,
        warnings=format_bullets(warnings),
        sources=format_sources(sources),
    ).strip()


def format_taxi_destination(destination: str) -> str:
    if destination == "한양대 ERICA":
        return "한양대 ERICA 정문으로 가주세요."
    return f"{destination}{choose_ro_particle(destination)} 가주세요."


def choose_ro_particle(text: str) -> str:
    if not text:
        return "로"

    last_char = text[-1]
    code_point = ord(last_char) - 0xAC00
    if not 0 <= code_point <= 11171:
        return "로"

    jongseong_index = code_point % 28
    if jongseong_index in (0, 8):
        return "로"
    return "으로"
