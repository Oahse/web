import json
import logging
from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, UTC, timedelta
from uuid import UUID
import redis

from backend.models.user import User
from backend.models.product import Product, ProductVariant # Needed for user/product lookups if not passed
from backend.core.exceptions import APIException
from backend.services.websockets import manager as websocket_manager # Import the manager instance
from negotiator.core import NegotiationEngine, Buyer, Seller
from backend.services.kafka_producer import get_kafka_producer_service
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis client for negotiation state persistence.
# This client is shared between FastAPI (routes) and Kafka consumer tasks.
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Key prefix for storing negotiated prices for a user/product variant
NEGOTIATED_PRICE_KEY_PREFIX = "negotiated_price:" # Key: negotiated_price:{user_id}:{product_variant_id}
NEGOTIATED_PRICE_EXPIRY_SECONDS = 3600 # Negotiated price valid for 1 hour

class NegotiatorService:
    def __init__(self, db: AsyncSession):
        self.db = db # Keep db session for User/Product lookups

    async def create_negotiation(
        self,
        buyer_id: UUID,
        seller_id: UUID,
        product_id: UUID,
        product_variant_id: Optional[UUID],
        quantity: int,
        initial_offer: float
    ) -> dict: # Changed return type as it no longer returns Negotiation model
        """
        Initiates a new negotiation session by creating a NegotiationEngine and storing its state in Redis.
        """
        negotiation_id = uuid.uuid4() # Generate new ID for Redis key

        # Fetch buyer and seller details to instantiate agents
        buyer_obj = await self.db.get(User, buyer_id)
        if not buyer_obj:
            raise APIException(status_code=404, message="Buyer not found.")
        seller_obj = await self.db.get(User, seller_id)
        if not seller_obj:
            raise APIException(status_code=404, message="Seller not found.")
        
        # Determine target and limit prices (placeholders for now, should come from product/user data)
        # For simplicity, assume product's base price is the seller's initial offer/target
        # and buyer's limit is a percentage above product's price, seller's limit is a percentage below.
        # This logic needs to be robustly defined based on actual product pricing.
        # For now, let's use initial_offer as basis.

        # Fetch product variant to determine pricing context (e.g., base_price, sale_price)
        variant = None
        if product_variant_id:
            variant = await self.db.get(ProductVariant, product_variant_id)
        
        if not variant:
            raise APIException(status_code=404, message="Product variant not found for negotiation.")

        # Assume seller's initial offer is the variant's current selling price (sale_price or base_price)
        seller_initial_price = variant.sale_price if variant.sale_price is not None else variant.base_price
        
        # Assume buyer's initial offer is the 'initial_offer' passed to this function
        # Buyer's limit might be 10% above their target, seller's limit 10% below their target
        # For a more robust model, these limits should be configurable/derived.
        
        buyer_agent = Buyer(
            name=buyer_obj.firstname,
            target_price=initial_offer, # Buyer's first offer
            limit_price=seller_initial_price * 1.2, # Buyer max willingness to pay (20% above seller's asking)
            style="balanced"
        )
        seller_agent = Seller(
            name=seller_obj.firstname,
            target_price=seller_initial_price, # Seller's asking price
            limit_price=seller_initial_price * 0.8, # Seller min willingness to accept (20% below asking)
            style="balanced"
        )

        engine = NegotiationEngine(buyer_agent, seller_agent)
        
        # Store engine state along with negotiation metadata in Redis
        engine_data = engine.to_dict()
        engine_data.update({
            "buyer_id": str(buyer_id),
            "seller_id": str(seller_id),
            "product_id": str(product_id),
            "product_variant_id": str(product_variant_id) if product_variant_id else None,
            "quantity": quantity
        })

        negotiation_key = f"negotiation:{negotiation_id}"
        redis_client.set(negotiation_key, json.dumps(engine_data))

        # Dispatch task to process the initial offer/round
        await self.dispatch_negotiation_round_processing(negotiation_id)
        
        return {
            "negotiation_id": str(negotiation_id),
            "status": "pending",
            "current_price": initial_offer,
            "message": "Negotiation initiated."
        }

    async def get_negotiation_state(self, negotiation_id: UUID) -> dict:
        """
        Retrieves the current state of a negotiation from Redis.
        """
        negotiation_key = f"negotiation:{negotiation_id}"
        negotiation_data_json = redis_client.get(negotiation_key)

        if not negotiation_data_json:
            raise APIException(status_code=404, message="Negotiation not found or expired.")

        engine_data = json.loads(negotiation_data_json)
        engine = NegotiationEngine.from_dict(engine_data)
        
        # This method is used to get state, not update, so just return relevant parts.
        return {
            "negotiation_id": str(negotiation_id),
            "round": engine.round,
            "finished": engine.finished,
            "final_price": engine.final_price,
            "buyer_current_offer": engine.buyer.target,
            "seller_current_offer": engine.seller.target,
            "message": "Negotiation ongoing." if not engine.finished else f"Deal reached at {engine.final_price:.2f}",
            "buyer_id": engine_data.get("buyer_id"),
            "seller_id": engine_data.get("seller_id"),
            "product_id": engine_data.get("product_id"),
            "product_variant_id": engine_data.get("product_variant_id"),
            "quantity": engine_data.get("quantity")
        }

    async def record_offer(
        self,
        negotiation_id: UUID,
        user_id: UUID,
        offer_price: float
    ) -> dict: # Changed return type
        """
        Records a new offer for an ongoing negotiation and triggers the next step.
        """
        negotiation_key = f"negotiation:{negotiation_id}"
        negotiation_data_json = redis_client.get(negotiation_key)

        if not negotiation_data_json:
            raise APIException(status_code=404, message="Negotiation not found or expired.")

        engine_data = json.loads(negotiation_data_json)
        engine = NegotiationEngine.from_dict(engine_data)

        stored_buyer_id = engine_data.get("buyer_id")
        stored_seller_id = engine_data.get("seller_id")

        if str(user_id) == stored_buyer_id:
            engine.buyer.set_price(offer_price)
        elif str(user_id) == stored_seller_id:
            engine.seller.set_price(offer_price)
        else:
            raise APIException(status_code=403, message="User is not a participant in this negotiation.")

        # Persist the updated engine state to Redis
        engine_data.update(engine.to_dict()) # Update engine state within the overall data
        redis_client.set(negotiation_key, json.dumps(engine_data))

        # Dispatch Kafka task to process this round
        await self.dispatch_negotiation_round_processing(negotiation_id)
        
        await self.notify_negotiation_update(engine, negotiation_id) # Notify participants via WebSocket

        return await self.get_negotiation_state(negotiation_id) # Return current state

    async def dispatch_negotiation_round_processing(self, negotiation_id: UUID):
        """
        Dispatches a Kafka message to asynchronously process a negotiation round.
        """
        producer_service = await get_kafka_producer_service()
        await producer_service.send_message(settings.KAFKA_TOPIC_NEGOTIATION, {
            "service": "NegotiatorService",
            "method": "process_negotiation_with_engine",
            "args": [str(negotiation_id)]
        })
        logger.info(f"Dispatched negotiation round processing for ID: {negotiation_id}")

    async def notify_negotiation_update(self, engine: NegotiationEngine, negotiation_id: UUID, event_type: str = "negotiation_update"):
        """
        Sends WebSocket updates to all participants of the negotiation.
        """
        # The engine_data (from Redis) now contains buyer_id and seller_id
        negotiation_key = f"negotiation:{negotiation_id}"
        negotiation_data_json = redis_client.get(negotiation_key)
        negotiation_meta = json.loads(negotiation_data_json)
        
        buyer_id = negotiation_meta.get("buyer_id")
        seller_id = negotiation_meta.get("seller_id")

        if not buyer_id or not seller_id:
            logger.error(f"Cannot send WebSocket update: Buyer or Seller ID missing for negotiation {negotiation_id}")
            return

        websocket_message = {
            "type": event_type,
            "negotiation_state": engine.to_dict(), # Send the engine state
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Send to buyer
        await websocket_manager.send_to_user(buyer_id, json.dumps(websocket_message))
        # Send to seller
        await websocket_manager.send_to_user(seller_id, json.dumps(websocket_message))
        
        logger.info(f"WebSocket update sent for negotiation {negotiation_id} to buyer {buyer_id} and seller {seller_id}")

    async def process_negotiation_with_engine(self, negotiation_id: UUID):
        """
        Processes a negotiation round using the NegotiationEngine stored in Redis.
        If a deal is reached, it stores the negotiated price temporarily for the user.
        """
        negotiation_key = f"negotiation:{negotiation_id}"
        negotiation_data_json = redis_client.get(negotiation_key)

        if not negotiation_data_json:
            logger.warning(f"Negotiation {negotiation_id} not found in Redis for processing. May be expired.")
            return

        engine_data = json.loads(negotiation_data_json)
        engine = NegotiationEngine.from_dict(engine_data)

        # Check if negotiation is already concluded
        if engine.finished:
            logger.info(f"Negotiation {negotiation_id} is already concluded. Skipping processing.")
            return

        # Fetch buyer and seller details to instantiate agents (only if not already in engine_data)
        # For simplicity, assuming user_id and product_variant_id can be derived from stored engine_data
        
        stored_buyer_id = engine_data.get("buyer_id")
        stored_product_variant_id = engine_data.get("product_variant_id")

        if not stored_buyer_id or not stored_product_variant_id:
            logger.error(f"Missing buyer_id or product_variant_id in Redis state for negotiation {negotiation_id}")
            return

        # Perform one step of negotiation
        result = engine.step()

        # Update Redis state
        engine_data.update(engine.to_dict()) # Update with latest engine state
        redis_client.set(negotiation_key, json.dumps(engine_data))

        if result["finished"]:
            # Deal reached, store final price temporarily for the user/product variant
            final_price = result["final_price"]
            
            temporary_price_key = f"{NEGOTIATED_PRICE_KEY_PREFIX}{stored_buyer_id}:{stored_product_variant_id}"
            redis_client.setex(temporary_price_key, NEGOTIATED_PRICE_EXPIRY_SECONDS, final_price)
            logger.info(f"Negotiation {negotiation_id} concluded with price: {final_price}. Stored for user {stored_buyer_id} and variant {stored_product_variant_id}.")
            
            # Optionally, notify the user that their negotiated price is available
            await self.notify_negotiation_update(engine, negotiation_id, event_type="negotiation_concluded")

        else:
            # Negotiation continues
            logger.info(f"Negotiation {negotiation_id} continues. Round {engine.round}.")
            await self.notify_negotiation_update(engine, negotiation_id) # Notify updates

        # Remove the negotiation state from Redis if finished (optional, or let expiry handle it)
        # If we rely on expiry, then this is not needed here.
        # if engine.finished:
        #    redis_client.delete(negotiation_key)

    async def clear_negotiation(self, negotiation_id: UUID):
        """Removes a negotiation from Redis."""
        negotiation_key = f"negotiation:{negotiation_id}"
        redis_client.delete(negotiation_key)
        logger.info(f"Negotiation {negotiation_id} cleared from Redis.")

    async def get_negotiated_price_for_user_product(self, user_id: UUID, product_variant_id: UUID) -> Optional[float]:
        """
        Retrieves a temporarily stored negotiated price for a given user and product variant.
        """
        temporary_price_key = f"{NEGOTIATED_PRICE_KEY_PREFIX}{user_id}:{product_variant_id}"
        price_str = redis_client.get(temporary_price_key)
        if price_str:
            return float(price_str)
        return None
