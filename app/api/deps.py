from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.db.sessions import get_db
from app.exceptions import InactiveUserException, InvalidTokenException, UserNotFoundException
from app.models.user import User
from app.repositories.user_repository import UserRepository
# from app.services.surgical_history.surgical_history_service import (
#     SurgicalHistoryUseCase,
# )

from app.services.user.user_service import UserService
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class UserDeps:
    @staticmethod
    def get_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
        return UserRepository(db)

    @staticmethod
    def get_service(
        repo: UserRepository = Depends(get_repository),
    ) -> UserService:
        return UserService(repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        user_id_str = decode_access_token(token)
    except ValueError as e:
        raise InvalidTokenException(str(e))

    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id_str))

    if user is None:
        raise UserNotFoundException("Usuario no encontrado")
    if not user.is_active:
        raise InactiveUserException("El usuario está desactivado")

    return user
