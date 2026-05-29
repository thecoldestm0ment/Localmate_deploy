from categories.types import CategoryResult

CATEGORY_NAME = "medical"

MEDICAL_KEYWORDS = (
    "병원", "의사", "진료", "진찰", "약국", "처방전", "처방", "감기약",
    "증상", "통증", "아파", "아프", "열", "기침", "감기", "응급",
    "응급실", "119", "상처", "화상", "코피", "부상", "두통", "복통",
    "설사", "구토", "치과", "내과", "보건소", "건강보험",
)

EMERGENCY_KEYWORDS = (
    "응급", "응급실", "119", "숨쉬기", "호흡", "기절",
    "쓰러", "피가 많이", "가슴 통증", "심한 화상", "부러",
)

TRANSPORT_KEYWORDS = (
    "버스", "지하철", "택시", "정류장",
    "역", "가는 법", "어떻게 가", "이동",
)

MEDICAL_SYMPTOM_KEYWORDS = (
    "아파", "아프", "통증", "열", "기침",
    "감기", "두통", "복통", "설사", "구토", "상처",
)

CARD_LOSS_KEYWORDS = ("잃어버", "분실", "없어졌", "사라졌")
MEDICAL_CARD_CONTEXT_KEYWORDS = (
    "건강보험", "보험증", "의료", "진료", "보건소",
)
MEDICAL_ADMIN_KEYWORDS = ("건강보험", "의료비", "본인부담금", "보건소")
PHARMACY_KEYWORDS = ("약국", "처방전", "처방", "감기약")
DENTAL_KEYWORDS = ("치과", "치통", "이빨", "치아")
VAGUE_MEDICAL_INPUTS = (
    "아파요", "아파", "몸이 안 좋아요",
    "몸이 안좋아요", "병원 가야 하나요", "병원 가고 싶어요",
)

MEDICAL_CLARIFICATION_QUESTION = (
    "어디가 아프신가요? 주요 증상, 증상이 시작된 시점, 응급 상황인지 알려주세요."
)

CARD_CLARIFICATION_QUESTION = (
    "어떤 카드를 잃어버리셨나요?\n"
    "1. 외국인등록증\n"
    "2. 은행 카드\n"
    "3. 교통카드/티머니\n"
    "4. 건강보험 관련 카드"
)


def normalize(text: str) -> str:
    return text.strip().lower()


