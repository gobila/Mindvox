from fastapi import HTTPException, Request, status

from settings import Settings


HTTPS_REQUIRED_DETAIL = "HTTPS is required for public deployment."


def require_secure_transport_for_public_request(
    *,
    request: Request,
    settings: Settings,
) -> None:
    if not settings.public_deployment:
        return

    if _request_uses_https(request):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=HTTPS_REQUIRED_DETAIL,
    )


def _request_uses_https(request: Request) -> bool:
    return request.url.scheme == "https"
