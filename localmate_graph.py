from categories import CATEGORY_REGISTRY, CategoryHandlerSpec
from categories.types import CategoryResult

DEFAULT_QUESTION = "외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?"
TOP_LEVEL_CLARIFICATION_QUESTION = (
    "행정, 의료, 교통 중 어떤 도움이 필요한지 조금 더 알려주세요."
)


def get_matching_handlers(user_input: str) -> list[CategoryHandlerSpec]:
    return [
        spec
        for spec in CATEGORY_REGISTRY
        if spec.module.can_handle(user_input)
    ]


def pick_handler(
    matching_handlers: list[CategoryHandlerSpec],
) -> CategoryHandlerSpec | None:
    if not matching_handlers:
        return None

    return max(
        matching_handlers,
        key=lambda spec: spec.priority,
    )


def run_localmate_result(user_input: str) -> CategoryResult:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    matching_handlers = get_matching_handlers(cleaned_input)
    selected_handler = pick_handler(matching_handlers)
    if selected_handler is None:
        return CategoryResult.clarification(TOP_LEVEL_CLARIFICATION_QUESTION)

    return selected_handler.module.run_category(cleaned_input)


def run_localmate(user_input: str) -> str:
    return run_localmate_result(user_input).answer


def main() -> None:
    try:
        user_input = input(
            "질문을 입력해주세요. 빈 입력이면 예시 질문을 사용합니다: "
        ).strip()
    except EOFError:
        user_input = ""

    if not user_input:
        user_input = DEFAULT_QUESTION

    print(run_localmate(user_input))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)
