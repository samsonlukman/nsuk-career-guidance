"""Errors raised by the recommendation package."""


class AssessmentError(ValueError):
    """Invalid student assessment input."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
