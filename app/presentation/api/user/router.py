from fastapi import APIRouter, Request, HTTPException, status, Query
from pydantic import BaseModel
from dishka.integrations.fastapi import FromDishka, inject
import logging

from app.application.user.get_me import (
    GetUserProfileInputDTO,
    GetUserProfileInteractor,
    GetUserProfileOutputDTO,
)
from app.application.user.list_users import (
    ListUsersInteractor,
    ListUsersInputDTO,
    ListUsersOutputDTO,
)
from app.application.user.get_user_by_id import (
    GetUserByIdInteractor,
    GetUserByIdInputDTO,
    GetUserByIdOutputDTO,
)
from app.application.user.update_user import (
    UpdateUserInteractor,
    UpdateUserInputDTO,
    UpdateUserOutputDTO,
)
from app.application.user.delete_user import (
    DeleteUserInteractor,
    DeleteUserInputDTO,
)
from app.application.common.transaction import TransactionManager
from app.application.common.exceptions import ValidationError
from app.domain.user.vo import UserId
from app.infrastructure.config import Config
from app.presentation.api.security import (
    get_optional_auth_claims_from_request,
)

logger = logging.getLogger(__name__)


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    is_admin: bool | None = None


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=GetUserProfileOutputDTO)
@inject
async def get_user_profile(
    request: Request,
    interactor: FromDishka[GetUserProfileInteractor],
    config: FromDishka[Config],
) -> GetUserProfileOutputDTO:
    """Get the authenticated user's profile."""
    claims = get_optional_auth_claims_from_request(request, config)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    response = await interactor(data=GetUserProfileInputDTO(user_id=claims.user_id))
    return response


@router.get("", response_model=ListUsersOutputDTO)
@inject
async def list_users(
    request: Request,
    config: FromDishka[Config],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    interactor: FromDishka[ListUsersInteractor] = None,
) -> ListUsersOutputDTO:
    """List all users with pagination. Admin only."""
    claims = get_optional_auth_claims_from_request(request, config)
    if not claims or not claims.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list users",
        )
    return await interactor(ListUsersInputDTO(limit=limit, offset=offset))


@router.get("/{user_id}", response_model=GetUserByIdOutputDTO)
@inject
async def get_user_by_id(
    user_id: int,
    request: Request,
    config: FromDishka[Config],
    interactor: FromDishka[GetUserByIdInteractor] = None,
) -> GetUserByIdOutputDTO:
    """Get user by ID. Admin can view any user, regular users can only view themselves."""
    claims = get_optional_auth_claims_from_request(request, config)

    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Check authorization: admin or self
    if not claims.is_admin and claims.user_id.value != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users' profiles"
        )

    try:
        return await interactor(GetUserByIdInputDTO(user_id=UserId(user_id)))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.put("/{user_id}", response_model=UpdateUserOutputDTO)
@inject
async def update_user(
    user_id: int,
    data: UpdateUserRequest,
    request: Request,
    config: FromDishka[Config],
    interactor: FromDishka[UpdateUserInteractor] = None,
    transaction_manager: FromDishka[TransactionManager] = None,
) -> UpdateUserOutputDTO:
    """Update user details. Admin only."""
    claims = get_optional_auth_claims_from_request(request, config)
    if not claims or not claims.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users",
        )

    try:
        result = await interactor(
            UpdateUserInputDTO(
                user_id=UserId(user_id),
                actor_user_id=claims.user_id if claims else None,
                full_name=data.full_name,
                is_admin=data.is_admin,
            )
        )
        await transaction_manager.commit()
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error updating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_user(
    user_id: int,
    request: Request,
    config: FromDishka[Config],
    interactor: FromDishka[DeleteUserInteractor] = None,
    transaction_manager: FromDishka[TransactionManager] = None,
) -> None:
    """Delete a user. Admin only. Cannot delete last admin."""
    claims = get_optional_auth_claims_from_request(request, config)
    if not claims or not claims.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users",
        )

    try:
        await interactor(
            DeleteUserInputDTO(
                user_id=UserId(user_id),
                actor_user_id=claims.user_id if claims else None,
            )
        )
        await transaction_manager.commit()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


user_router = router
