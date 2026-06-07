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
            "병원/약국 직원에게 말하거나 보여줄 문장",
            "증상과 시작 시간을 짧게 정리해 병원이나 약국 직원에게 알려주세요.",
            "(Briefly explain your symptoms and when they started to hospital or pharmacy staff.)",
        ),
        absent=(
            "## 참고 문서",
            "medical/medical_general.md",
            "관련 문서를 충분히 찾지 못했습니다",
        ),
    ),
    LocalMateCase(
        name="medical_health_insurance_bill",
        query="건강 보험 고지서가 나왔어요 어떻게 해야 돼요?",
        category="medical",
        sub_category="건강보험 고지서/보험료",
        needs_clarification=False,
        contains=(
            "의료 / 건강보험 고지서/보험료",
            "고지서에 적힌 납부 금액을 확인하세요.",
            "납부 기한을 확인하세요.",
            "본인 명의 고지서인지 확인하세요.",
            "납부 방법을 확인하세요.",
            "국민건강보험공단에 문의하세요.",
            "납부 후 처리 여부를 확인하세요.",
            "국민건강보험공단 직원에게 말하거나 보여줄 문장",
            "건강보험 고지서 금액과 납부 기한을 확인하고 싶습니다.",
        ),
        absent=(
            "보건소 무료 예방접종",
            "가족 합가 신청",
            "주소 변경 서류",
            "## 참고 문서",
            "medical/medical_admin.md",
            "관련 문서를 충분히 찾지 못했습니다",
        ),
    ),
    LocalMateCase(
        name="medical_public_health_vaccination",
        query="외국인도 보건소에서 무료로 예방접종을 받을 수 있나요?",
        category="medical",
        sub_category="보건소/예방접종",
        needs_clarification=False,
        contains=(
            "의료 / 보건소/예방접종",
            "무료 여부는 지역, 나이, 체류자격, 접종 종류에 따라 다를 수 있어요.",
            "보건소에 대상 여부를 먼저 확인하세요.",
            "보건소 직원에게 말하거나 보여줄 문장",
        ),
        absent=(
            "무료로 받을 수 있습니다",
            "## 참고 문서",
            "medical/medical_admin.md",
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
            "증상이 심하거나 숨쉬기 어렵거나 움직이기 힘들면 먼저 119에 연락하거나 응급실로 가세요.",
            "(If symptoms are severe, breathing is difficult, or moving is hard, call 119 or go to the emergency room first.)",
            "□ 현재 위치 메모 (Current location note)  \n□ 외국인등록증 또는 여권 (Alien registration card or passport)",
            "응급실 직원이나 119에 말할 문장",
        ),
        absent=(
            "사설 구급차",
            "응급의료관리료",
            "## 참고 문서",
            "medical/medical_emergency.md",
            "관련 문서를 충분히 찾지 못했습니다",
        ),
    ),
    LocalMateCase(
        name="medical_cost_insurance_eligibility",
        query="의료비 본인부담금이 너무 많이 나왔어요.",
        category="medical",
        sub_category="의료비/보험 자격 문의",
        needs_clarification=False,
        contains=(
            "의료 / 의료비/보험 자격 문의",
            "진료비 내역서와 영수증을 확인하세요.",
            "건강보험 자격이 적용됐는지 확인하세요.",
            "병원 원무과 또는 국민건강보험공단 직원에게 말하거나 보여줄 문장",
        ),
        absent=(
            "## 참고 문서",
            "medical/medical_admin.md",
            "관련 문서를 충분히 찾지 못했습니다",
        ),
    ),
]


def main() -> None:
    run_localmate_cases("medical", TEST_CASES)


if __name__ == "__main__":
    main()
