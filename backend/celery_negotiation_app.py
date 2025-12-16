"""
Minimal Celery application configuration for negotiation worker only
"""
import asyncio
from celery import Celery
from kombu import Queue
from core.config import settings

# Create Celery app instance for negotiation worker
celery_app = Celery(
    'banwee_negotiation',
    broker=settings.REDIS_URL,  # Redis is used as the message broker for Celery tasks
    backend=settings.REDIS_URL, # Redis is used as the result backend for Celery tasks
    include=[
        'tasks.negotiation_tasks' # Include only negotiation-specific tasks
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization settings
    task_serializer='json',
    accept_content=['json'], # Specify accepted content types for tasks
    result_serializer='json',
    timezone='UTC', # Use UTC timezone for consistent task scheduling and logging
    enable_utc=True,
    
    # Task execution behavior
    task_track_started=True, # Enable tracking of task's STARTED state
    task_time_limit=300,  # Hard time limit for task execution (5 minutes)
    task_soft_time_limit=240,  # Soft time limit before a warning is issued (4 minutes)
    
    # Result backend settings
    result_expires=3600,  # Results will expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster', # For Redis Sentinel, if used
        'visibility_timeout': 3600, # How long a message remains visible to other workers if not acknowledged
    },
    
    # Worker performance settings
    worker_prefetch_multiplier=4, # How many tasks a worker can prefetch
    worker_max_tasks_per_child=1000, # Max tasks a worker can execute before restarting (helps with memory leaks)
    
    # Task routing configuration
    # This maps task modules to specific queues for organized processing.
    task_routes={
        'tasks.negotiation_tasks.*': {'queue': 'negotiation'}, # Route negotiation tasks to their dedicated queue
    },
    
    # Definition of task queues
    task_queues=(
        Queue('negotiation', routing_key='negotiation'), # Dedicated queue for negotiation tasks
    ),
)

# Helper function to run async tasks within a Celery worker context
def run_async_task(coro):
    """
    Runs an asynchronous coroutine within a new event loop.
    Useful for integrating async functions into synchronous Celery tasks.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

if __name__ == '__main__':
    celery_app.start()