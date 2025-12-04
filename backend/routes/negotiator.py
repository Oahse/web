from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
from uuid import UUID
import uuid
import json
import redis

from core.config import settings
from core.exceptions import APIException
from core.utils.response import Response
from core.dependencies import get_current_auth_user
from models.user import User

from services.negotiator import Buyer, Seller, NegotiationEngine
from backend.tasks.negotiation_tasks import perform_negotiation_step # Import the Celery task

router = APIRouter(
    prefix="/negotiate",
    tags=["Negotiator"],
)

# Initialize Redis client for negotiation state persistence
# This client will be used by both FastAPI routes and Celery tasks.
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


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

class NegotiationStateResponse(BaseModel):
    """Response model for the current state of a negotiation."""
    negotiation_id: UUID
    round: int
    finished: bool
    message: str
    final_price: Optional[float] = None
    buyer_current_offer: Optional[float] = None
    seller_current_offer: Optional[float] = None

class NegotiationStepRequest(BaseModel):
    """Request model for advancing a negotiation by one step."""
    negotiation_id: UUID = Field(..., description="ID of the ongoing negotiation.")
    buyer_new_target: Optional[float] = Field(None, gt=0, description="Optional new target price for the buyer.")
    seller_new_target: Optional[float] = Field(None, gt=0, description="Optional new target price for the seller.")

class NegotiationTaskResponse(BaseModel):
    """Response model for when a negotiation task is dispatched asynchronously."""
    negotiation_id: UUID
    task_id: str
    message: str

@router.post("/start", response_model=Response[NegotiationTaskResponse], status_code=status.HTTP_202_ACCEPTED)
async def start_negotiation(
    request: NegotiationStartRequest,
    current_user: User = Depends(get_current_auth_user), # Requires authentication
):
    """
    Initializes a new negotiation session and dispatches the first step as a Celery task.
    The negotiation state is stored in Redis.
    """
    negotiation_id = uuid.uuid4() # Generate UUID for the session
    negotiation_key = f"negotiation:{negotiation_id}"

    # Initialize agents and engine
    buyer = Buyer(
        name=request.buyer_config.name,
        target_price=request.buyer_config.target_price,
        limit_price=request.buyer_config.limit_price,
        style=request.buyer_config.style
    )
    seller = Seller(
        name=request.seller_config.name,
        target_price=request.seller_config.target_price,
        limit_price=request.seller_config.limit_price,
        style=request.seller_config.style
    )
    engine = NegotiationEngine(buyer, seller)

    # Save initial engine state to Redis
    redis_client.set(negotiation_key, json.dumps(engine.to_dict()))

    # Dispatch the first negotiation step asynchronously
    task = perform_negotiation_step.delay(str(negotiation_id))

    return Response.success(
        NegotiationTaskResponse(negotiation_id=negotiation_id, task_id=task.id, message="Negotiation started and first step dispatched."),
        message="Negotiation started successfully."
    )


@router.post("/step", response_model=Response[NegotiationTaskResponse])
async def step_negotiation(
    request: NegotiationStepRequest,
    current_user: User = Depends(get_current_auth_user), # Requires authentication
):
    """
    Dispatches a Celery task to advance an ongoing negotiation by one step (round).
    Optionally allows updating buyer's or seller's target prices before the step.
    Returns the ID of the dispatched Celery task.
    """
    negotiation_id = request.negotiation_id
    negotiation_key = f"negotiation:{negotiation_id}"

    if not redis_client.exists(negotiation_key):
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Negotiation with ID {negotiation_id} not found."
        )
    
    # Dispatch the negotiation step asynchronously
    task = perform_negotiation_step.delay(
        str(negotiation_id),
        buyer_new_target=request.buyer_new_target,
        seller_new_target=request.seller_new_target
    )

    return Response.success(
        NegotiationTaskResponse(negotiation_id=negotiation_id, task_id=task.id, message="Negotiation step dispatched."),
        message="Negotiation step initiated asynchronously."
    )


@router.get("/{negotiation_id}", response_model=Response[NegotiationStateResponse])
async def get_negotiation_state(
    negotiation_id: UUID, # Use UUID type directly for path parameter
    current_user: User = Depends(get_current_auth_user), # Requires authentication
):
    """
    Retrieves the current state of a specific negotiation session from Redis.
    """
    negotiation_key = f"negotiation:{negotiation_id}"
    negotiation_data_json = redis_client.get(negotiation_key)

    if not negotiation_data_json:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Negotiation with ID {negotiation_id} not found."
        )
    
    negotiation_data = json.loads(negotiation_data_json)
    engine = NegotiationEngine.from_dict(negotiation_data)

    response_data = NegotiationStateResponse(
        negotiation_id=negotiation_id,
        round=engine.round,
        finished=engine.finished,
        message="Negotiation ongoing." if not engine.finished else f"Deal reached at ₦{engine.final_price:.2f}",
        final_price=engine.final_price,
        buyer_current_offer=engine.buyer.target,
        seller_current_offer=engine.seller.target
    )
    return Response.success(response_data, message="Negotiation state retrieved successfully.")


@router.delete("/{negotiation_id}", status_code=status.HTTP_200_OK) # Changed to 200 OK as it returns a response
async def delete_negotiation(
    negotiation_id: UUID, # Use UUID type directly for path parameter
    current_user: User = Depends(get_current_auth_user), # Requires authentication
):
    """
    Deletes an ongoing negotiation session from Redis.
    """
    negotiation_key = f"negotiation:{negotiation_id}"
    if redis_client.delete(negotiation_key):
        return Response.success(message="Negotiation session deleted successfully.")
    else:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Negotiation with ID {negotiation_id} not found."
        )
