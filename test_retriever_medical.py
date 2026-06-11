from test.test_support import RetrieverCase, run_retriever_cases

TEST_CASES = [
    RetrieverCase(
        name="medical_general",
        category="medical",
        query="기침이 나고 열이 있어요.",
        expected_source="medical/medical_general.md",
        expected_sub_category="일반 진료/약국",
    ),
    RetrieverCase(
        name="medical_emergency",
        category="medical",
        query="밤늦게 갑자기 아프면 응급실 가야 하나요?",
        expected_source="medical/medical_emergency.md",
        expected_sub_category="야간/응급",
    ),
    RetrieverCase(
        name="medical_health_insurance_bill",
        category="medical",
        query="건강 보험 고지서가 나왔어요 어떻게 해야 돼요?",
        expected_source="medical/medical_health_insurance_bill.md",
        expected_sub_category="건강보험 고지서/보험료",
        absent_sources=(
            "medical/medical_public_health_vaccination.md",
            "medical/medical_cost_insurance.md",
        ),
    ),
    RetrieverCase(
        name="medical_public_health_vaccination",
        category="medical",
        query="외국인도 보건소에서 무료로 예방접종을 받을 수 있나요?",
        expected_source="medical/medical_public_health_vaccination.md",
        expected_sub_category="보건소/예방접종",
        absent_sources=(
            "medical/medical_health_insurance_bill.md",
            "medical/medical_cost_insurance.md",
        ),
    ),
    RetrieverCase(
        name="medical_cost_insurance",
        category="medical",
        query="의료비 본인부담금이 너무 많이 나왔어요.",
        expected_source="medical/medical_cost_insurance.md",
        expected_sub_category="의료비/보험 자격 문의",
        absent_sources=(
            "medical/medical_health_insurance_bill.md",
            "medical/medical_public_health_vaccination.md",
        ),
    ),
]


def main() -> None:
    run_retriever_cases("retriever_medical", TEST_CASES)


if __name__ == "__main__":
    main()
