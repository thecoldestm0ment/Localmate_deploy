from test_support import LocalMateCase, run_localmate_cases

TEST_CASES = [
    LocalMateCase(
        name="traffic_bus_number_destination",
        query="3102 버스가 한양대 ERICA에 가나요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=False,
        contains=(
            "지도 앱에서 3102 또는 3102 버스",
            "버스 방향, 정류장 목록, 도착 시간",
            "기사님이나 주변 사람에게 말하거나 보여줄 문장",
            "“3102번 버스가 한양대 ERICA에 가나요?”",
            "(Does bus 3102 go to Hanyang University ERICA?)",
            "traffic/bus_transfer.md",
        ),
    ),
    LocalMateCase(
        name="traffic_bus_transfer",
        query="버스에서 내릴 때도 카드를 찍어야 해요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=False,
        contains=(
            "내릴 정류장 이름",
            "교통카드 잔액",
            "기사님이나 주변 사람에게 말하거나 보여줄 문장",
            "(Before boarding, it is safer to ask the driver once more.)",
            "traffic/bus_transfer.md",
        ),
    ),
    LocalMateCase(
        name="traffic_transport_card",
        query="교통카드는 어디서 충전해요?",
        category="traffic",
        sub_category="교통카드/결제",
        needs_clarification=False,
        contains=(
            "편의점이나 역 충전기",
            "편의점 직원이나 역 직원에게 말하거나 보여줄 문장",
            "“교통카드 충전하고 싶어요.”",
            "(I would like to recharge my transportation card.)",
            "traffic/transport_card.md",
        ),
    ),
    LocalMateCase(
        name="traffic_taxi_usage",
        query="택시 기사님에게 한양대 ERICA로 가달라고 말하고 싶어요.",
        category="traffic",
        sub_category="택시 이용",
        needs_clarification=False,
        contains=(
            "택시 기사님에게 말하거나 보여줄 문장",
            "“한양대 ERICA 정문으로 가주세요.”",
            "(Please take me to Hanyang University ERICA.)",
            "“카드 결제 가능해요?”",
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
            "지도 앱에 출발지는 중앙역, 목적지는 한양대 ERICA로 입력합니다.",
            "버스나 지하철을 탈 때는 번호만 보지 말고 방향과 내릴 정류장/역을 함께 확인합니다.",
            "3102번 등 학교 방면 버스 후보",
            "기사님이나 주변 사람에게 말하거나 보여줄 문장",
            "traffic/ansan_fixed_places_guide.md",
        ),
    ),
    LocalMateCase(
        name="traffic_generic_route_with_origin_destination",
        query="서울역에서 홍대입구역 어떻게 가요?",
        category="traffic",
        sub_category="고정 장소 이동",
        needs_clarification=False,
        contains=(
            "지도 앱에 출발지는 서울역, 목적지는 홍대입구역으로 입력합니다.",
            "추천 경로에서 버스/지하철/도보 중 지금 이용하기 쉬운 방법을 선택합니다.",
            "버스나 지하철을 탈 때는 번호만 보지 말고 방향과 내릴 정류장/역을 함께 확인합니다.",
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
        name="traffic_over_medical_destination",
        query="병원에 버스로 어떻게 가요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=True,
        contains=("출발지와 목적지가 어디인가요?",),
    ),
    LocalMateCase(
        name="traffic_over_admin_destination",
        query="출입국사무소에 택시 타고 가고 싶어요.",
        category="traffic",
        sub_category="택시 이용",
        needs_clarification=False,
        contains=(
            "택시 기사님에게 말하거나 보여줄 문장",
            "“카드 결제 가능해요?”",
            "traffic/taxi_usage.md",
        ),
    ),
]


def main() -> None:
    run_localmate_cases("traffic", TEST_CASES)


if __name__ == "__main__":
    main()
