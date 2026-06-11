from langchain_core.documents import Document

from categories.response_format import (
    format_bullets,
    format_numbered,
)
from categories.medical_rules import (
    NO_DOCS_WARNING,
    SUB_AMBIGUOUS,
    SUB_EMERGENCY,
    SUB_GENERAL_HOSPITAL,
    SUB_HEALTH_INSURANCE_BILL,
    SUB_MEDICAL_COST_INSURANCE,
    SUB_PUBLIC_HEALTH_VACCINATION,
)

from categories.medical_content_data import (
    EXPRESSION_HEADING_BY_SUBCATEGORY,
    FALLBACK_BUNDLES,
    INTRO_BY_SUBCATEGORY,
    PRIMARY_SOURCE_BY_SUBCATEGORY,
    WARNING_BY_SUBCATEGORY,
)


def get_fallback_bundle(sub_category: str) -> dict[str, object]:
    return FALLBACK_BUNDLES.get(sub_category, FALLBACK_BUNDLES[SUB_AMBIGUOUS])


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


def merge_medical_warnings(
    extra_warnings: list[str],
    sub_category: str,
    user_input: str,
) -> list[str]:
    warnings = list(WARNING_BY_SUBCATEGORY.get(sub_category, WARNING_BY_SUBCATEGORY[SUB_AMBIGUOUS]))
    for warning in extra_warnings:
        if not warning or is_no_docs_warning(warning):
            continue
        if warning not in warnings:
            warnings.append(warning)
    return warnings


def is_no_docs_warning(warning: str) -> bool:
    return warning == NO_DOCS_WARNING or "관련 문서를 충분히 찾지 못했습니다" in warning


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
    del sources  # Sources stay in CategoryResult, but final_answer does not print them.

    checklist_section = format_medical_checklist(checklist)
    expression_heading = EXPRESSION_HEADING_BY_SUBCATEGORY.get(
        sub_category,
        EXPRESSION_HEADING_BY_SUBCATEGORY[SUB_AMBIGUOUS],
    )

    sections = [
        INTRO_BY_SUBCATEGORY.get(sub_category, INTRO_BY_SUBCATEGORY[SUB_AMBIGUOUS]),
        "",
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
            f"## {expression_heading}",
            "아래 문장은 현장에서 직원에게 직접 말하거나 보여주면 됩니다. (You can say or show the sentences below to staff on site.)",
            f'- 기관에서 말할 문장:\n  "{korean_expressions.get("office", "")}"',
            f'- 전화로 물어볼 문장:\n  "{korean_expressions.get("phone", "")}"',
            f'- 문자/이메일 문장:\n  "{korean_expressions.get("message", "")}"',
            "",
            "## 주의사항",
            format_bullets(warnings),
        ]
    )

    return "\n".join(sections)
