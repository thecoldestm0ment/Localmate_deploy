from test_support import LocalMateCase, run_localmate_cases

TEST_CASES = [
    LocalMateCase(
        name="admin_alien_card_loss",
        query="외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?",
        category="admin",
        sub_category="외국인등록증 분실",
        needs_clarification=False,
        contains=(
            "외국인등록증을 잃어버렸다면 먼저 분실 여부를 확인",
            "행정 / 외국인등록증 분실",
            "## 준비물 체크리스트",
            "- [ ] 여권 (Passport)",
            "## 기관 직원에게 말하거나 보여줄 문장",
            "(I lost my Alien Registration Card. Please tell me the reissue process.)",
            "admin/admin_alien_card_loss.md",
        ),
    ),
    LocalMateCase(
        name="admin_address_change",
        query="이사했는데 주소 변경 신고를 해야 하나요?",
        category="admin",
        sub_category="주소 변경",
        needs_clarification=False,
        contains=(
            "행정 / 주소 변경",
            "이사 날짜와 새 주소",
            "(If you moved, you may need to report your new address.",
            "주소 변경 신고에는 기한이 있을 수 있으므로",
            "admin/admin_address_change.md",
        ),
    ),
    LocalMateCase(
        name="admin_visa_extension",
        query="비자 기간이 곧 끝나요. 뭘 해야 하나요?",
        category="admin",
        sub_category="체류기간 연장/비자",
        needs_clarification=False,
        contains=(
            "행정 / 체류기간 연장/비자",
            "현재 비자/체류자격 정보와 만료일",
            "(Check your current visa/status of stay and expiration date.)",
            "체류기간 만료 전에 신청 가능 시기와 필요 서류",
            "admin/admin_visa_extension.md",
        ),
    ),
    LocalMateCase(
        name="admin_expired_visa",
        query="비자 기간이 이제 지났어요. 괜찮아요?",
        category="admin",
        sub_category="체류기간 연장/비자",
        needs_clarification=False,
        contains=(
            "비자 기간이 이미 지났다면 괜찮다고 판단하지 말고",
            "가능한 빨리 관할 출입국외국인청 또는 공식 상담 채널",
            "본인의 체류자격과 만료일을 정확히 설명",
            "(If your stay period has already expired",
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
            "3. 교통카드/선불카드",
        ),
    ),
    LocalMateCase(
        name="admin_missing_task_ambiguous",
        query="서류 없이 가능한가요?",
        category="admin",
        sub_category="기타 행정",
        needs_clarification=False,
        contains=(
            "행정 / 기타 행정",
            "어떤 행정 업무인지 먼저 확인하세요.",
            "업무 종류와 개인 상황에 따라 필요한 서류와 절차가 달라질 수 있습니다.",
        ),
    ),
]


def main() -> None:
    run_localmate_cases("admin", TEST_CASES)


if __name__ == "__main__":
    main()
