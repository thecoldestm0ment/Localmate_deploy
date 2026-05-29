from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryResult:
    answer: str
    category: str | None = None
    sub_category: str | None = None
    sources: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    needs_clarification: bool = False
    clarifying_question: str | None = None

    @classmethod
    def success(
        cls,
        answer: str,
        category: str,
        sub_category: str | None = None,
        sources: tuple[str, ...] | list[str] = (),
        warnings: tuple[str, ...] | list[str] = (),
    ) -> "CategoryResult":
        return cls(
            answer=answer,
            category=category,
            sub_category=sub_category,
            sources=tuple(sources),
            warnings=tuple(warnings),
        )

    @classmethod
    def clarification(
        cls,
        question: str,
        category: str | None = None,
        sub_category: str | None = None,
        warnings: tuple[str, ...] | list[str] = (),
    ) -> "CategoryResult":
        return cls(
            answer=question,
            category=category,
            sub_category=sub_category,
            warnings=tuple(warnings),
            needs_clarification=True,
            clarifying_question=question,
        )
