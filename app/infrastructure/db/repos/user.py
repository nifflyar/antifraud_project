from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from app.domain.user.entity import User
from app.domain.user.repository import IUserRepository
from app.domain.user.vo import Email, UserId
from app.infrastructure.db.mappers import UserMapper
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class UserRepositoryImpl(IUserRepository, BaseSQLAlchemyRepo):
    async def get_by_id(self, user_id: UserId) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        user_model = result.scalars().first()
        return UserMapper.to_domain(user_model) if user_model else None

    async def get_by_email(self, email: Email) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        user_model = result.scalars().first()
        return UserMapper.to_domain(user_model) if user_model else None

    async def any_users_exist(self) -> bool:
        stmt = select(func.count()).select_from(UserModel)
        result = await self._session.execute(stmt)
        return bool(result.scalar() or 0)

    async def get_all(self, limit: int = 20, offset: int = 0) -> list[User]:
        stmt = select(UserModel).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        user_models = result.scalars().all()
        return [UserMapper.to_domain(model) for model in user_models]

    async def create_user(self, user: User) -> User:
        user_model = UserMapper.to_model(user)
        self._session.add(user_model)
        await self._session.flush()
        return UserMapper.to_domain(user_model)

    async def update_user(self, user: User) -> User:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(
                full_name=user.full_name,
                is_admin=user.is_admin,
                is_active=user.is_active,
                role=user.role,
                updated_at=user.updated_at,
            )
        )
        await self._session.execute(stmt)
        return user

    async def delete_user(self, user_id: UserId) -> None:
        stmt = delete(UserModel).where(UserModel.id == user_id)
        await self._session.execute(stmt)

    async def count_admins(self) -> int:
        """Count total number of admin users using efficient SQL query"""
        stmt = select(func.count()).select_from(UserModel).where(UserModel.is_admin == True)
        result = await self._session.execute(stmt)
        return result.scalar() or 0
