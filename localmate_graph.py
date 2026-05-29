from categories import CATEGORY_HANDLERS
from categories.types import CategoryResult

DEFAULT_QUESTION = "외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?"
TRAFFIC_HANDLER_NAME = "traffic"
TOP_LEVEL_CLARIFICATION_QUESTION = "행정, 의료, 교통 중 어떤 도움이 필요한지 조금 더 알려주세요."


def get_matching_handlers(user_input: str) -> list[object]:
    return [
        handler
        for handler in CATEGORY_HANDLERS
        if handler.can_handle(user_input)
    ]


def pick_handler(handlers: list[object]):
    if len(handlers) == 1:
        return handlers[0]

    return next(
        (
            handler
            for handler in handlers
            if getattr(handler, "CATEGORY_NAME", "") == TRAFFIC_HANDLER_NAME
        ),
        None,
    )


def run_localmate_result(user_input: str) -> CategoryResult:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    matching_handlers = get_matching_handlers(cleaned_input)

    if not matching_handlers:
        return CategoryResult.clarification(TOP_LEVEL_CLARIFICATION_QUESTION)

    selected_handler = pick_handler(matching_handlers)
    if selected_handler is not None:
        return selected_handler.run_category(cleaned_input)

    return CategoryResult.clarification(TOP_LEVEL_CLARIFICATION_QUESTION)


def run_localmate(user_input: str) -> str:
    return run_localmate_result(user_input).answer


def main() -> None:
    try:
        user_input = input("질문을 입력해주세요. 빈 입력이면 예시 질문을 사용합니다: ").strip()
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
