from .guards import require_admin, require_security, require_analyst, RoleRequired
from .tokens import (
    get_optional_auth_claims_from_request,
    require_admin_claims_for_optional_auth,
    require_refresh_token_from_request,
    get_optional_refresh_token_from_request,
    set_refresh_cookie,
    set_access_token_cookie,
    clear_auth_cookies,
    create_access_token,
    AuthenticatedUserClaims,
)

__all__ = [
    # Guards
    "require_admin",
    "require_security",
    "require_analyst",
    "RoleRequired",
    # Tokens
    "get_optional_auth_claims_from_request",
    "require_admin_claims_for_optional_auth",
    "require_refresh_token_from_request",
    "get_optional_refresh_token_from_request",
    "set_refresh_cookie",
    "set_access_token_cookie",
    "clear_auth_cookies",
    "create_access_token",
    "AuthenticatedUserClaims",
]
