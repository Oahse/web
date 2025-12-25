from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
from uuid import UUID
import uuid
import json
# import redis # REMOVED

from core.config import settings
from core.exceptions import APIException
from core.utils.response import Response
from schemas.response import APIResponse
from core.dependencies import get_current_auth_user, get_db # get_db for AsyncSession
from models.user import User
from models.product import Product, ProductVariant # ADDED for product lookup

from negotiator.core import Buyer, Seller, NegotiationEngine
from negotiator.service import NegotiatorService # ADDED NegotiatorService
from backend.core.kafka import get_kafka_producer_service # ADD THIS LINE


router = APIRouter(
    prefix="/negotiate",
    tags=["Negotiator"],
)

# Initialize Redis client for negotiation state persistence.
# This client is used by the FastAPI routes to store and retrieve the serialized
# state of NegotiationEngine instances, which are then processed by Kafka.
# redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True) # REMOVED


class NegotiationAgentConfig(BaseModel):
    """Configuration for a single negotiation agent."""
    name: str = Field(..., description="Name of the agent (e.g., Buyer, Seller)")
    target_price: float = Field(..., gt=0, description="The agent's initial target price.")
    limit_price: float = Field(..., gt=0, description="The agent's absolute limit price.")
    style: str = Field("balanced", description="Negotiation style (e.g., 'aggressive', 'patient', 'friendly', 'balanced').")

class NegotiationStartRequest(BaseModel):
    """Request model for starting a new negotiation."""
    buyer_config: NegotiationAgentConfig
    seller_config: NegotiationAgentConfig
    product_id: UUID
    product_variant_id: UUID
    quantity: int = Field(..., gt=0)
    initial_offer: float = Field(..., gt=0)

class NegotiationStateResponse(BaseModel):
    """Response model for the current state of a negotiation."""
    negotiation_id: UUID
    round: int
    finished: bool
    message: str
    final_price: Optional[float] = None
    buyer_current_offer: Optional[float] = None
    seller_current_offer: Optional[float] = None
    # Add metadata
    buyer_id: Optional[str] = None
    seller_id: Optional[str] = None
    product_id: Optional[str] = None
    product_variant_id: Optional[str] = None
    quantity: Optional[int] = None

class NegotiationStepRequest(BaseModel):
    """Request model for advancing a negotiation by one step."""
    negotiation_id: UUID = Field(..., description="ID of the ongoing negotiation.")
    offer_price: float = Field(..., gt=0, description="The new offer price from the current user.")
    # buyer_new_target: Optional[float] = Field(None, gt=0, description="Optional new target price for the buyer.") # REMOVED
    # seller_new_target: Optional[float] = Field(None, gt=0, description="Optional new target price for the seller.") # REMOVED

class NegotiationTaskResponse(BaseModel):
    """Response model for when a negotiation task is dispatched asynchronously."""
    negotiation_id: UUID
    task_id: str
    message: str

@router.post("/start", response_model=APIResponse[NegotiationTaskResponse], status_code=status.HTTP_202_ACCEPTED)
async def start_negotiation(
    request: NegotiationStartRequest,
    current_user: User = Depends(get_current_auth_user), # Requires authentication
    db: AsyncSession = Depends(get_db), # Inject DB session
):
    """
    Initializes a new negotiation session and dispatches the first step as a Kafka message.
    The negotiation state is stored in Redis for persistence.
    """
    # Fetch product variant to get seller_id
    product_variant = await db.get(ProductVariant, request.product_variant_id)
    if not product_variant:
        raise HTTPException(status_code=404, detail="Product variant not found.")
    
    product = await db.get(Product, product_variant.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    negotiator_service = NegotiatorService(db) # Initialize service
    
    negotiation_data = await negotiator_service.create_negotiation(
        buyer_id=current_user.id,
        seller_id=product.supplier_id, # Assuming supplier is the seller
        product_id=request.product_id,
        product_variant_id=request.product_variant_id,
        quantity=request.quantity,
        initial_offer=request.initial_offer
    )

    return Response.success(
        NegotiationTaskResponse(negotiation_id=UUID(negotiation_data["negotiation_id"]), task_id="N/A", message=negotiation_data["message"]), # task_id will not be available from Kafka
        message="Negotiation started successfully."
    )


@router.post("/step", response_model=APIResponse[NegotiationTaskResponse])
async def step_negotiation(
    request: NegotiationStepRequest,
    current_user: User = Depends(get_current_auth_user), # Requires authentication
    db: AsyncSession = Depends(get_db), # Inject DB session
):
    """
    Dispatches a Kafka message to advance an ongoing negotiation by one step (round).
    Returns the ID of the dispatched Kafka task for tracking.
    """
    negotiator_service = NegotiatorService(db)
    negotiation_state = await negotiator_service.record_offer(
        negotiation_id=request.negotiation_id,
        user_id=current_user.id,
        offer_price=request.offer_price
    )

    return Response.success(
        NegotiationTaskResponse(negotiation_id=negotiation_state["negotiation_id"], task_id="N/A", message="Negotiation step dispatched."),
        message="Negotiation step initiated asynchronously."
    )


@router.get("/{negotiation_id}", response_model=APIResponse[NegotiationStateResponse])
async def get_negotiation_state(
    negotiation_id: UUID, # Use UUID type directly for path parameter
    current_user: User = Depends(get_current_auth_user), # Requires authentication
    db: AsyncSession = Depends(get_db), # Inject DB session
):
    """
    Retrieves the current state of a specific negotiation session from Redis.
    """
    negotiator_service = NegotiatorService(db)
    negotiation_state = await negotiator_service.get_negotiation_state(negotiation_id)
    
    response_data = NegotiationStateResponse(
        negotiation_id=UUID(negotiation_state["negotiation_id"]),
        round=negotiation_state["round"],
        finished=negotiation_state["finished"],
        message=negotiation_state["message"],
        final_price=negotiation_state["final_price"],
        buyer_current_offer=negotiation_state["buyer_current_offer"],
        seller_current_offer=negotiation_state["seller_current_offer"],
        buyer_id=negotiation_state.get("buyer_id"),
        seller_id=negotiation_state.get("seller_id"),
        product_id=negotiation_state.get("product_id"),
        product_variant_id=negotiation_state.get("product_variant_id"),
        quantity=negotiation_state.get("quantity")
    )
    return Response.success(response_data, message="Negotiation state retrieved successfully.")


@router.delete("/{negotiation_id}", status_code=status.HTTP_200_OK) # Changed to 200 OK as it returns a response
async def delete_negotiation(
    negotiation_id: UUID, # Use UUID type directly for path parameter
    current_user: User = Depends(get_current_auth_user), # Requires authentication
    db: AsyncSession = Depends(get_db), # Inject DB session
):
    """
    Deletes an ongoing negotiation session from Redis.
    This endpoint is used to clean up completed or abandoned negotiation sessions.
    """
    negotiator_service = NegotiatorService(db)
    await negotiator_service.clear_negotiation(negotiation_id)
    return Response.success(message="Negotiation session deleted successfully.")
