from langchain_core.documents import Document

from categories.response_format import (
    format_bullets,
    format_numbered,
    format_sources,
)
from categories.medical_rules import (
    SUB_GENERAL_HOSPITAL,
    SUB_EMERGENCY,
    SUB_ADMIN_INSURANCE,
    SUB_DENTAL,
    SUB_MISC,
)

# 서브 카테고리별 매칭되는 마크다운 원본 파일 경로 지정
PRIMARY_SOURCE_BY_SUBCATEGORY = {
    SUB_GENERAL_HOSPITAL: "medical/medical_general.md",
    SUB_EMERGENCY: "medical/medical_emergency.md",
    SUB_ADMIN_INSURANCE: "medical/medical_admin.md",
}

# 의료 도메인 공통 기본 주의사항 정의
DEFAULT_WARNINGS = [
    "본 안내는 의사의 전문적인 진단이나 처방을 대체할 수 없습니다.",
    "병원 방문 전 진료 시간과 예약 필요 여부를 반드시 유선으로 확인하십시오.",
    "급성 질환, 중상 등 위급한 상황이 발생하면 즉시 119 또는 응급실로 연락하십시오.",
]

# LLM 오류 또는 누락 시 사용될 의료 파트 폴백 데이터 세트
FALLBACK_BUNDLES: dict[str, dict[str, object]] = {
    SUB_EMERGENCY: {
        "action_plan": {
            "first_checks": [
                "환자의 의식 상태와 호흡곤란 여부를 최우선으로 확인해주세요.",
                "심한 출혈, 골절, 가슴 통증 등 즉각적인 처치가 필요한지 보세요.",
            ],
            "todo_steps": [
                "생명이 위급한 상황인 경우 지체 없이 119에 전화를 걸어 구조를 요청하세요.",
                "야간이나 주말이라면 인근 종합병원 응급실 위치와 진료 가능 여부를 확인하세요.",
                "외국인등록증이나 여권, 현재 복용 중인 약 봉투를 신속히 챙기세요.",
            ],
            "visit_or_online": [
                "이송 중이거나 방문 전에 해당 의료기관 원무과에 전화를 걸어 접수가 가능한지 확인하세요.",
                "사설 구급차를 이용할 경우 별도의 비용이 청구될 수 있음을 인지하세요.",
            ],
            "after_checks": [
                "응급실 진료 이후 원무과에서 응급의료관리료 등 추가 수수료가 청구되었는지 확인하세요.",
                "의사의 지시에 따라 외래 진료 예약이나 약국 처방전 수령 여부를 체크하세요.",
            ],
        },
        "checklist": ["외국인등록증 또는 여권", "현재 복용 중인 약 정보 또는 처방전", "지병 및 알레르기 증상 메모", "비상 연락이 가능한 보호자 연락처"],
        "korean_expressions": {
            "office": "응급 상황입니다. 빨리 의사 선생님을 만나게 해주세요.",
            "phone": "지금 응급실에 가려고 하는데 바로 접수와 진료가 가능한가요?",
            "message": "환자가 심하게 아파서 응급 처치가 필요합니다. 안내를 부탁드립니다.",
        },
    },
    SUB_GENERAL_HOSPITAL: {
        "action_plan": {
            "first_checks": [
                "열, 기침, 통증 등 주요 증상이 언제부터 시작되었는지 정리해주세요.",
                "평일 주간 운영 시간 내에 방문할 수 있는 동네 의원이나 약국을 검색하세요.",
            ],
            "todo_steps": [
                "방문하려는 의료기관의 평일 진료 시간과 점심시간을 확인하세요.",
                "접수를 위해 신분증과 건강보험 자격 상태를 미리 점검하세요.",
                "의사에게 증상을 명확하게 설명할 수 있도록 간단히 메모하세요.",
            ],
            "visit_or_online": [
                "의원에 도착하면 원무과 접수처에 신분증을 제출하고 진료를 대기하세요.",
                "진료가 끝나면 수납 후 처방전을 받아 인근 약국으로 이동하세요.",
            ],
            "after_checks": [
                "약사에게 약의 하루 복용 횟수와 식전, 식후 복용 방법을 정확히 확인하세요.",
                "처방받은 약의 부작용이나 주의해야 할 음식 제약이 있는지 체크하세요.",
            ],
        },
        "checklist": ["외국인등록증 또는 여권", "국민건강보험 자격 확인 자료", "겪고 있는 증상 및 아픈 부위 메모", "기존에 복용하던 약 목록"],
        "korean_expressions": {
            "office": "진료 접수를 하고 싶습니다. 처음 왔습니다.",
            "phone": "안녕하세요. 오늘 평일 일반 진료가 가능한 시간과 예약 필요 여부를 여쭤봅니다.",
            "message": "평일 주간 진료 시간표와 필요한 지참 서류를 안내해주세요.",
        },
    },
    SUB_ADMIN_INSURANCE: {
        "action_plan": {
            "first_checks": [
                "국민건강보험 고지서의 납부 기한과 청구 금액을 정확히 확인해주세요.",
                "장기 체류 외국인으로서 건강보험 가입 자격이 정상 유지되고 있는지 보세요.",
            ],
            "todo_steps": [
                "건강보험 자격이나 보험료 체납 조회를 위해 국민건강보험공단 고객센터 번호를 확인하세요.",
                "보건소의 무료 예방접종이나 검사 프로그램을 이용할 수 있는지 대상을 조회하세요.",
                "가족 합가 신청이나 주소 변경에 필요한 증빙 서류를 수집하세요.",
            ],
            "visit_or_online": [
                "공단 지사 또는 보건소 방문 시 필요한 외국인등록증과 증빙 서류를 지참하세요.",
                "정부 가동 온라인 포털을 통해 모바일이나 PC로 신청 가능한지 확인하세요.",
            ],
            "after_checks": [
                "보험료 자동이체 신청이 정상적으로 처리되었는지 내역을 확인하세요.",
                "제출한 서류에 심사 반려나 보완 요청 사유가 없는지 다시 체크하세요.",
            ],
        },
        "checklist": ["외국인등록증 또는 여권", "국민건강보험 고지서 또는 안내문", "가족관계증명서 등 체류 자격 증빙 서류", "보건소 방문 목적 확인 서류"],
        "korean_expressions": {
            "office": "외국인 건강보험 자격 가입과 고지서 내역을 확인하러 왔습니다.",
            "phone": "안녕하세요. 건강보험료 청구 금액과 납부 기한 연장에 대해 문의드립니다.",
            "message": "외국인 건강보험 가입 절차와 보건소 혜택 안내문을 보내주세요.",
        },
    },
    SUB_DENTAL: {
        "action_plan": {
            "first_checks": [
                "치통이 발생한 정확한 위치와 붓기 상태를 확인해주세요.",
                "치과는 비급여 항목이 많으므로 대략적인 비용 예산을 고려하세요.",
            ],
            "todo_steps": [
                "예약제로 운영되는 치과가 많으므로 인근 치과의원에 전화를 걸어 예약 일정을 잡으세요.",
                "치과 진료 시 건강보험이 적용되는 급여 항목이 무엇인지 미리 파악하세요.",
            ],
            "visit_or_online": [
                "예약 시간에 맞춰 치과에 방문하여 문진표를 작성하고 대기하세요.",
                "치료 전 의사에게 통증의 강도와 진행 상황을 설명하세요.",
            ],
            "after_checks": [
                "치과 치료 후 처방된 소염진통제의 복용법을 약국에서 확인하세요.",
                "치료 부위의 소독이나 실밥 제거를 위한 다음 내원 일정을 체크하세요.",
            ],
        },
        "checklist": ["외국인등록증 또는 여권", "치과 예약 확인 내역", "치통 발생 시점 및 증상 기록"],
        "korean_expressions": {
            "office": "이가 너무 아파서 치료를 받고 싶습니다. 예약했습니다.",
            "phone": "안녕하세요. 치통이 심한데 오늘 치료나 예약이 가능한 시간이 있을까요?",
            "message": "치과 진료 예약 일정과 대략적인 초진 준비물을 안내해주세요.",
        },
    },
    SUB_MISC: {
        "action_plan": {
            "first_checks": [
                "질문하신 의료 상황과 관련된 공식 지침이나 가이드라인을 먼저 조회하세요.",
            ],
            "todo_steps": [
                "해당 의료 목적에 맞는 전문 의료기관 종류와 방문 절차를 확인하세요.",
                "본인의 체류 자격 조건에 따라 준비해야 할 의료 서류들을 정리하세요.",
            ],
            "visit_or_online": [
                "직접 방문이 요구되는 경우 관할 보건소나 기관의 위치를 파악하세요.",
            ],
            "after_checks": [
                "상담이나 진료 완료 후 추가 서류 제출 또는 추적 관찰이 필요한지 점검하세요.",
            ],
        },
        "checklist": ["외국인등록증 또는 여권", "기초 신분 확인 증명 서류", "해당 의료 행위 관련 안내문"],
        "korean_expressions": {
            "office": "이 의료 절차를 진행하려면 어디로 가서 확인해야 합니까?",
            "phone": "안녕하세요. 해당 의료 지원 프로그램의 조건과 절차를 문의하고자 합니다.",
            "message": "관련 의료 절차의 준비물 목록과 안내 서식을 송부해주세요.",
        },
    },
}


