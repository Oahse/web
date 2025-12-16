import json
from celery import shared_task
import redis
import uuid

from core.config import settings
from services.negotiator import NegotiationEngine, Buyer, Seller
from celery_negotiation_app import celery_app # Use negotiation-specific celery app

# Initialize Redis client for accessing negotiation states
# This client is shared between FastAPI (routes) and Celery (tasks) to
# store and retrieve the serialized state of NegotiationEngine instances.
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

@celery_app.task(bind=True) # Use celery_app.task decorator
def perform_negotiation_step(self, negotiation_id: str, buyer_new_target: float = None, seller_new_target: float = None):
    """
    Celery task to perform one step of the negotiation process.
    This task is designed to be executed asynchronously, typically triggered by a FastAPI endpoint.
    It retrieves the current negotiation state from Redis, performs a single negotiation step,
    persists the updated state back to Redis, and cleans up the state if the negotiation concludes.
    
    :param self: The task instance provided by Celery.
    :param negotiation_id: The UUID of the negotiation session to process.
    :param buyer_new_target: Optional new target price for the buyer for this step.
    :param seller_new_target: Optional new target price for the seller for this step.
    :return: A dictionary representing the current state of the negotiation after the step.
    """
    negotiation_key = f"negotiation:{negotiation_id}"
    negotiation_data_json = redis_client.get(negotiation_key)

    if not negotiation_data_json:
        # If the negotiation state is not found in Redis, it's an unrecoverable error for this task.
        self.update_state(state='FAILURE', meta={'message': f"Negotiation {negotiation_id} not found in Redis."})
        raise ValueError(f"Negotiation {negotiation_id} not found.")

    # Deserialize the negotiation state from JSON stored in Redis
    negotiation_data = json.loads(negotiation_data_json)
    
    # Reconstruct NegotiationEngine instance from the deserialized data
    engine = NegotiationEngine.from_dict(negotiation_data)

    # Apply any new target prices provided for this specific step
    if buyer_new_target is not None:
        engine.buyer.set_price(buyer_new_target)
    if seller_new_target is not None:
        engine.seller.set_price(seller_new_target)

    # Perform one step of the negotiation algorithm
    result = engine.step()

    # Serialize the updated NegotiationEngine state back to JSON
    updated_negotiation_data_json = json.dumps(engine.to_dict())
    # Persist the updated state back to Redis
    redis_client.set(negotiation_key, updated_negotiation_data_json)

    # If negotiation is finished, delete the state from Redis to clean up.
    # The task state is updated to SUCCESS or PENDING accordingly.
    if engine.finished:
        redis_client.delete(negotiation_key) # Remove the negotiation state from Redis
        self.update_state(state='SUCCESS', meta=result) # Update Celery task state
        return result
    else:
        self.update_state(state='PENDING', meta=result) # Update Celery task state
        return result