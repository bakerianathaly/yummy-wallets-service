from datetime import datetime

from app.models.user import User
from app.repositories.user_repository import UserRepository


class DeleteUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, user: User) -> User:
        user.is_active = False
        user.updated_at = datetime.now()
        return await self.repository.update(user)
