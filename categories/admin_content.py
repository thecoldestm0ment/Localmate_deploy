from langchain_core.documents import Document

from categories.response_format import (
    format_bullets,
    format_checkboxes,
    format_numbered,
    format_sources,
)
from categories.admin_rules import (
    SUB_ADDRESS_CHANGE,
    SUB_ALIEN_CARD_LOSS,
    SUB_MISC,
    SUB_VISA,
    SUB_VISIT,
)

PRIMARY_SOURCE_BY_SUBCATEGORY = {
    SUB_ALIEN_CARD_LOSS: "admin/admin_alien_card_loss.md",
    SUB_ADDRESS_CHANGE: "admin/admin_address_change.md",
    SUB_VISA: "admin/admin_visa_extension.md",
}

DEFAULT_WARNINGS = [
    "체류자격과 개인 상황에 따라 절차가 달라질 수 있습니다.",
    "방문 전 공식 안내를 꼭 확인해주세요.",
    "긴급하거나 법적 문제가 있으면 담당 기관에 직접 문의해주세요.",
]

FALLBACK_BUNDLES: dict[str, dict[str, object]] = {
    SUB_ALIEN_CARD_LOSS: {
        "action_plan": {
            "first_checks": [
                "외국인등록증을 마지막으로 본 장소와 시간을 다시 확인해주세요.",
                "단순 분실인지 도난인지 먼저 정리해주세요.",
            ],
            "todo_steps": [
                "출입국·외국인 관련 공식 안내에서 분실 신고나 재발급 절차를 확인해주세요.",
                "방문 예약이 필요한지 먼저 확인해주세요.",
                "여권, 사진, 본인 확인 자료를 준비해주세요.",
            ],
            "visit_or_online": [
                "공식 안내에서 온라인 신청 가능 여부와 방문 필요 여부를 확인해주세요.",
                "관할 기관과 준비물 목록을 다시 확인해주세요.",
            ],
            "after_checks": [
                "접수 후 새 등록증 수령 방법을 확인해주세요.",
                "추가 서류 요청이 있는지 다시 확인해주세요.",
            ],
        },
        "checklist": [
            "여권",
            "외국인등록 관련 본인 확인 자료",
            "증명사진",
            "분실 경위 메모",
            "방문 예약 확인 내역",
        ],
        "korean_expressions": {
            "office": "외국인등록증을 잃어버렸어요. 어떻게 하면 될까요?",
            "phone": "안녕하세요. 외국인등록증 분실 후 절차를 문의드리고 싶습니다.",
            "message": "외국인등록증 분실 후 준비물과 절차를 안내해주세요.",
        },
    },
    SUB_ADDRESS_CHANGE: {
        "action_plan": {
            "first_checks": [
                "이사한 날짜와 새 주소를 정확하게 확인해주세요.",
                "주소 변경 신고 대상인지 공식 안내를 먼저 확인해주세요.",
            ],
            "todo_steps": [
                "관할 기관과 신고 기한을 확인해주세요.",
                "온라인 신고 가능 여부와 방문 예약 필요 여부를 확인해주세요.",
                "여권과 거주지 확인 서류를 준비해주세요.",
            ],
            "visit_or_online": [
                "공식 안내에서 온라인 신청 가능 여부를 확인해주세요.",
                "직접 방문이 필요하면 예약이 가능한지 먼저 확인해주세요.",
            ],
            "after_checks": [
                "주소 정보가 정상 반영되었는지 확인해주세요.",
                "추가 제출 요청이 있는지 다시 확인해주세요.",
            ],
        },
        "checklist": [
            "여권",
            "외국인등록 관련 신분 확인 자료",
            "새 주소 확인 서류",
            "거주 확인 자료",
            "방문 예약 확인 내역",
        ],
        "korean_expressions": {
            "office": "이사해서 주소 변경 신고가 필요한지 확인하고 싶어요.",
            "phone": "안녕하세요. 이사 후 주소 변경 신고 방법을 문의드리고 싶습니다.",
            "message": "주소 변경 신고 방법과 준비물을 알려주세요.",
        },
    },
    SUB_VISA: {
        "action_plan": {
            "first_checks": [
                "현재 비자 종류와 체류기간 만료일을 확인해주세요.",
                "체류자격과 개인 상황에 따라 절차가 달라질 수 있는지 먼저 생각해보세요.",
            ],
            "todo_steps": [
                "공식 안내에서 체류기간 연장이나 비자 관련 절차를 확인해주세요.",
                "관할 출입국·외국인청 방문 예약 필요 여부를 확인해주세요.",
                "여권과 체류 관련 서류를 준비해주세요.",
            ],
            "visit_or_online": [
                "공식 채널에서 온라인 신청 가능 여부를 확인해주세요.",
                "방문이 필요하면 관할 기관과 준비물 목록을 다시 확인해주세요.",
            ],
            "after_checks": [
                "접수 상태와 추가 서류 요청 여부를 확인해주세요.",
                "처리 일정은 공식 안내에서 다시 확인해주세요.",
            ],
        },
        "checklist": [
            "여권",
            "외국인등록 관련 신분 확인 자료",
            "현재 체류자격 확인 자료",
            "체류기간 만료일 확인 자료",
            "상황별 추가 서류",
            "방문 예약 확인 내역",
        ],
        "korean_expressions": {
            "office": "비자 기간이 곧 끝나서 체류기간 연장 방법을 확인하고 싶어요.",
            "phone": "안녕하세요. 체류기간 만료 전에 확인해야 할 절차를 문의드리고 싶습니다.",
            "message": "체류기간 연장 관련 준비물과 절차를 안내해주세요.",
        },
    },
    SUB_VISIT: {
        "action_plan": {
            "first_checks": [
                "어느 기관을 방문해야 하는지 먼저 확인해주세요.",
                "예약이 필요한지 공식 안내를 확인해주세요.",
            ],
            "todo_steps": [
                "방문 목적에 맞는 기관인지 확인해주세요.",
                "예약 방법과 준비물을 확인해주세요.",
                "필요한 신분 확인 자료를 준비해주세요.",
            ],
            "visit_or_online": [
                "온라인 예약이 가능한지 확인해주세요.",
                "방문 시간이 정해져 있는지 확인해주세요.",
            ],
            "after_checks": [
                "예약 내용과 방문 시간을 다시 확인해주세요.",
                "추가로 가져가야 하는 서류가 있는지 확인해주세요.",
            ],
        },
        "checklist": [
            "여권",
            "방문 목적 관련 안내 내용",
            "예약 확인 내역",
            "본인 확인 자료",
        ],
        "korean_expressions": {
            "office": "방문 예약이 필요한지 확인하고 싶어요.",
            "phone": "안녕하세요. 기관 방문 예약 방법을 문의드리고 싶습니다.",
            "message": "방문 예약과 준비물을 안내해주세요.",
        },
    },
    SUB_MISC: {
        "action_plan": {
            "first_checks": [
                "질문과 관련된 공식 안내를 먼저 확인해주세요.",
            ],
            "todo_steps": [
                "필요한 기관과 절차를 확인해주세요.",
                "본인 상황에 맞는 준비물을 정리해주세요.",
            ],
            "visit_or_online": [
                "방문 또는 온라인 처리 가능 여부를 공식 안내에서 확인해주세요.",
            ],
            "after_checks": [
                "처리 후 추가 확인이 필요한지 다시 살펴보세요.",
            ],
        },
        "checklist": [
            "여권",
            "본인 확인 자료",
            "방문 또는 신청 관련 안내 내용",
        ],
        "korean_expressions": {
            "office": "이 절차를 어떻게 확인하면 될까요?",
            "phone": "안녕하세요. 관련 절차를 문의드리고 싶습니다.",
            "message": "준비물과 절차를 안내해주세요.",
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


def merge_admin_warnings(extra_warnings: list[str]) -> list[str]:
    warnings = list(DEFAULT_WARNINGS)
    for warning in extra_warnings:
        if warning not in warnings:
            warnings.append(warning)
    return warnings


def build_final_answer(
    sub_category: str,
    action_plan: dict[str, list[str]],
    checklist: list[str],
    korean_expressions: dict[str, str],
    warnings: list[str],
    sources: list[str],
) -> str:
    return "\n".join(
        [
            "## 상황 분류",
            f"행정 / {sub_category}",
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
            "## 준비물 체크리스트",
            format_checkboxes(checklist),
            "",
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
