import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import WalletDeps, get_current_user
from app.exceptions import (
    InactiveUserException,
    InvalidAmountException,
    UnauthorizedWalletAccessException,
    WalletAlreadyExistsException,
    WalletNotFoundException,
)
from app.models.api_response import APIResponse
from app.models.user import User
from app.models.wallet import DepositRequest, TransactionResponse, WalletResponse
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


@router.post(
    "/{wallet_id}/deposit",
    response_model=APIResponse[TransactionResponse],
    status_code=status.HTTP_200_OK,
)
async def deposit(
    wallet_id: uuid.UUID,
    body: DepositRequest,
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(WalletDeps.get_service),
) -> APIResponse[TransactionResponse]:
    try:
        transaction = await service.deposit.execute(wallet_id, current_user, body)
        return APIResponse(success=True, message="Depósito realizado", outcome=[transaction])
    except InvalidAmountException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except WalletNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedWalletAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
