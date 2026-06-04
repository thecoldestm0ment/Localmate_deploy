TRAFFIC_CLASSIFICATION_PROMPT = """
교통 질문을 아래 세부 카테고리 중 하나로 분류한다.
- 교통카드/결제
- 버스 이용/환승
- 택시 이용
- 고정 장소 이동
- 막차/야간 이동
- 애매함
""".strip()

TRAFFIC_ACTION_GUIDE_PROMPT = """
지도 앱, 정류장 안내기, 역 안내판에서 버스 방향, 정류장 목록, 도착 시간, 요금을 확인하는 방법을 안내한다.
출발지나 목적지가 부족하면 확인 질문으로 돌리고,
타기 전 기사님이나 직원에게 한 번 더 확인할 수 있는 문장을 제공한다.
""".strip()

TRAFFIC_EXPRESSION_PROMPT = """
외국인 주민이 바로 따라 말할 수 있는 짧고 쉬운 한국어 표현을 만든다.
필요하면 아주 짧은 영어 의미를 괄호로 붙일 수 있다.
""".strip()

TRAFFIC_WARNING_PROMPT = """
교통 답변에는 지도 앱과 현장 안내기 확인 방법, 막차/요금 변동 가능성,
타기 전 기사님 확인, 야간 안전 주의가 포함되어야 한다.
""".strip()

TRAFFIC_WARNING_BULLETS = [
    "지도 앱에서 버스 번호를 검색하면 방향, 정류장 목록, 도착 시간을 확인할 수 있습니다.",
    "막차 시간과 요금은 변동될 수 있으니 지도 앱이나 현장 안내기를 함께 확인하세요.",
    "타기 전 기사님에게 목적지에 가는지 한 번 더 물어보면 안전합니다.",
    "밤늦은 시간에는 밝고 사람이 있는 장소에서 이동 방법을 확인하세요.",
]

TRAFFIC_CARD_LOSS_QUESTION = """어떤 카드를 잃어버리셨나요?
1. 외국인등록증
2. 은행 카드
3. 교통카드/티머니
4. 학생증"""

SUPPORTED_PLACE_NAMES_TEXT = "중앙역, 한대앞역, 한양대 ERICA"

TRAFFIC_FIXED_PLACE_ORIGIN_QUESTION = f"""출발지가 어디인가요?
현재 MVP에서는 {SUPPORTED_PLACE_NAMES_TEXT} 사이의 이동 안내를 우선 지원합니다.
출발지를 {SUPPORTED_PLACE_NAMES_TEXT} 중에서 알려주세요."""

TRAFFIC_ROUTE_CLARIFICATION_QUESTION = f"""출발지와 목적지가 어디인가요?
현재 MVP에서는 {SUPPORTED_PLACE_NAMES_TEXT} 사이의 이동 안내를 우선 지원합니다.
출발지와 목적지를 {SUPPORTED_PLACE_NAMES_TEXT} 중에서 알려주세요."""

TRAFFIC_UNSUPPORTED_PLACE_QUESTION = f"""현재 MVP에서는 {SUPPORTED_PLACE_NAMES_TEXT} 중심의 이동 안내를 우선 지원합니다.
출발지와 목적지를 {SUPPORTED_PLACE_NAMES_TEXT} 중에서 알려주시거나,
택시 표현, 교통카드 사용, 버스/지하철 기본 이용 안내처럼 일반 교통 안내가 필요한지 알려주세요."""

TRAFFIC_REALTIME_BUS_RESPONSE = """지도 앱이나 정류장 안내기에서 버스 도착 시간과 방향을 확인할 수 있어요.
(You can check the bus arrival time and direction in a map app or on the bus stop display.)

타기 전에 기사님에게 한 번 더 물어보면 안전해요.
(Before boarding, it is safer to ask the driver once more.)

“이 버스 언제 와요?”
(When does this bus arrive?)

“이 버스가 한양대 ERICA에 가나요?”
(Does this bus go to Hanyang University ERICA?)"""

TRAFFIC_GENERIC_CLARIFICATION_QUESTION = f"""어디에서 어디로 이동하고 싶은지 조금 더 알려주세요.
현재 MVP에서는 {SUPPORTED_PLACE_NAMES_TEXT} 중심의 이동 안내를 우선 지원합니다."""

TRAFFIC_FIXED_PLACE_SECTION_TEMPLATE = """## 안산 고정 장소 안내
- 출발지: {origin}
- 목적지: {destination}
- 안내: 지도 앱에서 출발지와 목적지를 입력하고, 현장 안내기에서 방향을 한 번 더 확인하세요."""

TRAFFIC_FINAL_TEMPLATE = """{intro}

## 바로 확인하는 방법
{action_steps}

## 이동 전 확인할 것
{checklist}

## {expression_heading}
{expression_intro}
{expressions}

{place_section}## 주의사항
{warnings}

## 참고 문서
{sources}
"""
