from app.repositories.user_repository import UserRepository
from app.services.user.create_user import CreateUser
from app.services.user.delete_user import DeleteUser
from app.services.user.login_user import LoginUser
from app.services.user.update_user import UpdateUser


class UserService:
    def __init__(self, repository: UserRepository):
        self.create = CreateUser(repository)
        self.login = LoginUser(repository)
        self.update = UpdateUser(repository)
        self.delete = DeleteUser(repository)
