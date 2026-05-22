from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import WalletDeps, get_current_user
from app.exceptions import InactiveUserException, WalletAlreadyExistsException
from app.models.api_response import APIResponse
from app.models.user import User
from app.models.wallet import WalletResponse
from app.services.wallet import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post(
    "/",
    response_model=APIResponse[WalletResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_wallet(
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(WalletDeps.get_service),
) -> APIResponse[WalletResponse]:
    try:
        wallet = await service.create.execute(current_user)
        return APIResponse(success=True, message="Wallet creado", outcome=[wallet])
    except InactiveUserException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except WalletAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
