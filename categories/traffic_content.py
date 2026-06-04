import re

from categories.response_format import format_sources
from categories.traffic_rules import (
    PRIMARY_SOURCE_BY_SUBCATEGORY,
    SUB_BUS,
    SUB_FIXED_PLACE,
    SUB_LATE_NIGHT,
    SUB_TAXI,
    SUB_TRANSPORT_CARD,
)


def get_primary_source(sub_category: str) -> str | None:
    return PRIMARY_SOURCE_BY_SUBCATEGORY.get(sub_category)


def build_action_steps(
    sub_category: str,
    origin: str,
    destination: str,
    user_input: str = "",
) -> list[str]:
    details = build_question_details(user_input, destination)

    action_steps_map = {
        SUB_TRANSPORT_CARD: [
            "편의점이나 역 충전기에서 교통카드 충전이 가능한지 확인합니다.  \n(Check whether you can recharge your transportation card at a convenience store or station machine.)",
            "충전하기 전에 카드 잔액과 충전할 금액을 확인합니다.  \n(Check your card balance and the amount you want to add before recharging.)",
            "충전 후 단말기나 영수증에서 잔액이 바뀌었는지 확인합니다.  \n(After recharging, check the terminal or receipt to confirm the balance changed.)",
        ],
        SUB_BUS: [
            f"지도 앱에서 {details['bus_search_text']} 검색해 버스 방향, 정류장 목록, 도착 시간을 확인합니다.  \n(Search for {details['bus_search_text_en']} in a map app to check the bus direction, stop list, and arrival time.)",
            f"정류장 목록에서 {details['destination_text']} 또는 가까운 정류장이 있는지 확인합니다.  \n(Check the stop list to see whether it stops at or near {details['destination_en']}.)",
            "정류장 안내기에서도 버스 방향과 도착 시간을 확인합니다.  \n(Check the bus direction and arrival time on the bus stop display too.)",
            "타기 전에 기사님에게 한 번 더 물어보면 안전합니다.  \n(Before boarding, it is safer to ask the driver once more.)",
        ],
        SUB_TAXI: [
            f"목적지를 짧고 정확하게 말하거나 기사님에게 보여줍니다.  \n(Say the destination clearly and briefly, or show it to the driver.)",
            "출발 전에 카드 결제가 가능한지 먼저 물어봅니다.  \n(Ask whether card payment is possible before leaving.)",
            "도착지가 가까워지면 내릴 위치를 미리 말합니다.  \n(When you get close to the destination, tell the driver where you want to get off.)",
            "필요하면 영수증을 요청합니다.  \n(Ask for a receipt if you need one.)",
        ],
        SUB_FIXED_PLACE: [
            f"지도 앱에 출발지 {origin}, 목적지 {destination}를 입력합니다.  \n(Enter {origin} as the starting point and {destination} as the destination in a map app.)",
            "버스 번호만 보고 타지 말고 방향과 내릴 정류장을 함께 확인합니다.  \n(Do not board only by bus number; check the direction and the stop where you should get off.)",
            "정류장 안내기나 역 안내판에서 방향을 한 번 더 확인합니다.  \n(Check the direction once more on the bus stop display or station sign.)",
            "한양대 ERICA처럼 목적지와 정류장 이름이 다를 수 있으니 가까운 정류장도 확인합니다.  \n(The stop name may be different from the destination, such as Hanyang University ERICA, so check nearby stop names too.)",
        ],
        SUB_LATE_NIGHT: [
            "지도 앱에서 막차 또는 심야버스 시간을 먼저 확인합니다.  \n(Check the last bus or late-night bus time in a map app first.)",
            "정류장 안내기에서 방향과 도착 시간을 다시 확인합니다.  \n(Check the direction and arrival time again on the bus stop display.)",
            "막차를 놓칠 수 있으면 택시나 다른 이동 방법도 함께 확인합니다.  \n(If you may miss the last bus, also check a taxi or another way to travel.)",
        ],
    }
    return action_steps_map.get(
        sub_category,
        ["지도 앱이나 현장 안내기를 먼저 확인합니다.  \n(Check a map app or an on-site information display first.)"],
    )


def build_checklist(sub_category: str) -> list[str]:
    checklist_map = {
        SUB_TRANSPORT_CARD: ["교통카드", "충전할 금액", "카드 잔액", "결제 수단"],
        SUB_BUS: ["버스 번호", "버스 방향", "내릴 정류장 이름", "교통카드 잔액", "지도 앱의 도착 시간"],
        SUB_TAXI: ["목적지 이름", "기사님에게 보여줄 주소", "카드 결제 가능 여부", "내릴 위치", "영수증 필요 여부"],
        SUB_FIXED_PLACE: ["출발지", "목적지", "버스 방향", "내릴 정류장 이름", "교통카드 잔액"],
        SUB_LATE_NIGHT: ["현재 위치", "목적지", "막차 시간", "버스 방향", "대체 이동 방법"],
    }
    return checklist_map.get(sub_category, ["출발지", "목적지", "교통카드 잔액"])


