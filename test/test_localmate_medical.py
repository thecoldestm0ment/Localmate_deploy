from test_support import LocalMateCase, run_localmate_cases

TEST_CASES = [
    LocalMateCase(
        name="medical_general",
        query="기침이 나고 열이 있어요.",
        category="medical",
        sub_category="일반 진료/약국",
        needs_clarification=False,
        contains=(
            "의료 / 일반 진료/약국",
            "본 안내는 의사의 전문적인 진단",
            "medical/medical_general.md",
        ),
    ),
    LocalMateCase(
        name="medical_admin_health_insurance_notice",
        query="건강 보험 고지서가 나왔어요 어떻게 해야 돼요?",
        category="medical",
        sub_category="의료 행정/보험",
        needs_clarification=False,
        contains=(
            "의료 / 의료 행정/보험",
            "국민건강보험 고지서",
            "건강보험 가입 자격, 보험료, 체납, 감면 기준",
            "medical/medical_admin.md",
        ),
        absent=(
            "본 안내는 의사의 전문적인 진단",
            "119 또는 응급실",
            "관련 문서를 충분히 찾지 못했습니다",
        ),
    ),
    LocalMateCase(
        name="medical_admin_public_health_center",
        query="외국인도 보건소에서 무료로 예방접종 받을 수 있나요?",
        category="medical",
        sub_category="의료 행정/보험",
        needs_clarification=False,
        contains=(
            "의료 / 의료 행정/보험",
            "보건소",
            "국민건강보험공단, 보건소, 공식 안내",
        ),
        absent=(
            "본 안내는 의사의 전문적인 진단",
            "119 또는 응급실",
            "관련 문서를 충분히 찾지 못했습니다",
        ),
    ),
    LocalMateCase(
        name="medical_late_night_emergency",
        query="밤늦게 갑자기 아프면 응급실 가야 하나요?",
        category="medical",
        sub_category="야간/응급",
        needs_clarification=False,
        contains=(
            "의료 / 야간/응급",
            "119 또는 응급실",
            "medical/medical_emergency.md",
        ),
    ),
]


def main() -> None:
    run_localmate_cases("medical", TEST_CASES)


if __name__ == "__main__":
    main()
