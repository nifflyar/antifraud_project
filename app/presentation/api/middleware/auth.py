from dataclasses import dataclass
from typing import Optional

from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.infrastructure.config import Config
from app.domain.user.vo import UserId


@dataclass
class AuthClaims:
    """Authentication claims from JWT token"""
    user_id: UserId
    is_admin: bool
    role: str
    email: Optional[str] = None


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate JWT token from cookies"""

    def __init__(self, app, config: Config):
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next):
        # Extract token from cookies
        token = request.cookies.get("access_jwt")

        if token:
            try:
                # Decode token
                payload = jwt.decode(
                    token,
                    self.config.auth.secret_key.get_secret_value(),
                    algorithms=[self.config.auth.algorithm],
                )

                # Extract claims
                user_id_raw = payload.get("sub")
                is_admin = payload.get("is_admin", False)
                email = payload.get("email")

                # Determine role based on is_admin flag and other claims
                role = "admin" if is_admin else "analyst"

                if user_id_raw:
                    claims = AuthClaims(
                        user_id=UserId(int(user_id_raw)),
                        is_admin=is_admin,
                        role=role,
                        email=email,
                    )
                    request.state.auth_claims = claims
                else:
                    request.state.auth_claims = None

            except (JWTError, ValueError, TypeError):
                # Invalid token or invalid user_id - don't set claims
                request.state.auth_claims = None
        else:
            request.state.auth_claims = None

        response = await call_next(request)
        return response
