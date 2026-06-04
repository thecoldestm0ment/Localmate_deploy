from test_support import LocalMateCase, run_localmate_cases

TEST_CASES = [
    LocalMateCase(
        name="medical_general",
        query="기침이 나고 열이 있어요.",
        category="medical",
        sub_category="일반 진료/약국",
        needs_clarification=False,
        contains=("의료 / 일반 진료/약국", "medical/medical_general.md"),
    ),
    LocalMateCase(
        name="medical_late_night_emergency",
        query="밤늦게 갑자기 아프면 응급실 가야 하나요?",
        category="medical",
        sub_category="야간/응급",
        needs_clarification=False,
        contains=(
            "의료 / 야간/응급",
            "medical/medical_emergency.md",
        ),
    ),
]


def main() -> None:
    run_localmate_cases("medical", TEST_CASES)


if __name__ == "__main__":
    main()
