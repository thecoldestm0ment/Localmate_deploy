CATEGORY_NAME = "medical"
ROUTE_PRIORITY = 10
DISPLAY_CATEGORY = "의료"
MEDICAL_FILTER = {"category": "medical"}

# 의료 세부 카테고리 정의
SUB_GENERAL_HOSPITAL = "일반 진료/약국"
SUB_EMERGENCY = "야간/응급"
SUB_HEALTH_INSURANCE_BILL = "건강보험 고지서/보험료"
SUB_PUBLIC_HEALTH_VACCINATION = "보건소/예방접종"
SUB_MEDICAL_COST_INSURANCE = "의료비/보험 자격 문의"
SUB_AMBIGUOUS = "애매함"

NO_DOCS_WARNING = (
    "관련 문서를 충분히 찾지 못했습니다. 공식 안내 확인이 필요합니다."
)
GENERATION_ERROR_MESSAGE = (
    "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
)

# 모호한 질문 진입 시 던질 4지선다 확인 질문
CLARIFY_HOSPITAL_QUESTION = """어떤 병원이나 업무 안내가 필요하신가요?
1. 일반 내과/치과/피부과 등 주간 진료
2. 야간 응급실 및 휴일 소아과
3. 건강보험 고지서 또는 보험료 납부
4. 보건소 예방접종 또는 무료 지원 대상 확인"""

# 대분류 판별을 위한 의료 통합 키워드
MEDICAL_KEYWORDS = (
    "병원", "의사", "진료", "진찰", "약국", "처방전", "처방", "감기약",
    "증상", "통증", "아파", "아프", "아픈", "열", "기침", "감기", "응급",
    "응급실", "119", "상처", "화상", "코피", "부상", "두통", "복통",
    "설사", "구토", "치과", "내과", "보건소", "건강보험", "건강 보험",
    "고지서", "보험료", "납부", "예방접종", "백신", "의료비", "보험 자격",
)

# 세부 카테고리 라우팅용 키워드 튜플 정의
EMERGENCY_KEYWORDS = (
    "응급", "응급실", "119", "숨쉬기", "호흡", "기절",
    "쓰러", "피가 많이", "가슴 통증", "심한 화상", "부러",
    "휴일", "주말", "새벽", "갑자기", "심하게 아프", "못 걷", "숨",
)
HEALTH_INSURANCE_BILL_KEYWORDS = (
    "건강 보험 고지서",
    "건강보험 고지서",
    "고지서",
    "보험료",
    "납부",
    "체납",
)
PUBLIC_HEALTH_VACCINATION_KEYWORDS = (
    "보건소",
    "예방접종",
    "무료 접종",
    "무료로 예방접종",
    "백신",
    "접종",
)
MEDICAL_COST_INSURANCE_KEYWORDS = (
    "의료비",
    "본인부담금",
    "보험 자격",
    "건강보험 자격",
    "건강 보험 자격",
    "환급",
    "자격 문의",
)
PHARMACY_KEYWORDS = ("약국", "처방전", "처방", "감기약")
DENTAL_KEYWORDS = ("치과", "치통", "이빨", "치아")
VAGUE_MEDICAL_INPUTS = ("아파요", "아파", "몸이 안 좋아요", "몸이 안좋아요", "병원 가야 하나요", "병원 가고 싶어요")


def normalize_text(text: str) -> str:
    return text.strip().lower()


def has_any_keyword(text: str, keywords: list[str] | tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def is_ambiguous_medical_input(text: str) -> bool:
    # 텍스트가 5글자 이하이거나 지정된 모호한 표현 집합에 완벽히 일치하는 경우를 탐지합니다.
    return text in VAGUE_MEDICAL_INPUTS or len(text) <= 5


def classify_medical_input(user_input: str) -> dict[str, str | bool]:
    text = normalize_text(user_input)

    # 1. 생명 및 시급성을 요하는 야간/응급 상황을 최우선 분기 조건으로 설정
    if has_any_keyword(text, EMERGENCY_KEYWORDS):
        sub_category = SUB_EMERGENCY
        needs_clarification = False
        clarifying_question = ""
    # 2. 건강보험 고지서 또는 보험료 납부 관련 상황
    elif has_any_keyword(text, HEALTH_INSURANCE_BILL_KEYWORDS):
        sub_category = SUB_HEALTH_INSURANCE_BILL
        needs_clarification = False
        clarifying_question = ""
    # 3. 보건소 및 예방접종 관련 상황
    elif has_any_keyword(text, PUBLIC_HEALTH_VACCINATION_KEYWORDS):
        sub_category = SUB_PUBLIC_HEALTH_VACCINATION
        needs_clarification = False
        clarifying_question = ""
    # 4. 의료비 및 건강보험 자격 문의 관련 상황
    elif has_any_keyword(text, MEDICAL_COST_INSURANCE_KEYWORDS):
        sub_category = SUB_MEDICAL_COST_INSURANCE
        needs_clarification = False
        clarifying_question = ""
    # 5. 증상이나 목적이 모호하여 확인 질문이 필요한 경우
    elif is_ambiguous_medical_input(text):
        sub_category = SUB_AMBIGUOUS
        needs_clarification = True
        clarifying_question = CLARIFY_HOSPITAL_QUESTION
    # 6. 일반 의원, 치과, 약국 관련 상황
    elif (
        has_any_keyword(text, PHARMACY_KEYWORDS)
        or has_any_keyword(text, DENTAL_KEYWORDS)
        or has_any_keyword(text, ("내과", "의원", "진료"))
    ):
        sub_category = SUB_GENERAL_HOSPITAL
        needs_clarification = False
        clarifying_question = ""
    else:
        # 매칭되는 특이 키워드가 없으나 대분류 통과 시 일반 진료를 폴백 카테고리로 지정
        sub_category = SUB_GENERAL_HOSPITAL
        needs_clarification = False
        clarifying_question = ""

    return {
        "category": DISPLAY_CATEGORY,
        "sub_category": sub_category,
        "needs_clarification": needs_clarification,
        "clarifying_question": clarifying_question,
    }
