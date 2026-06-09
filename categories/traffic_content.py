import re

from categories.traffic_rules import (
    PRIMARY_SOURCE_BY_SUBCATEGORY,
    SUB_BUS_ROUTE_CHECK,
    SUB_BUS_TAP_OFF_TRANSFER,
    SUB_FIXED_PLACE,
    SUB_LATE_NIGHT,
    SUB_TAXI_EXPRESSION,
    SUB_TRANSPORT_CARD_CHARGE,
    SUB_TRANSPORT_CARD_USAGE,
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
    destination_with_particle = f"{destination}{choose_ro_particle(destination)}"

    fixed_place_steps = [
        f"지도 앱에 출발지 `{origin}`, 목적지 `{destination_with_particle}` 입력합니다.  \n(Enter {origin} as the starting point and {destination} as the destination in a map app.)",
        "추천 경로에서 버스, 지하철, 도보 중 지금 이용하기 쉬운 방법을 고릅니다.  \n(Choose the easiest option among bus, subway, and walking routes.)",
        "방향과 내릴 정류장 이름을 한 번 더 확인합니다.  \n(Check the direction and the stop where you should get off.)",
        "정류장 안내기나 역 안내판에서 운행 여부를 다시 확인합니다.  \n(Check the stop display or station sign again.)",
    ]
    fixed_place_steps.extend(build_supported_route_tips(origin, destination))

    action_steps_map = {
        SUB_BUS_ROUTE_CHECK: [
            f"지도 앱에서 `{details['bus_search_text']}`를 검색합니다.  \n(Search for {details['bus_search_text_en']} in a map app.)",
            "버스 방향이 목적지 쪽인지 확인합니다.  \n(Check whether the bus direction is toward your destination.)",
            f"정류장 목록에서 `{details['destination_text']}` 또는 가까운 정류장이 있는지 확인합니다.  \n(Check whether the stop list includes {details['destination_en']} or a nearby stop.)",
            "타기 전에 정류장 안내기나 기사님에게 한 번 더 확인합니다.  \n(Check once more on the stop display or with the driver before boarding.)",
        ],
        SUB_BUS_TAP_OFF_TRANSFER: [
            "버스에서 내릴 때 카드 단말기에 교통카드를 한 번 더 태그합니다.  \n(Tap your transportation card again on the card reader when getting off the bus.)",
            "다른 버스나 지하철로 갈아탈 예정이면 하차 태그가 되었는지 확인합니다.  \n(If you plan to transfer, check that your tap-off was processed.)",
            "단말기 소리나 화면으로 태그가 처리되었는지 확인합니다.  \n(Check the sound or screen on the card reader.)",
        ],
        SUB_TRANSPORT_CARD_CHARGE: [
            "편의점이나 역 충전기에서 교통카드 충전이 가능한지 확인합니다.  \n(Check whether you can recharge your card at a convenience store or station machine.)",
            "충전하기 전에 카드 잔액과 충전할 금액을 확인합니다.  \n(Check your card balance and the amount you want to add.)",
            "충전 후 단말기나 영수증에서 잔액이 바뀌었는지 확인합니다.  \n(After recharging, check the terminal or receipt.)",
        ],
        SUB_TRANSPORT_CARD_USAGE: [
            "버스 앞문 근처 카드 단말기에 교통카드를 가볍게 댑니다.  \n(Tap your card on the reader near the bus entrance.)",
            "소리나 화면으로 카드가 인식되었는지 확인합니다.  \n(Check the sound or screen to confirm it worked.)",
            "잔액 부족이나 인식 오류가 나오면 기사님에게 말하고, 필요하면 충전 가능한 곳을 확인합니다.  \n(If the balance is low or the card is not recognized, ask the driver and check where to recharge.)",
        ],
        SUB_TAXI_EXPRESSION: [
            "목적지를 짧고 정확하게 말하거나 기사님에게 보여줍니다.  \n(Say or show the destination clearly.)",
            "출발 전에 카드 결제가 가능한지 물어봅니다.  \n(Ask whether card payment is possible before leaving.)",
            "목적지 근처에 도착하면 내릴 위치를 미리 말합니다.  \n(Tell the driver where you want to get off when you are close.)",
        ],
        SUB_FIXED_PLACE: fixed_place_steps,
        SUB_LATE_NIGHT: [
            "지도 앱에서 막차나 심야 이동 가능 여부를 먼저 확인합니다.  \n(Check late-night transportation options in a map app first.)",
            "정류장 안내기나 역 안내판에서 운행 여부를 다시 확인합니다.  \n(Check the stop display or station sign again.)",
            "막차를 놓쳤다면 밝고 안전한 장소에서 택시나 다른 이동수단을 확인합니다.  \n(If you missed the last service, check taxi or other options in a safe, well-lit place.)",
        ],
    }
    return action_steps_map.get(
        sub_category,
        ["지도 앱이나 현장 안내기를 먼저 확인합니다.  \n(Check a map app or on-site information first.)"],
    )


def build_checklist(sub_category: str) -> list[str]:
    checklist_map = {
        SUB_BUS_ROUTE_CHECK: ["버스 번호", "버스 방향", "정류장 목록", "내릴 정류장 이름"],
        SUB_BUS_TAP_OFF_TRANSFER: ["교통카드", "하차 단말기 위치", "환승할 교통수단 정보", "단말기 처리 화면"],
        SUB_TRANSPORT_CARD_CHARGE: ["교통카드", "충전할 금액", "카드 잔액", "결제 수단"],
        SUB_TRANSPORT_CARD_USAGE: ["교통카드", "카드 단말기 위치", "카드 인식 소리/화면", "잔액"],
        SUB_TAXI_EXPRESSION: ["목적지 이름", "기사님에게 보여줄 주소", "카드 결제 가능 여부", "내릴 위치"],
        SUB_FIXED_PLACE: ["출발지", "목적지", "추천 경로", "방향", "내릴 정류장 이름", "교통카드 잔액"],
        SUB_LATE_NIGHT: ["현재 위치", "목적지", "막차 시간", "대체 이동수단", "안전하게 기다릴 장소"],
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
        SUB_BUS_ROUTE_CHECK: [
            (
                f"“{bus_number}번 버스가 {destination_text}에 가나요?”  \n"
                f"(Does bus {bus_number} go to {destination_en}?)"
            ) if bus_number else (
                f"“이 버스가 {destination_text}에 가나요?”  \n"
                f"(Does this bus go to {destination_en}?)"
            ),
            f"“{destination_text}에 가려면 어디에서 내려야 해요?”  \n(Where should I get off to go to {destination_en}?)",
            "“이 방향이 맞나요?”  \n(Is this the right direction?)",
        ],
        SUB_BUS_TAP_OFF_TRANSFER: [
            "“내릴 때도 교통카드를 찍어야 하나요?”  \n(Do I need to tap my transportation card when getting off?)",
            "“환승하려면 하차 태그가 필요한가요?”  \n(Do I need to tap off to transfer?)",
            "“카드가 제대로 찍혔나요?”  \n(Was my card tapped correctly?)",
        ],
        SUB_TRANSPORT_CARD_CHARGE: [
            "“교통카드 충전하고 싶어요.”  \n(I would like to recharge my transportation card.)",
            "“잔액 확인해 주세요.”  \n(Please check the balance.)",
            "“여기서 교통카드 충전할 수 있나요?”  \n(Can I recharge my transportation card here?)",
        ],
        SUB_TRANSPORT_CARD_USAGE: [
            "“교통카드는 어디에 찍어요?”  \n(Where should I tap my transportation card?)",
            "“카드가 인식됐나요?”  \n(Was my card recognized?)",
            "“잔액이 부족하면 어디서 충전해요?”  \n(Where can I recharge it if the balance is low?)",
        ],
        SUB_TAXI_EXPRESSION: [
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
            "“막차가 아직 있나요?”  \n(Is there still a last bus or train?)",
            "“택시는 어디에서 탈 수 있어요?”  \n(Where can I take a taxi?)",
            "“안전하게 기다릴 수 있는 곳이 어디예요?”  \n(Where can I wait safely?)",
        ],
    }
    return expression_map.get(
        sub_category,
        ["“교통 이용 방법을 안내해 주세요.”  \n(Please tell me how to use transportation.)"],
    )


def build_warnings(extra_warnings: list[str], sub_category: str = "") -> list[str]:
    warning_map = {
        SUB_BUS_ROUTE_CHECK: [
            "같은 번호의 버스라도 방향이 다를 수 있으니 타기 전에 방향을 확인하세요.  \n(Even buses with the same number may go in different directions.)",
            "실시간 도착 시간은 지도 앱이나 정류장 안내기에서 다시 확인하세요.  \n(Check real-time arrival information in a map app or on the stop display.)",
        ],
        SUB_BUS_TAP_OFF_TRANSFER: [
            "환승 가능 시간과 요금 규칙은 지역과 교통수단에 따라 다를 수 있습니다.  \n(Transfer time and fare rules can differ by region and transportation type.)",
            "헷갈리면 내릴 때 태그하는 것이 더 안전합니다.  \n(If you are not sure, tapping off when getting off is safer.)",
        ],
        SUB_TRANSPORT_CARD_CHARGE: [
            "충전 가능 카드 종류, 결제 수단, 충전 방식은 장소와 기기에 따라 다를 수 있습니다.  \n(Available card types, payment methods, and recharge methods can differ by place and machine.)",
        ],
        SUB_TRANSPORT_CARD_USAGE: [
            "잔액 부족이나 카드 인식 오류가 있으면 승차가 어려울 수 있습니다.  \n(If the balance is low or the card is not recognized, boarding may be difficult.)",
            "단말기 위치는 버스와 지하철역 구조에 따라 다를 수 있습니다.  \n(Card reader locations can differ by bus or station.)",
        ],
        SUB_TAXI_EXPRESSION: [
            "예상 요금과 소요 시간은 교통 상황에 따라 달라질 수 있습니다.  \n(Fare and travel time can vary depending on traffic.)",
        ],
        SUB_FIXED_PLACE: [
            "정확한 경로와 도착 시간은 지도 앱이나 정류장 안내기를 함께 확인하세요.  \n(Check the exact route and arrival time in a map app or on-site display.)",
        ],
        SUB_LATE_NIGHT: [
            "막차 시간과 요금은 변동될 수 있습니다.  \n(Last service times and fares can change.)",
            "밤늦은 시간에는 밝고 안전한 장소에서 대체 이동수단을 확인하세요.  \n(At night, check other options in a safe, well-lit place.)",
        ],
    }

    warnings = list(warning_map.get(sub_category, warning_map[SUB_FIXED_PLACE]))
    for warning in extra_warnings:
        if warning and warning not in warnings:
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
    del sources
    expression_heading = build_expression_heading(sub_category)

    sections = [
        build_intro(sub_category, user_input, origin, destination),
        "## 상황 분류",
        f"교통 / {sub_category}",
        "## 지금 할 일",
        format_numbered(action_steps),
        "## 준비물",
        format_checkboxes(checklist),
        f"## {expression_heading}",
        format_bullets(expressions),
        "## 주의사항",
        format_bullets(warnings),
    ]
    return "\n\n".join(section for section in sections if section).strip()


def build_intro(sub_category: str, user_input: str, origin: str, destination: str) -> str:
    details = build_question_details(user_input, destination)

    intro_map = {
        SUB_BUS_ROUTE_CHECK: (
            f"{details['destination_text']}에 가는 버스인지 확인하려면 버스 번호, 방향, 정류장 목록을 함께 봐야 해요.\n"
            f"(To check whether the bus goes to {details['destination_en']}, check the bus number, direction, and stop list together.)"
        ),
        SUB_BUS_TAP_OFF_TRANSFER: (
            "버스에서 내릴 때는 교통카드를 한 번 더 태그하는 것이 안전해요. 환승이나 거리 요금 계산에 필요할 수 있습니다.\n"
            "(When getting off the bus, it is safer to tap your card again. It may be needed for transfers or distance-based fares.)"
        ),
        SUB_TRANSPORT_CARD_CHARGE: (
            "교통카드는 편의점이나 역 충전기에서 충전 가능 여부를 먼저 확인하면 좋아요.\n"
            "(For a transportation card, first check whether recharging is available at a convenience store or station machine.)"
        ),
        SUB_TRANSPORT_CARD_USAGE: (
            "버스나 지하철을 탈 때는 카드 단말기에 교통카드를 가볍게 대고 인식 여부를 확인하면 됩니다.\n"
            "(When taking a bus or subway, tap your card on the reader and check that it is recognized.)"
        ),
        SUB_TAXI_EXPRESSION: (
            "택시를 탈 때는 목적지를 짧게 말하거나 기사님에게 문장을 보여주면 좋아요.\n"
            "(When taking a taxi, say the destination briefly or show the sentence to the driver.)"
        ),
        SUB_FIXED_PLACE: (
            f"{origin}에서 {destination}까지는 지도 앱에 출발지와 목적지를 넣고 방향과 내릴 정류장을 함께 확인하세요.\n"
            f"(From {origin} to {destination}, enter both places in a map app and check the direction and stop.)"
        ),
        SUB_LATE_NIGHT: (
            "밤늦은 시간에는 막차 여부를 먼저 확인하고, 안전한 장소에서 대체 이동수단도 함께 확인하세요.\n"
            "(Late at night, first check the last service and also check other options from a safe place.)"
        ),
    }
    return intro_map.get(
        sub_category,
        "교통 이용이 헷갈릴 때는 지도 앱과 현장 안내를 함께 확인하면 안전해요.\n"
        "(When transportation is confusing, check both a map app and on-site information.)",
    )


def build_expression_heading(sub_category: str) -> str:
    if sub_category == SUB_TAXI_EXPRESSION:
        return "택시 기사님에게 보여줄 문장"
    if sub_category == SUB_TRANSPORT_CARD_CHARGE:
        return "편의점/역 직원에게 말하거나 보여줄 문장"
    if sub_category == SUB_TRANSPORT_CARD_USAGE:
        return "기사님이나 역 직원에게 물어볼 문장"
    if sub_category == SUB_BUS_TAP_OFF_TRANSFER:
        return "기사님이나 주변 사람에게 물어볼 문장"
    return "기사님이나 주변 사람에게 확인할 문장"


def build_question_details(user_input: str, destination: str) -> dict[str, str]:
    bus_number = extract_bus_number(user_input)
    destination_text = destination or extract_destination_from_question(user_input) or "목적지"
    destination_en = translate_destination(destination_text)
    bus_search_text = f"{bus_number}번 버스" if bus_number else "버스 번호 또는 목적지"
    bus_search_text_en = f"bus {bus_number}" if bus_number else "the bus number or destination"
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
        r"버스가\s*(?P<destination>.+?)(?:에|으로|로)\s*가",
        r"\d{2,5}\s*번?\s*버스가\s*(?P<destination>.+?)(?:에|으로|로)\s*가",
        r"(?P<destination>.+?)(?:에|으로|로)\s*가나요",
        r"(?P<destination>.+?)(?:에|으로|로)\s*가려면",
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
        return "1. 지도 앱이나 현장 안내를 먼저 확인하세요.  \n   (Check a map app or on-site information first.)"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def format_checkboxes(items: list[str]) -> str:
    if not items:
        return "□ 지도 앱 확인"
    return "\n".join(f"□ {item}" for item in items)


def format_bullets(items: list[str]) -> str:
    if not items:
        return "- 현장에서 다시 확인해주세요.  \n  (Please check again on site.)"
    return "\n".join(f"- {item}" for item in items)


def build_supported_route_tips(origin: str, destination: str) -> list[str]:
    route_key = {normalize_place_name(origin), normalize_place_name(destination)}
    tips: list[str] = []

    if {"중앙역", "한대앞역"} <= route_key:
        tips.append(
            "중앙역과 한대앞역 사이는 지하철 4호선 방향과 정차 여부를 지도 앱에서 확인합니다.  \n"
            "(Between Jungang Station and Hanyang University at Ansan Station, check Line 4 direction and stops in a map app.)"
        )

    if "한양대 ERICA" in route_key and ("중앙역" in route_key or "한대앞역" in route_key):
        tips.append(
            "한양대 ERICA가 포함된 경로는 학교 방면 버스와 내릴 정류장을 지도 앱에서 함께 확인합니다.  \n"
            "(For a route involving Hanyang University ERICA, check school-bound buses and the stop where you should get off.)"
        )

    return tips


def normalize_place_name(place: str) -> str:
    normalized = place.strip().lower()
    aliases = {
        "중앙역": "중앙역",
        "안산 중앙역": "중앙역",
        "한대앞": "한대앞역",
        "한대앞역": "한대앞역",
        "한양대 erica": "한양대 ERICA",
        "한양대 에리카": "한양대 ERICA",
        "erica": "한양대 ERICA",
        "에리카": "한양대 ERICA",
    }
    return aliases.get(normalized, place.strip())


def format_taxi_destination(destination: str) -> str:
    if normalize_place_name(destination) == "한양대 ERICA":
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
