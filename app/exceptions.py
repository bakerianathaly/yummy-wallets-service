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


class WalletAlreadyExistsException(Exception):
    pass


class WalletNotFoundException(Exception):
    pass


class InvalidAmountException(Exception):
    pass


class UnauthorizedWalletAccessException(Exception):
    pass


class InsufficientFundsException(Exception):
    pass


class DatabaseException(Exception):
    pass
