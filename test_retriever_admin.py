from test.test_support import RetrieverCase, run_retriever_cases

TEST_CASES = [
    RetrieverCase(
        name="admin_alien_card_loss",
        category="admin",
        query="외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?",
        expected_source="admin/admin_alien_card_loss.md",
        expected_sub_category="외국인등록증 분실",
    ),
    RetrieverCase(
        name="admin_address_change",
        category="admin",
        query="이사했는데 주소 변경 신고를 해야 하나요?",
        expected_source="admin/admin_address_change.md",
        expected_sub_category="주소 변경",
    ),
    RetrieverCase(
        name="admin_visa_extension",
        category="admin",
        query="비자 기간이 곧 끝나요. 뭘 해야 하나요?",
        expected_source="admin/admin_visa_extension.md",
        expected_sub_category="체류기간 연장/비자",
    ),
]


def main() -> None:
    run_retriever_cases("retriever_admin", TEST_CASES)


if __name__ == "__main__":
    main()
