from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import UserDeps, get_current_user
from app.exceptions import (
    InactiveUserException,
    InvalidTokenException,
    UserAlreadyExistsException,
    ValidationException,
)
from app.models.api_response import APIResponse
from app.models.user import User, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me", response_model=APIResponse[UserResponse])
async def update_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(UserDeps.get_service),
) -> APIResponse[UserResponse]:
    try:
        updated = await service.update.execute(current_user, data)
        return APIResponse(
            success=True, message="Usuario actualizado", outcome=[updated]
        )
    except InactiveUserException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except InvalidTokenException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.delete("/me", response_model=APIResponse[UserResponse])
async def delete_user(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(UserDeps.get_service),
) -> APIResponse[UserResponse]:
    try:
        deactivated = await service.delete.execute(current_user)
        return APIResponse(
            success=True,
            message="Usuario desactivado. El token ya no es válido.",
            outcome=[deactivated],
        )
    except InvalidTokenException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