def get_fallback_bundle(sub_category: str) -> dict[str, object]:
    return FALLBACK_BUNDLES.get(sub_category, FALLBACK_BUNDLES[SUB_MISC])


def get_primary_source(sub_category: str) -> str | None:
    return PRIMARY_SOURCE_BY_SUBCATEGORY.get(sub_category)

def format_context(docs: list[Document]) -> str:
    if not docs:
        return (
            "관련 문서를 찾지 못했습니다. 공식 안내를 확인해야 한다는 전제로만 "
            "조심스럽게 안내해주세요."
        )

    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        sub_category = doc.metadata.get("sub_category", "unknown")
        parts.append(
            f"[source={source} | sub_category={sub_category}]\n{doc.page_content}"
        )
    return "\n\n".join(parts)


def merge_medical_warnings(extra_warnings: list[str]) -> list[str]:
    warnings = list(DEFAULT_WARNINGS)
    for warning in extra_warnings:
        if warning not in warnings:
            warnings.append(warning)
    return warnings


def format_medical_checklist(items: list[str]) -> str:
    normalized_items = [str(item).strip() for item in items if str(item).strip()]
    return "  \n".join(f"□ {item}" for item in normalized_items)


def build_final_answer(
    sub_category: str,
    action_plan: dict[str, list[str]],
    checklist: list[str],
    korean_expressions: dict[str, str],
    warnings: list[str],
    sources: list[str],
) -> str:
    checklist_section = format_medical_checklist(checklist)
    sections = [
        "## 상황 분류",
        f"의료 / {sub_category}",
        "",
        "## 먼저 확인할 것",
        format_bullets(action_plan.get("first_checks", [])),
        "",
        "## 해야 할 일",
        format_numbered(action_plan.get("todo_steps", [])),
        "",
        "## 방문/온라인 확인",
        format_bullets(action_plan.get("visit_or_online", [])),
        "",
        "## 처리 후 확인할 것",
        format_bullets(action_plan.get("after_checks", [])),
        "",
    ]

    if checklist_section:
        sections.extend(
            [
                "## 준비물 체크리스트",
                checklist_section,
                "",
            ]
        )

    sections.extend(
        [
            "## 기관에서 사용할 한국어",
            f'- 기관에서 말할 문장:\n  "{korean_expressions.get("office", "")}"',
            f'- 전화로 물어볼 문장:\n  "{korean_expressions.get("phone", "")}"',
            f'- 문자/이메일 문장:\n  "{korean_expressions.get("message", "")}"',
            "",
            "## 주의사항",
            format_bullets(warnings),
            "",
            "## 참고 문서",
            format_sources(sources),
        ]
    )

    return "\n".join(
        sections
    )
