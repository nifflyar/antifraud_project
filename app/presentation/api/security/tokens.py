from dataclasses import dataclass
from datetime import timedelta, datetime, timezone
from typing import Any

from fastapi import Request, Response, HTTPException, status
from jose import JWTError, jwt

from app.application.common.exceptions import ValidationError
from app.domain.user.vo import UserId
from app.infrastructure.config import Config

ACCESS_COOKIE_KEY = "access_jwt"
REFRESH_COOKIE_KEY = "refresh_token"
JWT_AUTH_COOKIE_PATH = "/"
JWT_AUTH_COOKIE_SAMESITE = "lax"


@dataclass(frozen=True)
class AuthenticatedUserClaims:
    user_id: UserId
    is_admin: bool


def _user_id_from_subject(subject: str) -> UserId:
    try:
        return UserId(int(subject))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject"
        ) from exc


def decode_token(encoded_token: str, config: Config) -> dict[str, Any]:
    """Decode JWT token and return payload"""
    normalized_token = _normalize_encoded_token(encoded_token)
    try:
        payload = jwt.decode(
            normalized_token,
            config.auth.secret_key.get_secret_value(),
            algorithms=[config.auth.algorithm],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        ) from exc


def _normalize_encoded_token(encoded_token: str) -> str:
    """Extract token from Bearer scheme if present"""
    if encoded_token.startswith("Bearer "):
        bearer_token = encoded_token[7:]
        if not bearer_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return bearer_token
    return encoded_token


def decode_token_to_user_id(encoded_token: str, config: Config) -> UserId:
    """Decode token and extract user ID"""
    payload = decode_token(encoded_token, config)
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject"
        )
    return _user_id_from_subject(subject)


def decode_token_to_claims(encoded_token: str, config: Config) -> AuthenticatedUserClaims:
    """Decode token and extract authenticated user claims"""
    payload = decode_token(encoded_token, config)
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject"
        )
    is_admin = payload.get("is_admin")
    if not isinstance(is_admin, bool):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return AuthenticatedUserClaims(user_id=_user_id_from_subject(subject), is_admin=is_admin)


def create_access_token(user_id: UserId, is_admin: bool, config: Config) -> str:
    """Create a new access token"""
    expires_delta = timedelta(minutes=config.auth.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": str(user_id),
        "is_admin": is_admin,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        config.auth.secret_key.get_secret_value(),
        algorithm=config.auth.algorithm,
    )
    return encoded_jwt


def _extract_optional_cookie_token(request: Request, cookie_key: str) -> str | None:
    """Extract optional token from request cookies"""
    encoded_token = request.cookies.get(cookie_key)
    if encoded_token is None:
        return None
    if not encoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return encoded_token


def get_optional_auth_claims_from_request(
    request: Request, config: Config
) -> AuthenticatedUserClaims | None:
    """Extract optional authenticated user claims from request"""
    encoded_token = _extract_optional_cookie_token(request, ACCESS_COOKIE_KEY)
    if encoded_token is None:
        return None
    return decode_token_to_claims(encoded_token=encoded_token, config=config)


def require_admin_claims_for_optional_auth(
    request: Request, config: Config
) -> AuthenticatedUserClaims | None:
    """Get optional auth claims and verify admin access if authenticated"""
    claims = get_optional_auth_claims_from_request(request, config)
    if claims is not None and not claims.is_admin:
        raise ValidationError("Only admins can register users")
    return claims


def get_optional_refresh_token_from_request(request: Request) -> str | None:
    """Extract optional refresh token from request cookies"""
    return _extract_optional_cookie_token(request, REFRESH_COOKIE_KEY)


def require_refresh_token_from_request(request: Request) -> str:
    """Extract required refresh token from request cookies"""
    refresh_token = get_optional_refresh_token_from_request(request)
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found in request cookies"
        )
    return refresh_token


def set_refresh_cookie(response: Response, refresh_token: str, config: Config) -> Response:
    """Set refresh token cookie on response"""
    response.set_cookie(
        key=REFRESH_COOKIE_KEY,
        value=refresh_token,
        max_age=config.auth.refresh_token_expire_days * 24 * 60 * 60,
        path=JWT_AUTH_COOKIE_PATH,
        secure=config.environment == "production",
        httponly=True,
        samesite=JWT_AUTH_COOKIE_SAMESITE,
    )
    return response


def set_access_token_cookie(response: Response, access_token: str, config: Config) -> Response:
    """Set access token cookie on response"""
    response.set_cookie(
        key=ACCESS_COOKIE_KEY,
        value=access_token,
        max_age=config.auth.access_token_expire_minutes * 60,
        path=JWT_AUTH_COOKIE_PATH,
        secure=config.environment == "production",
        httponly=True,
        samesite=JWT_AUTH_COOKIE_SAMESITE,
    )
    return response


def clear_auth_cookies(response: Response) -> Response:
    """Clear authentication cookies from response"""
    response.delete_cookie(
        key=ACCESS_COOKIE_KEY,
        path=JWT_AUTH_COOKIE_PATH,
    )
    response.delete_cookie(
        key=REFRESH_COOKIE_KEY,
        path=JWT_AUTH_COOKIE_PATH,
    )
    return response
