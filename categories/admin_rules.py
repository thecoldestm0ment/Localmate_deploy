CATEGORY_NAME = "admin"
ROUTE_PRIORITY = 20
DISPLAY_CATEGORY = "행정"
ADMIN_FILTER = {"category": "admin"}

SUB_ALIEN_CARD_LOSS = "외국인등록증 분실"
SUB_ADDRESS_CHANGE = "주소 변경"
SUB_VISA = "체류기간 연장/비자"
SUB_VISIT = "기관 방문/예약"
SUB_MISC = "기타 행정"
SUB_AMBIGUOUS = "애매함"

NO_DOCS_WARNING = (
    "관련 문서를 충분히 찾지 못했습니다. 공식 안내 확인이 필요합니다."
)
GENERATION_ERROR_MESSAGE = (
    "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
)

CLARIFY_CARD_QUESTION = """어떤 카드를 잃어버리셨나요?
1. 외국인등록증
2. 은행 카드
3. 교통카드/티머니
4. 학생증"""

ADMIN_KEYWORDS = (
    "외국인등록증",
    "외국인 등록증",
    "비자",
    "체류",
    "체류기간",
    "체류 자격",
    "체류자격",
    "출입국",
    "주소",
    "주소 변경",
    "주소변경",
    "이사",
    "전입",
    "등록증",
    "행정",
    "신고",
)

LOSS_KEYWORDS = ("잃어버", "분실", "없어졌", "사라졌")
ALIEN_CARD_KEYWORDS = (
    "외국인등록증",
    "외국인 등록증",
    "alien registration card",
    "arc",
)
GENERIC_CARD_KEYWORDS = ("카드", "등록증", "신분증")
CARD_LOSS_EXCLUDE_KEYWORDS = ("은행", "교통", "티머니")
ADDRESS_KEYWORDS = ("주소 변경", "주소변경", "주소", "이사", "전입")
VISA_KEYWORDS = (
    "비자",
    "체류기간",
    "체류 기간",
    "체류자격",
    "체류 자격",
    "연장",
    "만료",
    "체류",
)
VISIT_KEYWORDS = ("예약", "방문")


def normalize_text(text: str) -> str:
    return text.strip().lower()


def has_any_keyword(text: str, keywords: list[str] | tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def is_ambiguous_card_loss(text: str) -> bool:
    return (
        has_any_keyword(text, GENERIC_CARD_KEYWORDS)
        and has_any_keyword(text, LOSS_KEYWORDS)
        and not has_any_keyword(
            text,
            ALIEN_CARD_KEYWORDS + CARD_LOSS_EXCLUDE_KEYWORDS,
        )
    )


def classify_admin_input(user_input: str) -> dict[str, str | bool]:
    text = normalize_text(user_input)

    if has_any_keyword(text, ALIEN_CARD_KEYWORDS) and has_any_keyword(text, LOSS_KEYWORDS):
        sub_category = SUB_ALIEN_CARD_LOSS
        needs_clarification = False
        clarifying_question = ""
    elif is_ambiguous_card_loss(text):
        sub_category = SUB_AMBIGUOUS
        needs_clarification = True
        clarifying_question = CLARIFY_CARD_QUESTION
    elif has_any_keyword(text, ADDRESS_KEYWORDS):
        sub_category = SUB_ADDRESS_CHANGE
        needs_clarification = False
        clarifying_question = ""
    elif has_any_keyword(text, VISA_KEYWORDS):
        sub_category = SUB_VISA
        needs_clarification = False
        clarifying_question = ""
    elif has_any_keyword(text, VISIT_KEYWORDS):
        sub_category = SUB_VISIT
        needs_clarification = False
        clarifying_question = ""
    else:
        sub_category = SUB_MISC
        needs_clarification = False
        clarifying_question = ""

    return {
        "category": DISPLAY_CATEGORY,
        "sub_category": sub_category,
        "needs_clarification": needs_clarification,
        "clarifying_question": clarifying_question,
    }
