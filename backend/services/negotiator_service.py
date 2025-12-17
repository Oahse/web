import json
from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, UTC
from uuid import UUID

from models.negotiation import Negotiation, NegotiationStatus
from models.user import User
from models.product import Product, ProductVariant
from core.exceptions import APIException
from services.websockets import manager as websocket_manager # Import the manager instance
from services.negotiator import NegotiationEngine, Buyer, Seller # Import the core negotiation logic
from tasks.negotiation_tasks import perform_negotiation_step # Celery task for async processing


class NegotiatorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_negotiation(
        self,
        buyer_id: UUID,
        seller_id: UUID,
        product_id: UUID,
        product_variant_id: Optional[UUID],
        quantity: int,
        initial_offer: float
    ) -> Negotiation:
        """
        Initiates a new negotiation record in the database.
        """
        negotiation = Negotiation(
            buyer_id=buyer_id,
            seller_id=seller_id,
            product_id=product_id,
            product_variant_id=product_variant_id,
            quantity=quantity,
            initial_offer=initial_offer,
            current_price=initial_offer,
            last_offer_by=buyer_id, # Buyer makes the initial offer
            status=NegotiationStatus.PENDING,
            offers=[
                {"user_id": str(buyer_id), "offer_price": initial_offer, "timestamp": datetime.now(UTC).isoformat()}
            ]
        )
        self.db.add(negotiation)
        await self.db.commit()
        await self.db.refresh(negotiation)

        # Dispatch task to process the initial offer/round
        self.dispatch_negotiation_round_processing(negotiation.id)
        
        return negotiation

    async def get_negotiation_by_id(self, negotiation_id: UUID) -> Negotiation:
        """
        Retrieves a negotiation record by its ID.
        """
        result = await self.db.execute(
            select(Negotiation).where(Negotiation.id == negotiation_id)
        )
        negotiation = result.scalar_one_or_none()
        if not negotiation:
            raise APIException(status_code=404, message="Negotiation not found.")
        return negotiation

    async def record_offer(
        self,
        negotiation_id: UUID,
        user_id: UUID,
        offer_price: float
    ) -> Negotiation:
        """
        Records a new offer for an ongoing negotiation.
        """
        negotiation = await self.get_negotiation_by_id(negotiation_id)

        if negotiation.status in [NegotiationStatus.ACCEPTED, NegotiationStatus.REJECTED, NegotiationStatus.EXPIRED]:
            raise APIException(status_code=400, message="Cannot record offer for a concluded negotiation.")
        
        # Determine if the offer is from buyer or seller and validate turn (optional but good practice)
        if user_id not in [negotiation.buyer_id, negotiation.seller_id]:
            raise APIException(status_code=403, message="User is not a participant in this negotiation.")
        
        # Update negotiation state
        negotiation.current_price = offer_price
        negotiation.last_offer_by = user_id
        negotiation.offers.append(
            {"user_id": str(user_id), "offer_price": offer_price, "timestamp": datetime.now(UTC).isoformat()}
        )
        negotiation.status = NegotiationStatus.IN_PROGRESS if negotiation.status == NegotiationStatus.PENDING else NegotiationStatus.COUNTERED
        negotiation.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(negotiation)

        # Dispatch Celery task to process this round, which might lead to counter-offer or conclusion
        self.dispatch_negotiation_round_processing(negotiation.id) # Call the helper to dispatch
        
        await self.notify_negotiation_update(negotiation) # Notify participants via WebSocket

        return negotiation

    async def update_negotiation_status(self, negotiation_id: UUID, new_status: NegotiationStatus) -> Negotiation:
        """
        Updates the status of a negotiation (e.g., accepted, rejected, expired).
        """
        negotiation = await self.get_negotiation_by_id(negotiation_id)
        negotiation.status = new_status
        negotiation.updated_at = datetime.now(UTC)
        if new_status in [NegotiationStatus.ACCEPTED, NegotiationStatus.REJECTED, NegotiationStatus.EXPIRED]:
            negotiation.end_time = datetime.now(UTC)
        
        await self.db.commit()
        await self.db.refresh(negotiation)
        await self.notify_negotiation_update(negotiation, event_type="negotiation_status_update") # Notify participants via WebSocket
        return negotiation

    def dispatch_negotiation_round_processing(self, negotiation_id: UUID):
        """
        Dispatches a Celery task to asynchronously process a negotiation round.
        This allows the main API thread to respond quickly while complex negotiation
        logic or agent responses are handled in the background.
        """
        perform_negotiation_step.delay(str(negotiation_id))
        print(f"Dispatched negotiation round processing for ID: {negotiation_id}")

    async def notify_negotiation_update(self, negotiation: Negotiation, event_type: str = "negotiation_update"):
        """
        Sends WebSocket updates to all participants of the negotiation.
        """
        websocket_message = {
            "type": event_type,
            "negotiation": negotiation.to_dict(),
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Send to buyer
        await websocket_manager.send_to_user(str(negotiation.buyer_id), json.dumps(websocket_message))
        # Send to seller
        await websocket_manager.send_to_user(str(negotiation.seller_id), json.dumps(websocket_message))
        
        print(f"WebSocket update sent for negotiation {negotiation.id} to buyer {negotiation.buyer_id} and seller {negotiation.seller_id}")

    async def process_negotiation_with_engine(self, negotiation_id: UUID):
        """
        Processes a negotiation round using the NegotiationEngine.
        This method would typically be called by a Celery task.
        """
        negotiation = await self.get_negotiation_by_id(negotiation_id)

        if negotiation.status != NegotiationStatus.IN_PROGRESS and negotiation.status != NegotiationStatus.PENDING and negotiation.status != NegotiationStatus.COUNTERED:
            print(f"Negotiation {negotiation_id} is already concluded ({negotiation.status.value}). Skipping processing.")
            return

        # Fetch buyer and seller details to instantiate agents
        buyer_db = await self.db.execute(select(User).where(User.id == negotiation.buyer_id))
        buyer_obj = buyer_db.scalar_one()
        
        seller_db = await self.db.execute(select(User).where(User.id == negotiation.seller_id))
        seller_obj = seller_db.scalar_one()

        # You would need to define how to derive target_price, limit_price, and style
        # from your User/Product models or from settings. For now, using placeholders.
        # Example: buyer's limit could be a percentage below initial_offer, seller's limit a percentage above cost.
        buyer_target_price = negotiation.initial_offer # Buyer's ideal price
        buyer_limit_price = negotiation.current_price * 1.1 # Buyer's max willingness, for example 10% above current counter

        seller_target_price = negotiation.current_price # Seller's ideal price
        seller_limit_price = negotiation.current_price * 0.9 # Seller's min willingness, for example 10% below current counter

        buyer_agent = Buyer(
            name=buyer_obj.firstname,
            target_price=buyer_target_price,
            limit_price=buyer_limit_price,
            style="balanced" # Or derive from user profile
        )
        seller_agent = Seller(
            name=seller_obj.firstname,
            target_price=seller_target_price,
            limit_price=seller_limit_price,
            style="balanced" # Or derive from user profile
        )

        engine = NegotiationEngine(buyer_agent, seller_agent)
        # Reconstruct engine state from negotiation offers if needed, or start fresh if always 1 round per task
        
        result = engine.step() # Perform one step of negotiation

        if result["finished"]:
            negotiation.status = NegotiationStatus.ACCEPTED if result["final_price"] else NegotiationStatus.REJECTED # Or other logic
            negotiation.current_price = result["final_price"]
            negotiation.end_time = datetime.now(UTC)
            print(f"Negotiation {negotiation_id} concluded with price: {result['final_price']}")
        else:
            negotiation.status = NegotiationStatus.IN_PROGRESS
            # Logic to update negotiation.current_price based on new offers from engine.step()
            # This part needs careful thought: does engine.step() give us a new price to record?
            # Or does it just determine if a deal is closed?
            # If agent makes an offer, we need to record that offer as if a user made it.
            print(f"Negotiation {negotiation_id} continues. Buyer offer: {result.get('buyer_offer')}, Seller offer: {result.get('seller_offer')}")
        
        negotiation.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(negotiation)
        await self.notify_negotiation_update(negotiation)