def build_expressions(
    sub_category: str,
    origin: str,
    destination: str,
    user_input: str = "",
) -> list[str]:
    details = build_question_details(user_input, destination)
    destination_text = details["destination_text"]
    destination_en = details["destination_en"]
    bus_number = details["bus_number"]

    expression_map = {
        SUB_TRANSPORT_CARD: [
            "“교통카드 충전하고 싶어요.”  \n(I would like to recharge my transportation card.)",
            "“잔액 확인해 주세요.”  \n(Please check the balance.)",
            "“여기서 교통카드 충전할 수 있나요?”  \n(Can I recharge my transportation card here?)",
        ],
        SUB_BUS: [
            f"“{bus_number}번 버스가 {destination_text}에 가나요?”  \n(Does bus {bus_number} go to {destination_en}?)"
            if bus_number
            else f"“이 버스가 {destination_text}에 가나요?”  \n(Does this bus go to {destination_en}?)",
            f"“{destination_text}에 가려면 어디에서 내려야 해요?”  \n(Where should I get off to go to {destination_en}?)",
            f"“{destination_text} 근처 정류장에 서나요?”  \n(Does this bus stop near {destination_en}?)",
        ],
        SUB_TAXI: [
            f"“{format_taxi_destination(destination_text)}”  \n(Please take me to {destination_en}.)",
            "“카드 결제 가능해요?”  \n(Can I pay by card?)",
            "“여기서 내려주세요.”  \n(Please let me off here.)",
            "“영수증 주세요.”  \n(Please give me a receipt.)",
        ],
        SUB_FIXED_PLACE: [
            f"“{origin}에서 {destination_text} 가고 싶어요.”  \n(I want to go from {origin} to {destination_en}.)",
            f"“{destination_text}에 가려면 어디에서 내려야 해요?”  \n(Where should I get off to go to {destination_en}?)",
            "“이 방향이 맞나요?”  \n(Is this the right direction?)",
        ],
        SUB_LATE_NIGHT: [
            "“막차가 아직 있나요?”  \n(Is there still a last bus?)",
            "“이 버스가 지금도 운행하나요?”  \n(Is this bus still running now?)",
            "“택시는 어디에서 탈 수 있어요?”  \n(Where can I take a taxi?)",
        ],
    }
    return expression_map.get(
        sub_category,
        ["“교통 이용 방법을 안내해 주세요.”  \n(Please tell me how to use transportation.)"],
    )


def build_warnings(extra_warnings: list[str]) -> list[str]:
    warnings = [
        "같은 번호의 버스라도 방향이 반대일 수 있으니 타기 전에 방향을 확인하세요.  \n(Even if the bus number is the same, it may go in the opposite direction, so check the direction before boarding.)",
        "정류장 이름이 목적지와 정확히 같지 않을 수 있으니 가까운 정류장 이름도 함께 확인하세요.  \n(The stop name may not be exactly the same as your destination, so check nearby stop names too.)",
        "막차 시간과 요금은 지역과 날짜에 따라 달라질 수 있으니 지도 앱이나 현장 안내기를 함께 확인하세요.  \n(Last bus times and fares can vary by area and date, so check a map app or on-site display too.)",
    ]
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
    user_input: str = "",
) -> str:
    intro = build_intro(sub_category, user_input, origin, destination)
    expression_heading = build_expression_heading(sub_category)
    expression_intro = build_expression_intro(sub_category)

    sections = [
        intro,
        "## 바로 확인하는 방법",
        format_numbered(action_steps),
        "## 이동 전 확인할 것",
        format_checkboxes(checklist),
        f"## {expression_heading}",
        expression_intro,
        format_bullets(expressions),
        "## 주의사항",
        format_bullets(warnings),
        "## 참고 문서",
        format_sources(sources),
    ]
    return "\n\n".join(section for section in sections if section).strip()


