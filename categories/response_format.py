def format_bullets(
    items: list[str],
    empty_text: str = "- 확인이 필요한 정보가 있습니다.",
) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def format_numbered(
    items: list[str],
    empty_text: str = "1. 공식 안내를 먼저 확인해주세요.",
) -> str:
    if not items:
        return empty_text
    return "\n".join(
        f"{index}. {item}"
        for index, item in enumerate(items, start=1)
    )

def format_checkboxes(items: list[str]) -> str:
    if not items:
        return "- [ ] 준비물이 있는지 다시 확인하세요.  \n  (Check again whether any documents are required.)"
    return "\n".join(f"- [ ] {item}" for item in items)


def format_sources(
    items: list[str],
    empty_text: str = "- 관련 문서를 찾지 못했습니다.",
) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)
