"""Transaction API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import get_current_user, get_transaction_client, AuthUser
from app.grpc_clients.transaction_client import TransactionGRPCClient
from aegis_shared.schemas.transaction import TransactionCreate, TransactionAccepted, TransactionResponse
from aegis_shared.utils.logging import get_logger

logger = get_logger("transactions_router")
router = APIRouter(prefix="/transactions", tags=["Transactions"])



@router.post(
    "",
    response_model=TransactionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a transaction for risk evaluation",
)
async def create_transaction(
    transaction: TransactionCreate,
    request: Request,
    user: AuthUser = Depends(get_current_user),               
    client: TransactionGRPCClient = Depends(get_transaction_client),  
):
    """
    Submit a transaction for fraud risk evaluation.
    """


    logger.info(
        "transaction_submission_received",
        idempotency_key=transaction.idempotency_key,
    )


    return await client.create_transaction(
        transaction=transaction,
        client_id=user.sub,         
        request=request,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get transaction details",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    request: Request,
    user: AuthUser = Depends(get_current_user),
    client: TransactionGRPCClient = Depends(get_transaction_client),
):
    """Retrieve a transaction by ID."""
    
    result = await client.get_transaction(
        transaction_id=transaction_id,
        client_id=user.sub,
        request=request,
    )

    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return result
    