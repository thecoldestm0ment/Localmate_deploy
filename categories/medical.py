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


def can_handle(user_input: str) -> bool:
    text = user_input.strip().lower()
    return any(keyword in text for keyword in MEDICAL_KEYWORDS)


def run_category(user_input: str) -> str:
    _ = user_input
    return (
        "의료 카테고리는 현재 팀원이 구현 중입니다.\n\n"
        "증상, 진료과, 응급 여부를 함께 알려주시면 이후 의료 모듈에 바로 연결할 수 있게 구조를 준비해 두었습니다."
    )
