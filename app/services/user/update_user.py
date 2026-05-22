from datetime import datetime
from uuid import UUID

from app.auth.security import hash_password
from app.exceptions import (
    InactiveUserException,
    UserAlreadyExistsException,
    ValidationException,
)
from app.models.user import User, UserUpdate
from app.repositories.user_repository import UserRepository


class UpdateUser:
    MIN_PASSWORD_LENGTH = 8

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, user: User, data: UserUpdate) -> User:
        if not user.is_active:
            raise InactiveUserException("No se puede editar un usuario desactivado")

        fields = data.model_dump(exclude_unset=True)
        self._validate(fields)

        if "email" in fields:
            new_email = fields["email"].lower().strip()
            if new_email != user.email:
                existing = await self.repository.get_by_email(new_email)
                if existing:
                    raise UserAlreadyExistsException(
                        f"El email '{new_email}' ya está en uso"
                    )
            fields["email"] = new_email

        if "full_name" in fields:
            fields["full_name"] = fields["full_name"].strip()

        if "password" in fields:
            fields["hashed_password"] = hash_password(fields.pop("password"))

        for field, value in fields.items():
            setattr(user, field, value)
        user.updated_at = datetime.now()

        return await self.repository.update(user)

    def _validate(self, fields: dict) -> None:
        password = fields.get("password")
        if password is not None and len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationException(
                f"La contraseña debe tener al menos {self.MIN_PASSWORD_LENGTH} caracteres"
            )

        email = fields.get("email")
        if email is not None and "@" not in email:
            raise ValidationException("El email no es válido")

        full_name = fields.get("full_name")
        if full_name is not None and len(full_name.strip()) < 2:
            raise ValidationException("El nombre debe tener al menos 2 caracteres")
