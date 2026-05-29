from test.test_support import RetrieverCase, run_retriever_cases

TEST_CASES = [
    RetrieverCase(
        name="traffic_transport_card",
        category="traffic",
        query="교통카드는 어디서 충전해요?",
        expected_source="traffic/transport_card.md",
        expected_sub_category="교통카드/결제",
    ),
    RetrieverCase(
        name="traffic_bus_transfer",
        category="traffic",
        query="버스에서 내릴 때도 카드를 찍어야 해요?",
        expected_source="traffic/bus_transfer.md",
        expected_sub_category="버스 이용/환승",
    ),
    RetrieverCase(
        name="traffic_fixed_place_route",
        category="traffic",
        query="중앙역에서 한양대 ERICA 어떻게 가요?",
        expected_source="traffic/ansan_fixed_places_guide.md",
        expected_sub_category="고정 장소 이동",
    ),
]


def main() -> None:
    run_retriever_cases("retriever_traffic", TEST_CASES)


if __name__ == "__main__":
    main()
