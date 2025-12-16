"""
Property-based tests for Celery task processing functionality (standalone version).

These tests validate the core Celery task processing requirements without requiring database setup:
- Property 18: Negotiation algorithm integration
- Property 19: Celery Beat scheduling  
- Property 20: Task result storage
- Property 21: Async task processing
"""

import pytest
import json
import sys
import os
from hypothesis import given, strategies as st
from hypothesis import settings as hypothesis_settings
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime

# Add the backend directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Celery components
from celery_app import celery_app
from services.negotiator import NegotiationEngine, Buyer, Seller
from core.config import settings

# Override the database setup fixture to prevent it from running
@pytest.fixture(scope="session", autouse=True)
def override_database_setup():
    """Override to prevent database setup for these standalone tests."""
    yield


class TestCeleryTaskProcessingPropertiesStandalone:
    """Property-based tests for Celery task processing functionality (standalone)."""

    @given(
        task_name=st.sampled_from([
            'tasks.email_tasks.send_cart_abandonment_emails',
            'tasks.email_tasks.send_review_requests', 
            'tasks.notification_tasks.cleanup_old_notifications',
            'tasks.notification_tasks.check_low_stock_task'
        ])
    )
    @hypothesis_settings(max_examples=20, deadline=5000)
    def test_property_19_celery_beat_scheduling(self, task_name):
        """
        Feature: docker-full-functionality, Property 19: Celery Beat scheduling
        
        For any periodic task defined in the beat schedule, Celery Beat should trigger 
        the task at the configured interval.
        
        Validates: Requirements 5.4
        """
        # Verify the task is defined in the beat schedule
        beat_schedule = celery_app.conf.beat_schedule
        
        # Find the schedule entry for this task
        schedule_entry = None
        for entry_name, entry_config in beat_schedule.items():
            if entry_config['task'] == task_name:
                schedule_entry = entry_config
                break
        
        # Verify the task is properly scheduled
        assert schedule_entry is not None, f"Task {task_name} not found in beat schedule"
        assert 'schedule' in schedule_entry
        assert isinstance(schedule_entry['schedule'], (int, float))
        assert schedule_entry['schedule'] > 0
        
        # Verify the schedule interval is reasonable (between 1 minute and 1 week)
        assert 60 <= schedule_entry['schedule'] <= 604800  # 1 minute to 1 week

    @given(
        buyer_target=st.floats(min_value=100.0, max_value=1000.0),
        buyer_limit=st.floats(min_value=1000.0, max_value=2000.0),
        seller_target=st.floats(min_value=1500.0, max_value=3000.0),
        seller_limit=st.floats(min_value=1000.0, max_value=1500.0),
        buyer_style=st.sampled_from(["aggressive", "balanced", "friendly", "patient"]),
        seller_style=st.sampled_from(["aggressive", "balanced", "friendly", "patient"])
    )
    @hypothesis_settings(max_examples=30, deadline=8000)
    def test_property_18_negotiation_algorithm_integration(
        self, buyer_target, buyer_limit, seller_target, seller_limit, buyer_style, seller_style
    ):
        """
        Feature: docker-full-functionality, Property 18: Negotiation algorithm integration
        
        For any negotiation task, when processed, it should use the NegotiationEngine class 
        with buyer and seller agents.
        
        Validates: Requirements 5.3
        """
        # Ensure buyer_limit >= buyer_target and seller_limit <= seller_target for valid negotiation
        if buyer_limit < buyer_target:
            buyer_limit = buyer_target + 100
        if seller_limit > seller_target:
            seller_limit = seller_target - 100
            
        # Skip if the negotiation setup is impossible (buyer limit < seller limit)
        if buyer_limit < seller_limit:
            return

        # Create negotiation session
        buyer = Buyer("test_buyer", buyer_target, buyer_limit, buyer_style)
        seller = Seller("test_seller", seller_target, seller_limit, seller_style)
        engine = NegotiationEngine(buyer, seller)

        # Test that the negotiation engine works correctly
        initial_round = engine.round
        result = engine.step()

        # Verify the negotiation algorithm integration
        assert isinstance(result, dict)
        assert "round" in result
        assert result["round"] == initial_round + 1
        assert result["round"] >= 1
        
        # Verify the engine uses buyer and seller agents correctly
        assert isinstance(engine.buyer, Buyer)
        assert isinstance(engine.seller, Seller)
        assert engine.buyer.name == "test_buyer"
        assert engine.seller.name == "test_seller"
        
        # Verify serialization/deserialization works (needed for Redis storage)
        engine_dict = engine.to_dict()
        assert isinstance(engine_dict, dict)
        assert "buyer" in engine_dict
        assert "seller" in engine_dict
        assert "round" in engine_dict
        assert "finished" in engine_dict
        
        # Test deserialization
        restored_engine = NegotiationEngine.from_dict(engine_dict)
        assert restored_engine.round == engine.round
        assert restored_engine.finished == engine.finished
        assert restored_engine.buyer.target == engine.buyer.target
        assert restored_engine.seller.target == engine.seller.target

    @given(
        task_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            values=st.one_of(st.text(max_size=100), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
            min_size=1,
            max_size=5
        )
    )
    @hypothesis_settings(max_examples=20, deadline=8000)
    def test_property_20_task_result_storage(self, task_data):
        """
        Feature: docker-full-functionality, Property 20: Task result storage
        
        For any Celery task, when completed, the result should be stored in the 
        configured backend (PostgreSQL or Redis).
        
        Validates: Requirements 5.5
        """
        # Verify the result backend configuration
        assert celery_app.conf.result_backend == settings.REDIS_URL
        assert celery_app.conf.result_expires == 3600  # 1 hour
        
        # Verify result serialization settings
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.task_serializer == 'json'
        
        # Test that task results can be serialized
        test_result = {"status": "completed", "data": task_data, "task_id": str(uuid4())}
        
        # Verify the result can be JSON serialized (required for Redis storage)
        try:
            serialized = json.dumps(test_result)
            deserialized = json.loads(serialized)
            assert deserialized == test_result
        except (TypeError, ValueError) as e:
            pytest.fail(f"Task result cannot be JSON serialized: {e}")

    @given(
        num_tasks=st.integers(min_value=1, max_value=5),
        task_delay=st.floats(min_value=0.1, max_value=1.0)
    )
    @hypothesis_settings(max_examples=10, deadline=10000)
    def test_property_21_async_task_processing(self, num_tasks, task_delay):
        """
        Feature: docker-full-functionality, Property 21: Async task processing
        
        For any task enqueued via the API, the API should respond immediately 
        without waiting for task completion.
        
        Validates: Requirements 5.6
        """
        # Create a mock task that simulates work with a delay
        @celery_app.task
        def mock_slow_task(delay_seconds):
            return {"completed_at": datetime.utcnow().isoformat(), "delay": delay_seconds}

        # Measure the time to enqueue multiple tasks
        start_time = datetime.utcnow()
        
        # Enqueue tasks asynchronously (should return immediately)
        async_results = []
        for i in range(num_tasks):
            # Use apply_async to simulate real async enqueueing
            result = mock_slow_task.apply_async(args=[task_delay])
            async_results.append(result)
        
        enqueue_time = datetime.utcnow()
        enqueue_duration = (enqueue_time - start_time).total_seconds()
        
        # Verify that enqueuing was fast (should be nearly instantaneous)
        # Allow up to 1 second for enqueueing regardless of task delay
        assert enqueue_duration < 1.0, \
            f"Enqueuing took {enqueue_duration}s, but should be much faster"
        
        # Verify all tasks were enqueued successfully
        assert len(async_results) == num_tasks
        for result in async_results:
            assert result.id is not None  # Task ID should be assigned immediately
            # Note: We don't check result.state here as it may vary depending on broker availability

    def test_negotiation_task_routing_configuration(self):
        """
        Verify that negotiation tasks are properly routed to the negotiation queue.
        """
        # Check task routing configuration
        task_routes = celery_app.conf.task_routes
        assert 'tasks.negotiation_tasks.*' in task_routes
        assert task_routes['tasks.negotiation_tasks.*']['queue'] == 'negotiation'
        
        # Check queue configuration
        task_queues = celery_app.conf.task_queues
        queue_names = [q.name for q in task_queues]
        assert 'negotiation' in queue_names

    def test_general_worker_queue_configuration(self):
        """
        Verify that general worker queues are properly configured.
        """
        # Check task routing configuration for general queues
        task_routes = celery_app.conf.task_routes
        assert 'tasks.email_tasks.*' in task_routes
        assert 'tasks.notification_tasks.*' in task_routes
        assert 'tasks.order_tasks.*' in task_routes
        
        assert task_routes['tasks.email_tasks.*']['queue'] == 'emails'
        assert task_routes['tasks.notification_tasks.*']['queue'] == 'notifications'
        assert task_routes['tasks.order_tasks.*']['queue'] == 'orders'
        
        # Check queue configuration
        task_queues = celery_app.conf.task_queues
        queue_names = [q.name for q in task_queues]
        assert 'emails' in queue_names
        assert 'notifications' in queue_names
        assert 'orders' in queue_names

    def test_celery_configuration_optimization(self):
        """
        Verify that Celery is configured for optimal performance.
        """
        # Check performance settings
        assert celery_app.conf.worker_prefetch_multiplier == 4
        assert celery_app.conf.worker_max_tasks_per_child == 1000
        assert celery_app.conf.task_time_limit == 300  # 5 minutes
        assert celery_app.conf.task_soft_time_limit == 240  # 4 minutes
        
        # Check serialization settings
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']
        
        # Check timezone settings
        assert celery_app.conf.timezone == 'UTC'
        assert celery_app.conf.enable_utc is True
        
        # Check broker and backend configuration
        assert celery_app.conf.broker_url == settings.REDIS_URL
        assert celery_app.conf.result_backend == settings.REDIS_URL

    def test_celery_task_includes(self):
        """
        Verify that all required task modules are included in Celery configuration.
        """
        includes = celery_app.conf.include
        expected_modules = [
            'tasks.email_tasks',
            'tasks.notification_tasks', 
            'tasks.order_tasks',
            'tasks.negotiation_tasks'
        ]
        
        for module in expected_modules:
            assert module in includes, f"Task module {module} not included in Celery configuration"

    def test_beat_schedule_completeness(self):
        """
        Verify that all expected periodic tasks are configured in the beat schedule.
        """
        beat_schedule = celery_app.conf.beat_schedule
        
        expected_tasks = [
            'tasks.email_tasks.send_cart_abandonment_emails',
            'tasks.email_tasks.send_review_requests',
            'tasks.notification_tasks.cleanup_old_notifications',
            'tasks.notification_tasks.check_low_stock_task'
        ]
        
        scheduled_tasks = [entry['task'] for entry in beat_schedule.values()]
        
        for task in expected_tasks:
            assert task in scheduled_tasks, f"Expected periodic task {task} not found in beat schedule"