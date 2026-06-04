# 기존에 작성해두신 의료 도메인 프롬프트 및 안내 상수 세트
MEDICAL_CLASSIFICATION_PROMPT = """
의료 질문을 아래 세부 카테고리 중 하나로 분류한다.
- 일반 진료/약국
- 야간/응급
- 의료 행정/보험
- 약 복용/처방
- 예방접종/검사
- 애매함
""".strip()

MEDICAL_ACTION_GUIDE_PROMPT = """
특정 질병에 대한 전문적인 의학적 진단, 약물 오남용 우려가 있는 처방, 정확한 수술 비용을 지어내지 않는다.
환자의 상태나 증상이 불명확하면 확인 질문으로 돌리고,
중증 및 응급 상황으로 판단될 경우 즉시 119 신고 또는 대형병원 응급실 방문을 안내한다.
""".strip()

MEDICAL_EXPRESSION_PROMPT = """
외국인 주민이 병원 원무과나 약국에서 바로 따라 말할 수 있는 짧고 쉬운 한국어 표현을 만든다.
필요하면 아주 짧은 영어 의미를 괄호로 붙일 수 있다.
""".strip()

MEDICAL_WARNING_PROMPT = """
의료 답변에는 전문 의학적 진단 대체 불가, 주말/야간 전문의 부재 가능성,
응급의료관리료 등 추가 비용 발생 가능성, 건강보험 체납 시 불이익 경고가 포함되어야 한다.
""".strip()

MEDICAL_WARNING_BULLETS = [
    "본 안내는 의사의 전문적인 진단을 대체할 수 없습니다.",
    "야간 및 휴일에는 병원 사정에 따라 특정 진료과 전문의가 부재할 수 있습니다.",
    "응급실 이용 시 증상에 따라 응급의료관리료 등 추가 비용이 발생할 수 있습니다.",
    "건강보험료가 체납된 경우 보험 수가 미적용 및 체류 자격 연장에 제한이 있을 수 있습니다.",
]

MEDICAL_INSURANCE_TYPE_QUESTION = """어떤 업무에 대한 안내가 필요하신가요?
1. 건강보험 가입 자격 및 고지서 확인
2. 보건소 무료 검사 및 예방접종
3. 진료비 및 약값 환급 신청
4. 외국인 건강보험 체납 문제"""

SUPPORTED_HOSPITAL_TYPES_TEXT = "보건소, 일반 의원, 종합병원 응급실"

MEDICAL_SYMPTOM_CLARIFICATION_QUESTION = f"""현재 어떤 증상이 있으신가요?
현재 MVP에서는 {SUPPORTED_HOSPITAL_TYPES_TEXT} 이용 가이드라인을 우선 지원합니다.
가장 겪고 계신 증상이나 방문 목적을 알려주세요."""

MEDICAL_UNSUPPORTED_SYMPTOM_QUESTION = f"""현재 MVP에서는 {SUPPORTED_HOSPITAL_TYPES_TEXT} 중심의 기초 의료 행정 및 대처 안내를 우선 지원합니다.
상세한 전문 의학적 상담은 어렵지만,
응급실 이용 절차, 건강보험 고지서 처리, 약국 이용 표현과 같은 일반 의료 안내가 필요한지 알려주세요."""

MEDICAL_REALTIME_EMERGENCY_RESPONSE = """저는 실시간 응급실 병상 현황이나 전문의 대기 여부를 직접 조회하지는 못합니다.
방문 전 해당 병원 원무과에 유선으로 접수 가능 여부를 확인해야 합니다.
대신 병원에 전화할 때 이렇게 물어볼 수 있습니다.
"지금 응급실 접수 가능한가요?"
"야간에 진료 가능한 의사 선생님 계시나요?" """

MEDICAL_GENERIC_CLARIFICATION_QUESTION = f"""어디가 아프신지 또는 어떤 의료 도움이 필요하신지 조금 더 알려주세요.
현재 MVP에서는 {SUPPORTED_HOSPITAL_TYPES_TEXT} 중심의 이용 안내를 우선 지원합니다."""

MEDICAL_EMERGENCY_SECTION_TEMPLATE = """## 안산 응급 의료 안내
- 증상 및 상황: {symptom}
- 권장 기관: {hospital_type}
- 안내: 야간 및 휴일 방문 전 반드시 해당 기관 원무과에 유선으로 진료 가능 여부를 확인하세요."""

MEDICAL_FINAL_TEMPLATE = """## 상황 분류
의료 / {sub_category}

## 지금 해야 할 일
{action_steps}

## 진료 전 확인할 것
{checklist}

## 사용할 수 있는 한국어
{expressions}

{place_section}## 주의사항
{warnings}

## 참고 문서
{sources}
"""


# medical.py에서 import하여 호출할 렌더링 함수 추가 정의
def render_medical_plan_prompt(user_input: str, sub_category: str, context: str) -> str:
    """사용자 입력과 RAG 컨텍스트를 결합하여 의료 플랜 생성용 최종 프롬프트를 빌드합니다."""
    return f"""
당신은 외국인 주민을 위한 전문 의료 행정 및 병의원 이용 안내 가이드 AI 에이전트입니다.
제공된 참고 문서 컨텍스트를 기반으로 사용자의 질문에 맞는 안전하고 실용적인 행동 지침을 작성하세요.

[지침 사항]
1. {MEDICAL_ACTION_GUIDE_PROMPT}
2. 분류 체계 지침: {MEDICAL_CLASSIFICATION_PROMPT}
3. 한국어 표현 지침: {MEDICAL_EXPRESSION_PROMPT}
4. 주의사항 필수 포함 지침: {MEDICAL_WARNING_PROMPT}

[사용자 입력 질문]
{user_input}

[현재 시스템이 분류한 세부 카테고리]
{sub_category}

[벡터 데이터베이스 참고 문서 컨텍스트]
{context}

출력은 반드시 사전에 정의된 데이터 스키마 규격(action_plan, checklist, korean_expressions) 구조의 JSON 포맷 형식을 준수하여 내보내야 합니다.
""".strip()