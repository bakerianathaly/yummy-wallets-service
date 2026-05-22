from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import UserDeps
from app.exceptions import (
    InactiveUserException,
    InvalidPasswordException,
    UserAlreadyExistsException,
    UserNotFoundException,
    ValidationException,
)
from app.models.api_response import APIResponse
from app.models.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserCreate,
    service: UserService = Depends(UserDeps.get_service),
) -> APIResponse[UserResponse]:
    try:
        user = await service.create.execute(data)
        return APIResponse(success=True, message="Usuario creado", outcome=[user])
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    service: UserService = Depends(UserDeps.get_service),
) -> TokenResponse:
    try:
        return await service.login.execute(data)
    except UserNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InactiveUserException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidPasswordException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
