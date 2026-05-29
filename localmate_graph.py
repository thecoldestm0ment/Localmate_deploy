from categories import CATEGORY_HANDLERS
from categories.types import CategoryResult

TOP_LEVEL_CLARIFICATION_QUESTION = "행정, 의료, 교통 중 어떤 도움이 필요한지 조금 더 알려주세요."


def run_localmate_result(user_input: str) -> CategoryResult:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    matching_handlers = [handler for handler in CATEGORY_HANDLERS if handler.can_handle(cleaned_input)]

    if not matching_handlers:
        return CategoryResult.clarification(TOP_LEVEL_CLARIFICATION_QUESTION)

    if len(matching_handlers) == 1:
        return matching_handlers[0].run_category(cleaned_input)

    traffic_handler = next(
        (handler for handler in matching_handlers if getattr(handler, "CATEGORY_NAME", "") == "traffic"),
        None,
    )
    if traffic_handler is not None:
        return traffic_handler.run_category(cleaned_input)

    return CategoryResult.clarification(TOP_LEVEL_CLARIFICATION_QUESTION)


def run_localmate(user_input: str) -> str:
    return run_localmate_result(user_input).answer


def main() -> None:
    default_question = "외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?"

    try:
        user_input = input("질문을 입력해주세요. 빈 입력이면 예시 질문을 사용합니다: ").strip()
    except EOFError:
        user_input = ""

    if not user_input:
        user_input = default_question

    print(run_localmate(user_input))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)
