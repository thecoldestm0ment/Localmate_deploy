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
