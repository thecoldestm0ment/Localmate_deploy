from langchain_core.documents import Document

from categories.response_format import (
    format_bullets,
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

from categories.admin_content_data import (
    EXPIRED_VISA_INTRO,
    EXPIRED_VISA_WARNINGS,
    FALLBACK_BUNDLES,
    INTRO_BY_SUBCATEGORY,
    PRIMARY_SOURCE_BY_SUBCATEGORY,
    WARNING_BY_SUBCATEGORY,
)


def get_fallback_bundle(sub_category: str) -> dict[str, object]:
    return FALLBACK_BUNDLES.get(sub_category, FALLBACK_BUNDLES[SUB_MISC])


def get_primary_source(sub_category: str) -> str | None:
    return PRIMARY_SOURCE_BY_SUBCATEGORY.get(sub_category)


def format_context(docs: list[Document]) -> str:
    if not docs:
        return (
            "관련 문서를 찾지 못했습니다. 절차를 단정하지 말고, 공식 안내 확인이 필요하다는 점을 "
            "자연스럽게 안내해 주세요."
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
    warnings: list[str] = []
    for warning in extra_warnings:
        if warning not in warnings:
            warnings.append(warning)
    return warnings


def build_final_answer(
    sub_category: str,
    is_expired_visa: bool,
    action_plan: dict[str, list[str]],
    checklist: list[str],
    korean_expressions: dict[str, str],
    warnings: list[str],
    sources: list[str],
) -> str:
    bundle = get_fallback_bundle(sub_category)
    curated_plan = bundle["action_plan"]
    curated_checklist = bundle["checklist"]
    curated_expressions = bundle["korean_expressions"]
    intro = EXPIRED_VISA_INTRO if is_expired_visa else INTRO_BY_SUBCATEGORY.get(
        sub_category,
        INTRO_BY_SUBCATEGORY[SUB_MISC],
    )
    final_warnings = build_warnings(sub_category, is_expired_visa, warnings)
    final_sources = prioritize_sources(sub_category, sources)
    checklist_section = format_admin_checkboxes(curated_checklist or checklist)

    sections = [
        intro,
        "## 상황 분류\n"
        f"행정 / {sub_category}",
        "## 지금 해야 할 일\n"
        f"{format_numbered(curated_plan.get('todo_steps', action_plan.get('todo_steps', [])))}",
    ]

    if checklist_section:
        sections.append(
            "## 준비물 체크리스트\n"
            f"{checklist_section}"
        )

    sections.extend(
        [
            "## 기관 직원에게 말하거나 보여줄 문장\n"
            "아래 문장은 출입국외국인청, 주민센터, 상담 창구 직원에게 직접 말하거나 보여주면 됩니다.  \n"
            "(You can say or show the following sentences to staff at the immigration office, community center, or consultation desk.)\n\n"
            f"{format_bullets(list((curated_expressions or korean_expressions).values()))}",
            "## 방문/온라인 확인\n"
            f"{format_bullets(curated_plan.get('visit_or_online', action_plan.get('visit_or_online', [])))}",
            "## 처리 후 확인할 것\n"
            f"{format_bullets(curated_plan.get('after_checks', action_plan.get('after_checks', [])))}",
            "## 주의사항\n"
            f"{format_bullets(final_warnings)}",
            "## 참고 문서\n"
            f"{format_sources(final_sources)}",
        ]
    )

    return "\n\n".join(sections).strip()


def build_warnings(
    sub_category: str,
    is_expired_visa: bool,
    extra_warnings: list[str],
) -> list[str]:
    warnings = (
        list(EXPIRED_VISA_WARNINGS)
        if is_expired_visa
        else list(WARNING_BY_SUBCATEGORY.get(sub_category, WARNING_BY_SUBCATEGORY[SUB_MISC]))
    )
    for warning in extra_warnings:
        if warning and warning not in warnings and "관련 문서를 충분히 찾지 못했습니다" not in warning:
            warnings.append(warning)
    return warnings


def format_admin_checkboxes(items: list[str]) -> str:
    if not items:
        return ""
    return "  \n".join(f"□ {item}" for item in items)


def prioritize_sources(sub_category: str, sources: list[str]) -> list[str]:
    primary_source = get_primary_source(sub_category)
    prioritized: list[str] = []
    if primary_source:
        prioritized.append(primary_source)

    for source in sources:
        if source == primary_source:
            continue
        if not is_relevant_source(sub_category, source):
            continue
        if source not in prioritized:
            prioritized.append(source)
        if len(prioritized) >= 2:
            break

    return prioritized


def is_relevant_source(sub_category: str, source: str) -> bool:
    expected = get_primary_source(sub_category)
    if expected:
        return source == expected
    return source.startswith("admin/")
