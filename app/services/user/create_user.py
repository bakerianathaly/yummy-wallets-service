from app.auth.security import hash_password
from app.exceptions import UserAlreadyExistsException, ValidationException
from app.models.user import User, UserCreate
from app.repositories.user_repository import UserRepository


class CreateUser:
    MIN_PASSWORD_LENGTH = 8

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, data: UserCreate) -> User:
        self._validate(data)

        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise UserAlreadyExistsException(
                f"El email '{data.email}' ya está registrado"
            )

        user = User(
            email=data.email.lower().strip(),
            full_name=data.full_name.strip(),
            hashed_password=hash_password(data.password),
        )
        return await self.repository.create(user)

    def _validate(self, data: UserCreate) -> None:
        if len(data.password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationException(
                f"La contraseña debe tener al menos {self.MIN_PASSWORD_LENGTH} caracteres"
            )
        if not data.email or "@" not in data.email:
            raise ValidationException("El email no es válido")
        if not data.full_name or len(data.full_name.strip()) < 2:
            raise ValidationException("El nombre debe tener al menos 2 caracteres")