def build_intro(sub_category: str, user_input: str, origin: str, destination: str) -> str:
    details = build_question_details(user_input, destination)

    if sub_category == SUB_BUS:
        return (
            f"{details['destination_text']}에 가는 버스인지 헷갈릴 때는 지도 앱에서 먼저 확인하고, 타기 전에 기사님에게 한 번 더 물어보면 안전해요.\n"
            f"(When you are not sure if a bus goes to {details['destination_en']}, check it in a map app first and ask the driver before boarding.)"
        )
    if sub_category == SUB_TRANSPORT_CARD:
        return (
            "교통카드는 편의점이나 역 충전기에서 충전 가능 여부를 먼저 확인하면 좋아요.\n"
            "(For a transportation card, first check whether recharging is available at a convenience store or station machine.)"
        )
    if sub_category == SUB_TAXI:
        return (
            "택시를 탈 때는 목적지를 짧게 말하고, 결제 방법과 내릴 위치를 미리 확인하면 좋아요.\n"
            "(When taking a taxi, say the destination briefly and check the payment method and drop-off point in advance.)"
        )
    if sub_category == SUB_FIXED_PLACE:
        return (
            f"{origin}에서 {destination}까지는 지도 앱에 출발지와 목적지를 넣고 방향과 내릴 정류장을 함께 확인하세요.\n"
            f"(From {origin} to {destination}, enter the starting point and destination in a map app and check both the direction and the stop where you should get off.)"
        )
    if sub_category == SUB_LATE_NIGHT:
        return (
            "늦은 시간에는 지도 앱과 정류장 안내기에서 막차 시간과 방향을 먼저 확인하면 안전해요.\n"
            "(Late at night, it is safer to check the last bus time and direction in a map app and on the bus stop display first.)"
        )
    return (
        "교통 이용이 헷갈릴 때는 지도 앱과 현장 안내를 함께 확인하면 안전해요.\n"
        "(When transportation is confusing, it is safer to check both a map app and on-site information.)"
    )


def build_expression_heading(sub_category: str) -> str:
    if sub_category == SUB_TAXI:
        return "택시 기사님에게 말하거나 보여줄 문장"
    if sub_category == SUB_TRANSPORT_CARD:
        return "편의점 직원이나 역 직원에게 말하거나 보여줄 문장"
    return "기사님이나 주변 사람에게 말하거나 보여줄 문장"


def build_expression_intro(sub_category: str) -> str:
    if sub_category == SUB_TAXI:
        return (
            "아래 문장은 택시 기사님에게 직접 말하거나 보여주면 됩니다.\n"
            "(You can say or show the sentences below directly to the taxi driver.)"
        )
    if sub_category == SUB_TRANSPORT_CARD:
        return (
            "아래 문장은 편의점 직원이나 역 직원에게 직접 말하거나 보여주면 됩니다.\n"
            "(You can say or show the sentences below directly to convenience store or station staff.)"
        )
    return (
        "아래 문장은 현장에서 직원, 기사님, 주변 사람에게 직접 말하거나 보여주면 됩니다.\n"
        "(You can say or show the sentences below directly to staff, drivers, or people nearby.)"
    )


def build_question_details(user_input: str, destination: str) -> dict[str, str]:
    bus_number = extract_bus_number(user_input)
    destination_text = destination or extract_destination_from_question(user_input) or "목적지"
    destination_en = translate_destination(destination_text)
    bus_search_text = f"{bus_number} 또는 {bus_number} 버스" if bus_number else "버스 번호나 목적지"
    bus_search_text_en = f"{bus_number} or bus {bus_number}" if bus_number else "the bus number or destination"
    return {
        "bus_number": bus_number,
        "destination_text": destination_text,
        "destination_en": destination_en,
        "bus_search_text": bus_search_text,
        "bus_search_text_en": bus_search_text_en,
    }


def extract_bus_number(text: str) -> str:
    match = re.search(r"\b(\d{2,5})\b", text)
    return match.group(1) if match else ""


def extract_destination_from_question(text: str) -> str:
    patterns = [
        r"에게\s*(?P<destination>.+?)(?:에|으로|로)\s*가달",
        r"버스가\s*(?P<destination>.+?)(?:에|으로|로)\s*가",
        r"(?P<destination>.+?)(?:에|으로|로)\s*가나요",
        r"(?P<destination>.+?)(?:에|으로|로)\s*가요",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            destination = match.group("destination").strip()
            destination = re.sub(r"^\d+\s*번?\s*버스가\s*", "", destination).strip()
            if destination:
                return destination
    return ""


def translate_destination(destination: str) -> str:
    translations = {
        "한양대 ERICA": "Hanyang University ERICA",
        "한양대 에리카": "Hanyang University ERICA",
        "중앙역": "Jungang Station",
        "한대앞역": "Hanyang University at Ansan Station",
        "목적지": "your destination",
    }
    return translations.get(destination, destination)


def format_numbered(items: list[str]) -> str:
    if not items:
        return "1. 지도 앱에서 먼저 확인합니다.  \n   (Check in a map app first.)"
    return "\n\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def format_checkboxes(items: list[str]) -> str:
    if not items:
        return "□ 지도 앱 확인"
    return "  \n".join(f"□ {item}" for item in items)


def format_bullets(items: list[str]) -> str:
    if not items:
        return "- 현장에서 다시 확인해 주세요.  \n  (Please check again on site.)"
    return "\n\n".join(f"- {item}" for item in items)


def format_taxi_destination(destination: str) -> str:
    if destination in ("한양대 ERICA", "한양대 에리카"):
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
