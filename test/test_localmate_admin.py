from test.test_support import LocalMateCase, run_localmate_cases

TEST_CASES = [
    LocalMateCase(
        name="admin_alien_card_loss",
        query="외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?",
        category="admin",
        sub_category="외국인등록증 분실",
        needs_clarification=False,
        contains=(
            "행정 / 외국인등록증 분실",
            "준비물 체크리스트",
            "기관에서 사용할 한국어",
            "admin/admin_alien_card_loss.md",
        ),
    ),
    LocalMateCase(
        name="admin_card_ambiguous",
        query="카드를 잃어버렸어요.",
        category="admin",
        sub_category="애매함",
        needs_clarification=True,
        contains=(
            "어떤 카드를 잃어버리셨나요?",
            "1. 외국인등록증",
            "3. 교통카드/티머니",
        ),
    ),
]


def main() -> None:
    run_localmate_cases("admin", TEST_CASES)


if __name__ == "__main__":
    main()
