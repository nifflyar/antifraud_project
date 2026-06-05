from functools import wraps
from typing import Callable, Any

from fastapi import HTTPException, status, Request
from app.domain.user.vo import UserRole


# DEPRECATED: These decorators are incompatible with current JWT implementation
# that only includes user_id and is_admin claims (no role field).
# Use manual auth checks in endpoint bodies instead:
#   claims = getattr(request.state, "auth_claims", None)
#   if not claims or not claims.is_admin:
#       raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="...")


class RoleRequired:
    """
    DEPRECATED: Do not use this decorator.

    JWT claims don't include role field. Use manual auth checks instead.
    """

    def __init__(self, required_roles: list[UserRole] | UserRole):
        """
        Args:
            required_roles: Single role or list of allowed roles
        """
        if isinstance(required_roles, UserRole):
            self.required_roles = [required_roles]
        else:
            self.required_roles = required_roles

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs) -> Any:
            # Get auth claims from request state
            claims = getattr(request.state, "auth_claims", None)
            if not claims:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )

            # Check user role - NOTE: role field doesn't exist in JWT
            # This decorator is deprecated
            user_role = getattr(claims, "role", None)
            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Role not found in token",
                )

            # Check if user role is in required roles
            if UserRole(user_role) not in self.required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {[r.value for r in self.required_roles]}",
                )

            return await func(request, *args, **kwargs)

        return wrapper


def require_admin(func: Callable) -> Callable:
    """
    DEPRECATED: Do not use this decorator.
    Use manual auth checks in endpoint bodies instead.
    """
    return RoleRequired(UserRole.ADMIN)(func)


def require_security(func: Callable) -> Callable:
    """
    DEPRECATED: Do not use this decorator.
    Use manual auth checks in endpoint bodies instead.
    """
    return RoleRequired([UserRole.SECURITY, UserRole.ADMIN])(func)


def require_analyst(func: Callable) -> Callable:
    """
    DEPRECATED: Do not use this decorator.
    Use manual auth checks in endpoint bodies instead.
    """
    return RoleRequired(
        [UserRole.ANALYST, UserRole.SECURITY, UserRole.ADMIN]
    )(func)
