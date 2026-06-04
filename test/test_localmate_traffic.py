from test_support import LocalMateCase, run_localmate_cases

TEST_CASES = [
    LocalMateCase(
        name="traffic_transport_card",
        query="교통카드는 어디서 충전해요?",
        category="traffic",
        sub_category="교통카드/결제",
        needs_clarification=False,
        contains=(
            "교통 / 교통카드/결제",
            "교통카드 충전하고 싶어요.",
            "traffic/transport_card.md",
        ),
    ),
    LocalMateCase(
        name="traffic_bus_transfer",
        query="버스에서 내릴 때도 카드를 찍어야 해요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=False,
        contains=(
            "교통 / 버스 이용/환승",
            "환승",
            "traffic/bus_transfer.md",
        ),
    ),
    LocalMateCase(
        name="traffic_taxi_usage",
        query="택시 기사님에게 한양대 ERICA로 가달라고 말하고 싶어요.",
        category="traffic",
        sub_category="택시 이용",
        needs_clarification=False,
        contains=(
            "교통 / 택시 이용",
            "한양대 ERICA 정문으로 가주세요.",
            "카드 결제 가능해요?",
            "traffic/taxi_usage.md",
        ),
    ),
    LocalMateCase(
        name="traffic_fixed_place_route",
        query="중앙역에서 한양대 ERICA 어떻게 가요?",
        category="traffic",
        sub_category="고정 장소 이동",
        needs_clarification=False,
        contains=(
            "교통 / 고정 장소 이동",
            "출발지: 중앙역",
            "목적지: 한양대 ERICA",
            "지도 앱 또는 정류장 안내기",
            "traffic/ansan_fixed_places_guide.md",
        ),
    ),
    LocalMateCase(
        name="traffic_missing_origin",
        query="한양대 ERICA 가고 싶어요.",
        category="traffic",
        sub_category="고정 장소 이동",
        needs_clarification=True,
        contains=(
            "출발지가 어디인가요?",
            "중앙역, 한대앞역, 한양대 ERICA",
        ),
    ),
    LocalMateCase(
        name="traffic_realtime_arrival",
        query="지금 버스 몇 분 뒤에 와요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=True,
        contains=(
            "실시간 버스 도착 시간",
            "정류장 안내기나 지도 앱",
            "이 버스 언제 와요?",
        ),
    ),
    LocalMateCase(
        name="traffic_last_bus",
        query="막차 언제예요?",
        category="traffic",
        sub_category="막차/야간 이동",
        needs_clarification=False,
        contains=(
            "교통 / 막차/야간 이동",
            "traffic/late_night_transport.md",
        ),
    ),
    LocalMateCase(
        name="traffic_late_night_bus",
        query="심야버스 있나요?",
        category="traffic",
        sub_category="막차/야간 이동",
        needs_clarification=False,
        contains=(
            "교통 / 막차/야간 이동",
            "traffic/late_night_transport.md",
        ),
    ),
    LocalMateCase(
        name="traffic_late_time_bus_context",
        query="밤늦게 버스 탈 수 있나요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=False,
        contains=(
            "교통 / 버스 이용/환승",
            "traffic/bus_transfer.md",
        ),
    ),
    LocalMateCase(
        name="traffic_over_medical",
        query="병원에 버스로 어떻게 가요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=True,
        contains=("출발지와 목적지가 어디인가요?",),
    ),
    LocalMateCase(
        name="traffic_over_admin",
        query="출입국사무소에 택시 타고 가고 싶어요.",
        category="traffic",
        sub_category="택시 이용",
        needs_clarification=False,
        contains=("카드 결제 가능해요?", "교통 / 택시 이용"),
    ),
]


def main() -> None:
    run_localmate_cases("traffic", TEST_CASES)


if __name__ == "__main__":
    main()
