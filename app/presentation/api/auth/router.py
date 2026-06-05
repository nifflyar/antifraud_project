from fastapi import APIRouter, Request, Response, status, HTTPException
from dishka.integrations.fastapi import FromDishka, inject

from app.application.auth.login import LoginInputDTO, LoginInteractor
from app.application.auth.logout import LogoutInputDTO, LogoutInteractor
from app.application.auth.refresh import RefreshInputDTO, RefreshInteractor
from app.application.auth.register import RegisterInputDTO, RegisterInteractor
from app.application.common.transaction import TransactionManager
from app.application.services.audit import AuditService
from app.domain.user.vo import UserId
from app.infrastructure.config import Config
from app.presentation.api.security import (
    get_optional_auth_claims_from_request,
    require_admin_claims_for_optional_auth,
    require_refresh_token_from_request,
    get_optional_refresh_token_from_request,
    set_refresh_cookie,
    set_access_token_cookie,
    clear_auth_cookies,
    create_access_token,
)

from .schemas import (
    LoginRequest,
    RegisterRequest,
    SuccessResponse,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=SuccessResponse, status_code=201)
@inject
async def register_user_handler(
    request: Request,
    data: RegisterRequest,
    interactor: FromDishka[RegisterInteractor],
    config: FromDishka[Config],
    audit_service: FromDishka[AuditService],
    transaction_manager: FromDishka[TransactionManager],
) -> SuccessResponse:
    """Register a new user account"""
    claims = require_admin_claims_for_optional_auth(request, config)
    actor_user_id = claims.user_id if claims is not None else None

    register_result = await interactor(
        RegisterInputDTO(
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            actor_user_id=actor_user_id,
            is_admin=data.is_admin,
        )
    )

    # Audit log: User registration
    creator_id = claims.user_id if claims else None
    await audit_service.log_action(
        action="USER_REGISTERED",
        entity_type="user",
        entity_id=register_result.email,
        user_id=creator_id,
        meta={"email": register_result.email, "is_admin": data.is_admin},
    )
    await transaction_manager.commit()

    return SuccessResponse(success=True)


@router.post("/login", response_model=SuccessResponse)
@inject
async def login_user_handler(
    data: LoginRequest,
    interactor: FromDishka[LoginInteractor],
    config: FromDishka[Config],
    audit_service: FromDishka[AuditService],
    transaction_manager: FromDishka[TransactionManager],
) -> Response:
    """Authenticate user and set JWT cookies"""
    login_result = await interactor(
        LoginInputDTO(
            email=data.email,
            password=data.password,
        )
    )

    # Audit log: User login
    user_id = UserId(login_result.user_id)
    await audit_service.log_login(user_id)
    await transaction_manager.commit()

    access_token = create_access_token(
        user_id=user_id,
        is_admin=login_result.is_admin,
        config=config,
    )
    refresh_token = login_result.refresh_token

    response = Response(
        content='{"success": true}',
        status_code=status.HTTP_200_OK,
        media_type="application/json",
    )

    response = set_access_token_cookie(response, access_token, config)
    response = set_refresh_cookie(response, refresh_token, config)

    return response


@router.post("/refresh", response_model=SuccessResponse)
@inject
async def refresh_user_handler(
    request: Request,
    interactor: FromDishka[RefreshInteractor],
    config: FromDishka[Config],
) -> Response:
    """Refresh access token using refresh token"""
    refresh_token = require_refresh_token_from_request(request)

    refresh_result = await interactor(
        RefreshInputDTO(
            refresh_token=refresh_token,
        )
    )

    access_token = create_access_token(
        user_id=UserId(refresh_result.user_id),
        is_admin=refresh_result.is_admin,
        config=config,
    )

    response = Response(
        content='{"success": true}',
        status_code=status.HTTP_200_OK,
        media_type="application/json",
    )

    response = set_access_token_cookie(response, access_token, config)

    return response


@router.post("/logout", response_model=SuccessResponse)
@inject
async def logout_user_handler(
    request: Request,
    interactor: FromDishka[LogoutInteractor],
    audit_service: FromDishka[AuditService],
    transaction_manager: FromDishka[TransactionManager],
    config: FromDishka[Config],
) -> Response:
    """Logout user and clear auth cookies"""
    # Check authentication
    claims = get_optional_auth_claims_from_request(request, config)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    refresh_token = get_optional_refresh_token_from_request(request)

    await interactor(
        LogoutInputDTO(
            refresh_token=refresh_token,
        )
    )

    # Audit log: User logout
    await audit_service.log_logout(claims.user_id)
    await transaction_manager.commit()

    response = Response(
        content='{"success": true}',
        status_code=status.HTTP_200_OK,
        media_type="application/json",
    )
    response = clear_auth_cookies(response)

    return response


auth_router = router
