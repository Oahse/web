import json
from celery import shared_task
import redis
import uuid

from core.config import settings
from services.negotiator import NegotiationEngine, Buyer, Seller
from backend.celery_app import celery_app # Assuming celery_app is defined here

# Initialize Redis client
# Using a dedicated connection for Celery tasks
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

@celery_app.task(bind=True) # Use celery_app.task decorator
def perform_negotiation_step(self, negotiation_id: str, buyer_new_target: float = None, seller_new_target: float = None):
    """
    Celery task to perform one step of the negotiation process.
    Retrieves negotiation state from Redis, performs the step, and saves the updated state back.
    :param self: The task instance.
    :param negotiation_id: The UUID of the negotiation session.
    :param buyer_new_target: Optional new target price for the buyer for this step.
    :param seller_new_target: Optional new target price for the seller for this step.
    :return: A dictionary representing the current state of the negotiation.
    """
    negotiation_key = f"negotiation:{negotiation_id}"
    negotiation_data_json = redis_client.get(negotiation_key)

    if not negotiation_data_json:
        # Log error, negotiation not found. Update task state for visibility.
        self.update_state(state='FAILURE', meta={'message': f"Negotiation {negotiation_id} not found in Redis."})
        # It's better to raise an exception for unrecoverable errors in Celery tasks
        raise ValueError(f"Negotiation {negotiation_id} not found.")

    negotiation_data = json.loads(negotiation_data_json)
    
    # Reconstruct NegotiationEngine from stored data
    engine = NegotiationEngine.from_dict(negotiation_data)

    # Apply optional new target prices before performing the step
    if buyer_new_target is not None:
        engine.buyer.set_price(buyer_new_target)
    if seller_new_target is not None:
        engine.seller.set_price(seller_new_target)

    # Perform one step of negotiation
    result = engine.step()

    # Save updated negotiation state back to Redis
    updated_negotiation_data_json = json.dumps(engine.to_dict())
    redis_client.set(negotiation_key, updated_negotiation_data_json)

    # If negotiation is finished, delete the state from Redis
    if engine.finished:
        redis_client.delete(negotiation_key)
        self.update_state(state='SUCCESS', meta=result) # Update task state to SUCCESS
        return result
    else:
        self.update_state(state='PENDING', meta=result) # Update task state to PENDING if not finished
        return result
