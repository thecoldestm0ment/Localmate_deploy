from categories.types import CategoryResult

MEDICAL_KEYWORDS = [
    "병원",
    "의사",
    "진료",
    "약",
    "약국",
    "증상",
    "통증",
    "아파",
    "아프",
    "열",
    "기침",
    "감기",
    "응급",
    "상처",
]
MEDICAL_CLARIFICATION_QUESTION = (
    "어디가 아프신가요? 주요 증상, 얼마나 아픈지, 응급 상황인지 알려주세요."
)


def can_handle(user_input: str) -> bool:
    text = user_input.strip().lower()
    return any(keyword in text for keyword in MEDICAL_KEYWORDS)


def needs_clarification(user_input: str) -> bool:
    text = user_input.strip().lower()
    vague_inputs = ["아파요", "아파", "몸이 안 좋아요", "몸이 안좋아요", "병원 가야 하나요"]
    return text in vague_inputs or len(text) <= 6


def run_category(user_input: str) -> CategoryResult:
    if needs_clarification(user_input):
        return CategoryResult.clarification(MEDICAL_CLARIFICATION_QUESTION, category="medical")

    return CategoryResult.success(
        "의료 카테고리는 현재 팀원이 구현 중입니다.\n\n"
        "증상, 진료과, 응급 여부를 함께 알려주시면 이후 의료 모듈에 바로 연결할 수 있게 구조를 준비해 두었습니다.",
        category="medical",
    )
