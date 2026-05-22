class UserNotFoundException(Exception):
    pass


class UserAlreadyExistsException(Exception):
    pass


class InvalidPasswordException(Exception):
    pass


class InactiveUserException(Exception):
    pass


class InvalidTokenException(Exception):
    pass


class ValidationException(Exception):
    pass
