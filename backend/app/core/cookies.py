"""httpOnly session cookie helpers. The JWT itself is not exposed to JavaScript."""

from __future__ import annotations

from fastapi import Response

from app.core.config import get_settings


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.auth_cookie_secure,
        max_age=settings.auth_token_minutes * 60,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(key=settings.auth_cookie_name, path="/")
