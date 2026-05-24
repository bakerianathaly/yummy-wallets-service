import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import WalletDeps, get_current_user
from app.exceptions import (
    InactiveUserException,
    InactiveWalletException,
    InsufficientFundsException,
    InvalidAmountException,
    SameWalletTransferException,
    UnauthorizedWalletAccessException,
    WalletAlreadyExistsException,
    WalletNotFoundException,
)
from app.models.api_response import APIResponse
from app.models.user import User
from app.models.wallet import (
    DepositRequest,
    PaginatedTransactionsResponse,
    TransactionResponse,
    TransferRequest,
    WalletResponse,
    WalletSummaryResponse,
    WithdrawalRequest,
)
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
        return APIResponse(
            success=True, message="Depósito realizado", outcome=[transaction]
        )
    except InvalidAmountException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except WalletNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedWalletAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{wallet_id}/withdraw",
    response_model=APIResponse[TransactionResponse],
    status_code=status.HTTP_200_OK,
)
async def withdraw(
    wallet_id: uuid.UUID,
    body: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(WalletDeps.get_service),
) -> APIResponse[TransactionResponse]:
    try:
        transaction = await service.withdraw.execute(wallet_id, current_user, body)
        return APIResponse(
            success=True, message="Retiro realizado", outcome=[transaction]
        )
    except InvalidAmountException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except InsufficientFundsException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except WalletNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedWalletAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/me",
    response_model=APIResponse[WalletSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_wallet_summary(
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(WalletDeps.get_service),
) -> APIResponse[WalletSummaryResponse]:
    try:
        summary = await service.get_summary.execute(current_user)
        return APIResponse(success=True, message="Wallet obtenida", outcome=[summary])
    except WalletNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/me/transactions",
    response_model=APIResponse[PaginatedTransactionsResponse],
    status_code=status.HTTP_200_OK,
)
async def get_wallet_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(WalletDeps.get_service),
) -> APIResponse[PaginatedTransactionsResponse]:
    try:
        result = await service.get_transactions.execute(current_user, page, page_size)
        return APIResponse(
            success=True, message="Transacciones obtenidas", outcome=[result]
        )
    except WalletNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{from_wallet_id}/transfer",
    response_model=APIResponse[TransactionResponse],
    status_code=status.HTTP_200_OK,
)
async def transfer(
    from_wallet_id: uuid.UUID,
    body: TransferRequest,
    current_user: User = Depends(get_current_user),
    service: WalletService = Depends(WalletDeps.get_service),
) -> APIResponse[TransactionResponse]:
    try:
        transaction = await service.transfer.execute(from_wallet_id, current_user, body)
        return APIResponse(
            success=True, message="Transferencia realizada", outcome=[transaction]
        )
    except (
        InvalidAmountException,
        SameWalletTransferException,
        InsufficientFundsException,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except WalletNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InactiveWalletException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except UnauthorizedWalletAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
