"""HTTP-layer exceptions. Handlers live in app.core.errors."""

from __future__ import annotations


class AppError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str = "error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str, *, code: str = "not_found") -> None:
        super().__init__(message, status_code=404, code=code)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required", *, code: str = "unauthenticated") -> None:
        super().__init__(message, status_code=401, code=code)


class ConflictError(AppError):
    def __init__(self, message: str, *, code: str = "conflict") -> None:
        super().__init__(message, status_code=409, code=code)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Not allowed to access this resource", *, code: str = "forbidden") -> None:
        super().__init__(message, status_code=403, code=code)


class UnprocessableError(AppError):
    def __init__(self, message: str, *, code: str = "unprocessable") -> None:
        super().__init__(message, status_code=422, code=code)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str, *, code: str = "unavailable") -> None:
        super().__init__(message, status_code=503, code=code)
