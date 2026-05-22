from app.auth.security import create_access_token, verify_password
from app.exceptions import (
    InactiveUserException,
    InvalidPasswordException,
    UserNotFoundException,
)
from app.models.user import LoginRequest, TokenResponse
from app.repositories.user_repository import UserRepository


class LoginUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, data: LoginRequest) -> TokenResponse:
        user = await self.repository.get_by_email(data.email)
        if not user:
            raise UserNotFoundException(
                f"No existe un usuario con el email '{data.email}'"
            )

        if not user.is_active:
            raise InactiveUserException("El usuario está desactivado")

        if not verify_password(data.password, user.hashed_password):
            raise InvalidPasswordException("Contraseña incorrecta")

        token = create_access_token(user.id)
        return TokenResponse(access_token=token)
