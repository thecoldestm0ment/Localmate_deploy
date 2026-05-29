from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryResult:
    answer: str
    category: str | None = None
    needs_clarification: bool = False
    clarifying_question: str | None = None

    @classmethod
    def success(cls, answer: str, category: str) -> "CategoryResult":
        return cls(answer=answer, category=category)

    @classmethod
    def clarification(
        cls,
        question: str,
        category: str | None = None,
    ) -> "CategoryResult":
        return cls(
            answer=question,
            category=category,
            needs_clarification=True,
            clarifying_question=question,
        )