def contains_any(text: str, keywords: list[str] | tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def is_emergency(text: str) -> bool:
    return contains_any(text, EMERGENCY_KEYWORDS)


def is_transport_question(text: str) -> bool:
    return contains_any(text, TRANSPORT_KEYWORDS)


def is_medical_card_question(text: str) -> bool:
    if "카드" not in text:
        return False

    return (
        contains_any(text, CARD_LOSS_KEYWORDS)
        and contains_any(text, MEDICAL_CARD_CONTEXT_KEYWORDS)
    )


def can_handle(user_input: str) -> bool:
    text = normalize(user_input)

    if not text:
        return False

    if is_emergency(text):
        return True

    if is_medical_card_question(text):
        return True

    # "병원에 버스로 어떻게 가요?" 같은 질문은 교통 카테고리가 처리하게 둔다.
    if is_transport_question(text):
        has_medical_symptom = contains_any(text, MEDICAL_SYMPTOM_KEYWORDS)
        if not has_medical_symptom:
            return False

    return contains_any(text, MEDICAL_KEYWORDS)


def needs_clarification(user_input: str) -> bool:
    text = normalize(user_input)

    if not text:
        return True

    if is_medical_card_question(text):
        return True

    if is_emergency(text):
        return False

    return text in VAGUE_MEDICAL_INPUTS or len(text) <= 5


def get_clarification_question(user_input: str) -> str:
    text = normalize(user_input)

    if is_medical_card_question(text):
        return CARD_CLARIFICATION_QUESTION

    return MEDICAL_CLARIFICATION_QUESTION


def classify_sub_category(user_input: str) -> str:
    text = normalize(user_input)

    if is_emergency(text):
        return "야간/응급"

    if contains_any(text, MEDICAL_ADMIN_KEYWORDS):
        return "의료 행정/보험"

    if contains_any(text, PHARMACY_KEYWORDS):
        return "일반 진료/약국"

    if contains_any(text, DENTAL_KEYWORDS):
        return "치과"

    return "일반 진료/약국"


def build_answer(sub_category: str) -> str:
    if sub_category == "야간/응급":
        return (
            "## 상황 분류\n"
            "의료 / 야간·응급\n\n"
            "## 먼저 해야 할 일\n"
            "1. 위급한 상황이면 바로 119에 연락하세요.\n"
            "2. 의식 저하, 호흡곤란, 심한 출혈, 가슴 통증이 있으면 응급실 방문을 우선 고려하세요.\n"
            "3. 가능하면 외국인등록증 또는 여권, 복용 중인 약 정보를 함께 챙기세요.\n\n"
            "## 사용할 수 있는 한국어\n"
            "- “응급상황이에요. 119 불러주세요.”\n"
            "- “숨쉬기가 힘들어요.”\n"
            "- “피가 많이 나요.”\n"
            "- “응급실에 가야 해요.”\n\n"
            "## 주의사항\n"
            "- 이 안내는 진단이나 처방이 아닙니다.\n"
            "- 응급상황에서는 119 또는 의료진 안내를 우선 따르세요."
        )

    if sub_category == "의료 행정/보험":
        return (
            "## 상황 분류\n"
            "의료 / 의료 행정·보험\n\n"
            "## 먼저 확인할 것\n"
            "1. 건강보험 가입 여부를 확인하세요.\n"
            "2. 병원 방문 전 외국인 진료 가능 여부와 필요한 신분증을 확인하세요.\n"
            "3. 진료비는 보험 자격과 병원 종류에 따라 달라질 수 있습니다.\n\n"
            "## 준비물 체크리스트\n"
            "□ 외국인등록증 또는 여권\n"
            "□ 건강보험 관련 정보\n"
            "□ 증상 메모\n"
            "□ 현재 복용 중인 약 정보\n\n"
            "## 사용할 수 있는 한국어\n"
            "- “외국인도 건강보험 적용이 되나요?”\n"
            "- “진료비가 얼마나 나오는지 알 수 있을까요?”\n"
            "- “외국인등록증을 가져왔습니다.”\n\n"
            "## 주의사항\n"
            "- 체류자격, 건강보험 가입 여부, 병원 종류에 따라 비용과 절차가 달라질 수 있습니다.\n"
            "- 정확한 비용과 필요 서류는 병원 또는 공식 안내에서 확인하세요."
        )

    return (
        "## 상황 분류\n"
        f"의료 / {sub_category}\n\n"
        "## 먼저 확인할 것\n"
        "1. 증상이 언제 시작되었는지 정리하세요.\n"
        "2. 열, 기침, 통증, 출혈, 구토 등 주요 증상을 메모하세요.\n"
        "3. 증상이 심하거나 갑자기 악화되면 119 또는 응급실을 먼저 고려하세요.\n\n"
        "## 해야 할 일\n"
        "1. 가벼운 증상이라면 가까운 병의원이나 약국 이용 가능 여부를 확인하세요.\n"
        "2. 병원 방문 전 진료 시간, 예약 필요 여부, 외국인 진료 가능 여부를 확인하세요.\n"
        "3. 약이 필요한 경우 의사 또는 약사에게 복용 방법을 꼭 확인하세요.\n\n"
        "## 준비물 체크리스트\n"
        "□ 외국인등록증 또는 여권\n"
        "□ 건강보험 관련 정보\n"
        "□ 증상 메모\n"
        "□ 현재 복용 중인 약\n"
        "□ 알레르기 정보\n\n"
        "## 사용할 수 있는 한국어\n"
        "- “진료 접수하고 싶어요.”\n"
        "- “열이 나고 기침이 있어요.”\n"
        "- “언제부터 아팠는지 설명드릴게요.”\n"
        "- “외국인도 진료 가능한가요?”\n"
        "- “약국은 어디에 있나요?”\n\n"
        "## 주의사항\n"
        "- 이 안내는 진단이나 처방이 아닙니다.\n"
        "- 약 복용 여부나 치료 방법은 의사 또는 약사에게 확인하세요.\n"
        "- 상급종합병원이나 대학병원은 진료의뢰서가 필요할 수 있습니다. 방문 전 병원에 확인하세요."
    )


def run_category(user_input: str) -> CategoryResult:
    if needs_clarification(user_input):
        return CategoryResult.clarification(
            get_clarification_question(user_input),
            category=CATEGORY_NAME,
            sub_category="애매함",
        )

    sub_category = classify_sub_category(user_input)
    answer = build_answer(sub_category)

    return CategoryResult.success(
        answer,
        category=CATEGORY_NAME,
        sub_category=sub_category,
    )
