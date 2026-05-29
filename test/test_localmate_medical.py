from test.test_support import LocalMateCase, run_localmate_cases

TEST_CASES = [
    LocalMateCase(
        name="medical_general",
        query="기침이 나고 열이 있어요.",
        category="medical",
        sub_category="일반 진료/약국",
        needs_clarification=False,
        contains=("의료 / 일반 진료/약국", "약국은 어디에 있나요?"),
    ),
]


def main() -> None:
    run_localmate_cases("medical", TEST_CASES)


if __name__ == "__main__":
    main()
