"""
Integration tests for the negotiation feature end-to-end.

Task 12.5: Write integration test for negotiation feature end-to-end
- Test negotiation start → rounds → completion flow
- Verify negotiation tasks route to dedicated worker
- Test WebSocket updates during negotiation

Validates: Requirements 15.9, 15.10, 15.11
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from uuid import UUID, uuid4
import json
from datetime import datetime
import unittest
import redis
import time

from negotiator.service import NegotiatorService
from models.negotiation import Negotiation, NegotiationStatus
from tasks.negotiation_tasks import perform_negotiation_step
from models.user import User
from models.product import Product, ProductVariant
from core.database import Base
from core.config import settings
from negotiator.core import NegotiationEngine, Buyer, Seller


class TestNegotiationIntegrationEndToEnd:
    """
    Integration tests for negotiation feature end-to-end.
    Task 12.5: Write integration test for negotiation feature end-to-end
    """

    @pytest.mark.asyncio
    async def test_negotiation_service_integration_flow(
        self,
        db_session: AsyncSession,
        test_user: User,
        admin_user: User,
        test_product: Product,
        test_product_variant: ProductVariant
    ):
        """
        Feature: docker-full-functionality, Task 12.5
        
        Test complete negotiation flow using service layer:
        1. Create negotiation via service
        2. Process multiple rounds via service
        3. Complete negotiation
        4. Verify all data persistence and WebSocket updates
        
        Validates: Requirements 15.9, 15.10, 15.11
        """
        negotiator_service = NegotiatorService(db_session)
        
        # Mock Celery task to avoid actual async execution during test
        with patch('tasks.negotiation_tasks.perform_negotiation_step.delay') as mock_celery_delay:
            # Mock WebSocket manager to verify updates
            with patch('services.negotiator_service.websocket_manager.send_to_user', new_callable=AsyncMock) as mock_websocket:
                
                # 1. Create negotiation via service
                initial_offer = 100.0
                negotiation = await negotiator_service.create_negotiation(
                    buyer_id=test_user.id,
                    seller_id=admin_user.id,
                    product_id=test_product.id,
                    product_variant_id=test_product_variant.id,
                    quantity=1,
                    initial_offer=initial_offer
                )
                
                # Verify negotiation was created correctly
                assert negotiation.id is not None
                assert negotiation.buyer_id == test_user.id
                assert negotiation.seller_id == admin_user.id
                assert negotiation.current_price == initial_offer
                assert negotiation.status == NegotiationStatus.PENDING
                
                # Verify Celery task was dispatched for initial step
                mock_celery_delay.assert_called_once_with(str(negotiation.id))
                mock_celery_delay.reset_mock()
                
                # 2. Record buyer offer (simulating negotiation round)
                buyer_offer = 95.0
                updated_negotiation = await negotiator_service.record_offer(
                    negotiation_id=negotiation.id,
                    user_id=test_user.id,
                    offer_price=buyer_offer
                )
                
                # Verify offer was recorded
                assert updated_negotiation.current_price == buyer_offer
                assert updated_negotiation.last_offer_by == test_user.id
                assert updated_negotiation.status == NegotiationStatus.IN_PROGRESS
                assert len(updated_negotiation.offers) == 2  # Initial + buyer offer
                
                # Verify Celery task was dispatched for processing
                mock_celery_delay.assert_called_once_with(str(negotiation.id))
                mock_celery_delay.reset_mock()
                
                # Verify WebSocket updates were sent
                assert mock_websocket.call_count >= 2  # Buyer and seller notifications
                
                # 3. Record seller counter-offer
                seller_offer = 97.0
                counter_negotiation = await negotiator_service.record_offer(
                    negotiation_id=negotiation.id,
                    user_id=admin_user.id,
                    offer_price=seller_offer
                )
                
                # Verify counter-offer was recorded
                assert counter_negotiation.current_price == seller_offer
                assert counter_negotiation.last_offer_by == admin_user.id
                assert counter_negotiation.status == NegotiationStatus.COUNTERED
                assert len(counter_negotiation.offers) == 3  # Initial + buyer + seller
                
                # 4. Complete negotiation
                final_negotiation = await negotiator_service.update_negotiation_status(
                    negotiation_id=negotiation.id,
                    new_status=NegotiationStatus.ACCEPTED
                )
                
                # Verify completion
                assert final_negotiation.status == NegotiationStatus.ACCEPTED
                assert final_negotiation.end_time is not None
                
                # Verify WebSocket status update was sent
                status_calls = [call for call in mock_websocket.call_args_list 
                              if 'negotiation_status_update' in str(call)]
                assert len(status_calls) >= 2  # Buyer and seller status updates
                
                print("✅ Complete negotiation service integration test passed")

    @pytest.mark.asyncio
    async def test_negotiation_task_routing_to_dedicated_worker(self):
        """
        Feature: docker-full-functionality, Task 12.5
        
        Verify negotiation tasks route to dedicated worker queue.
        Test that negotiation tasks are properly configured to use the negotiation queue.
        
        Validates: Requirements 15.10
        """
        # Import Celery apps to verify configuration
        from celery_app import celery_app as general_celery_app
        from celery_negotiation_app import celery_app as negotiation_celery_app
        
        # 1. Verify general Celery app routes negotiation tasks to negotiation queue
        general_task_routes = general_celery_app.conf.task_routes
        general_queues = [q.name for q in general_celery_app.conf.task_queues]
        
        # General app should route all task types to their respective queues
        assert 'tasks.email_tasks.*' in general_task_routes
        assert 'tasks.notification_tasks.*' in general_task_routes
        assert 'tasks.order_tasks.*' in general_task_routes
        assert 'tasks.negotiation_tasks.*' in general_task_routes
        
        # Verify negotiation tasks are routed to negotiation queue
        assert general_task_routes['tasks.negotiation_tasks.*']['queue'] == 'negotiation'
        
        # All queues should be defined in general app
        assert 'emails' in general_queues
        assert 'notifications' in general_queues
        assert 'orders' in general_queues
        assert 'negotiation' in general_queues
        
        # 2. Verify negotiation Celery app handles ONLY negotiation tasks
        negotiation_task_routes = negotiation_celery_app.conf.task_routes
        negotiation_queues = [q.name for q in negotiation_celery_app.conf.task_queues]
        
        # Negotiation worker should handle only negotiation tasks
        assert 'tasks.negotiation_tasks.*' in negotiation_task_routes
        assert negotiation_task_routes['tasks.negotiation_tasks.*']['queue'] == 'negotiation'
        
        assert 'negotiation' in negotiation_queues
        assert len(negotiation_queues) == 1  # Only negotiation queue
        
        # 3. Verify negotiation task is registered in negotiation app
        negotiation_registered_tasks = negotiation_celery_app.tasks
        assert 'tasks.negotiation_tasks.perform_negotiation_step' in negotiation_registered_tasks
        
        # 4. Verify task routing works correctly
        # Both apps should route negotiation tasks to the same queue
        general_negotiation_queue = general_task_routes['tasks.negotiation_tasks.*']['queue']
        negotiation_negotiation_queue = negotiation_task_routes['tasks.negotiation_tasks.*']['queue']
        assert general_negotiation_queue == negotiation_negotiation_queue == 'negotiation'
        
        # 5. Verify negotiation app doesn't handle other task types
        # Negotiation app should not have routes for other task types
        for route_pattern in negotiation_task_routes:
            assert 'email_tasks' not in route_pattern, f"Negotiation app should not route email tasks: {route_pattern}"
            assert 'notification_tasks' not in route_pattern, f"Negotiation app should not route notification tasks: {route_pattern}"
            assert 'order_tasks' not in route_pattern, f"Negotiation app should not route order tasks: {route_pattern}"
        
        print("✅ Negotiation task routing verification test passed")

    @pytest.mark.asyncio
    async def test_negotiation_engine_algorithm_integration(self):
        """
        Feature: docker-full-functionality, Task 12.5
        
        Test negotiation algorithm integration and correctness.
        Verify that the negotiation engine works correctly with serialization/deserialization.
        
        Validates: Requirements 15.9, 15.11
        """
        # Initialize negotiation engine
        buyer = Buyer(
            name="Test Buyer",
            target_price=80.0,
            limit_price=100.0,
            style="balanced"
        )
        seller = Seller(
            name="Test Seller",
            target_price=120.0,
            limit_price=90.0,
            style="patient"
        )
        engine = NegotiationEngine(buyer, seller)
        
        # 1. Test serialization/deserialization (key for Redis storage)
        engine_dict = engine.to_dict()
        assert "buyer" in engine_dict
        assert "seller" in engine_dict
        assert "round" in engine_dict
        assert "finished" in engine_dict
        assert engine_dict["round"] == 0
        assert engine_dict["finished"] is False
        
        # Reconstruct engine from dict
        reconstructed_engine = NegotiationEngine.from_dict(engine_dict)
        assert reconstructed_engine.round == engine.round
        assert reconstructed_engine.finished == engine.finished
        assert reconstructed_engine.buyer.target == engine.buyer.target
        assert reconstructed_engine.seller.target == engine.seller.target
        
        # 2. Test negotiation algorithm execution
        max_rounds = 10
        current_round = 0
        
        while current_round < max_rounds and not engine.finished:
            # Execute one negotiation step
            result = engine.step()
            current_round += 1
            
            # Verify result structure
            assert isinstance(result, dict)
            assert "round" in result
            assert "finished" in result
            assert result["round"] == current_round
            
            # If finished, verify final price
            if result.get("finished", False):
                assert "final_price" in result
                assert isinstance(result["final_price"], (int, float))
                final_price = result["final_price"]
                # Final price should be within reasonable bounds
                assert 80.0 <= final_price <= 120.0, f"Final price {final_price} outside expected range"
                break
            else:
                # If not finished, should have current offers
                assert "buyer_offer" in result or "seller_offer" in result
        
        # 3. Test serialization after negotiation steps
        if engine.finished:
            final_dict = engine.to_dict()
            assert final_dict["finished"] is True
            assert final_dict["final_price"] is not None
            
            # Reconstruct final engine
            final_reconstructed = NegotiationEngine.from_dict(final_dict)
            assert final_reconstructed.finished is True
            assert final_reconstructed.final_price == engine.final_price
        
        # 4. Test negotiation algorithm properties
        # Verify buyer and seller agents maintain their constraints
        assert engine.buyer.target >= 80.0  # Buyer shouldn't go below initial target
        assert engine.seller.target <= 120.0  # Seller shouldn't go above initial target
        
        print(f"✅ Negotiation algorithm integration test passed after {current_round} rounds")
        
        # 5. Test edge case: immediate deal closure
        quick_buyer = Buyer("Quick Buyer", target_price=100.0, limit_price=110.0, style="friendly")
        quick_seller = Seller("Quick Seller", target_price=95.0, limit_price=90.0, style="friendly")
        quick_engine = NegotiationEngine(quick_buyer, quick_seller)
        
        # This should close quickly since buyer target (100) > seller target (95)
        quick_result = quick_engine.step()
        assert quick_result["finished"] is True
        assert 90.0 <= quick_result["final_price"] <= 110.0
        
        print("✅ Quick negotiation closure test passed")

    @pytest.mark.asyncio
    async def test_websocket_updates_during_negotiation_flow(
        self,
        db_session: AsyncSession,
        test_user: User,
        admin_user: User,
        test_product: Product,
        test_product_variant: ProductVariant
    ):
        """
        Feature: docker-full-functionality, Task 12.5
        
        Test WebSocket updates during complete negotiation flow.
        Verify that WebSocket messages are sent at each stage of negotiation.
        
        Validates: Requirements 15.11
        """
        negotiator_service = NegotiatorService(db_session)
        
        # Mock WebSocket manager to capture all messages
        websocket_messages = []
        
        async def mock_send_to_user(user_id: str, message: str):
            websocket_messages.append({
                "user_id": user_id,
                "message": json.loads(message),
                "timestamp": datetime.now().isoformat()
            })
        
        with patch('services.negotiator_service.websocket_manager.send_to_user', side_effect=mock_send_to_user):
            # Mock Celery task dispatch
            with patch('tasks.negotiation_tasks.perform_negotiation_step.delay') as mock_celery_delay:
                
                # 1. Create negotiation (should trigger WebSocket for creation)
                negotiation = await negotiator_service.create_negotiation(
                    buyer_id=test_user.id,
                    seller_id=admin_user.id,
                    product_id=test_product.id,
                    product_variant_id=test_product_variant.id,
                    quantity=1,
                    initial_offer=100.0
                )
                
                # Verify Celery task was dispatched
                mock_celery_delay.assert_called_once_with(str(negotiation.id))
                mock_celery_delay.reset_mock()
                
                # 2. Record buyer offer (should trigger WebSocket updates)
                await negotiator_service.record_offer(
                    negotiation_id=negotiation.id,
                    user_id=test_user.id,
                    offer_price=95.0
                )
                
                # Verify WebSocket messages were sent
                assert len(websocket_messages) >= 2  # At least buyer and seller notifications
                
                # Check buyer received update
                buyer_messages = [msg for msg in websocket_messages if msg["user_id"] == str(test_user.id)]
                assert len(buyer_messages) >= 1
                
                buyer_msg = buyer_messages[0]["message"]
                assert buyer_msg["type"] == "negotiation_update"
                assert "negotiation" in buyer_msg
                assert buyer_msg["negotiation"]["current_price"] == 95.0
                
                # Check seller received update
                seller_messages = [msg for msg in websocket_messages if msg["user_id"] == str(admin_user.id)]
                assert len(seller_messages) >= 1
                
                seller_msg = seller_messages[0]["message"]
                assert seller_msg["type"] == "negotiation_update"
                assert "negotiation" in seller_msg
                assert seller_msg["negotiation"]["current_price"] == 95.0
                
                websocket_messages.clear()  # Clear for next test
                
                # 3. Record seller counter-offer (should trigger more WebSocket updates)
                await negotiator_service.record_offer(
                    negotiation_id=negotiation.id,
                    user_id=admin_user.id,
                    offer_price=98.0
                )
                
                # Verify more WebSocket messages
                assert len(websocket_messages) >= 2
                
                # 4. Update negotiation status (should trigger status update WebSocket)
                await negotiator_service.update_negotiation_status(
                    negotiation_id=negotiation.id,
                    new_status=NegotiationStatus.ACCEPTED
                )
                
                # Verify status update WebSocket messages
                status_messages = [msg for msg in websocket_messages if msg["message"]["type"] == "negotiation_status_update"]
                assert len(status_messages) >= 2  # Buyer and seller
                
                for status_msg in status_messages:
                    assert status_msg["message"]["negotiation"]["status"] == "accepted"
                    assert status_msg["message"]["negotiation"]["end_time"] is not None
                
                print("✅ WebSocket updates during negotiation flow test passed")

    @pytest.mark.asyncio
    async def test_negotiation_database_service_integration(
        self,
        db_session: AsyncSession,
        test_user: User,
        admin_user: User,
        test_product: Product,
        test_product_variant: ProductVariant
    ):
        """
        Feature: docker-full-functionality, Task 12.5
        
        Test negotiation database service integration end-to-end.
        Verify all database operations work correctly in the negotiation flow.
        
        Validates: Requirements 15.9
        """
        negotiator_service = NegotiatorService(db_session)
        
        # Mock Celery and WebSocket to focus on database operations
        with patch('tasks.negotiation_tasks.perform_negotiation_step.delay'):
            with patch('services.negotiator_service.websocket_manager.send_to_user', new_callable=AsyncMock):
                
                # 1. Test negotiation creation and database persistence
                initial_offer = 100.0
                negotiation = await negotiator_service.create_negotiation(
                    buyer_id=test_user.id,
                    seller_id=admin_user.id,
                    product_id=test_product.id,
                    product_variant_id=test_product_variant.id,
                    quantity=2,
                    initial_offer=initial_offer
                )
                
                # Verify negotiation was created correctly
                assert negotiation.id is not None
                assert negotiation.buyer_id == test_user.id
                assert negotiation.seller_id == admin_user.id
                assert negotiation.product_id == test_product.id
                assert negotiation.product_variant_id == test_product_variant.id
                assert negotiation.quantity == 2
                assert negotiation.initial_offer == initial_offer
                assert negotiation.current_price == initial_offer
                assert negotiation.status == NegotiationStatus.PENDING
                assert len(negotiation.offers) == 1
                assert negotiation.offers[0]["user_id"] == str(test_user.id)
                assert negotiation.offers[0]["offer_price"] == initial_offer
                
                # 2. Test negotiation retrieval
                retrieved_negotiation = await negotiator_service.get_negotiation_by_id(negotiation.id)
                assert retrieved_negotiation.id == negotiation.id
                assert retrieved_negotiation.buyer_id == test_user.id
                assert retrieved_negotiation.seller_id == admin_user.id
                
                # 3. Test offer recording and database updates
                buyer_offer = 95.0
                updated_negotiation = await negotiator_service.record_offer(
                    negotiation_id=negotiation.id,
                    user_id=test_user.id,
                    offer_price=buyer_offer
                )
                
                assert updated_negotiation.current_price == buyer_offer
                assert updated_negotiation.last_offer_by == test_user.id
                assert updated_negotiation.status == NegotiationStatus.IN_PROGRESS
                assert len(updated_negotiation.offers) == 2
                assert updated_negotiation.offers[1]["user_id"] == str(test_user.id)
                assert updated_negotiation.offers[1]["offer_price"] == buyer_offer
                
                # 4. Test seller counter-offer
                seller_offer = 97.0
                counter_negotiation = await negotiator_service.record_offer(
                    negotiation_id=negotiation.id,
                    user_id=admin_user.id,
                    offer_price=seller_offer
                )
                
                assert counter_negotiation.current_price == seller_offer
                assert counter_negotiation.last_offer_by == admin_user.id
                assert counter_negotiation.status == NegotiationStatus.COUNTERED
                assert len(counter_negotiation.offers) == 3
                
                # 5. Test status update and completion
                final_negotiation = await negotiator_service.update_negotiation_status(
                    negotiation_id=negotiation.id,
                    new_status=NegotiationStatus.ACCEPTED
                )
                
                assert final_negotiation.status == NegotiationStatus.ACCEPTED
                assert final_negotiation.end_time is not None
                
                # 6. Verify data persistence by retrieving again
                final_retrieved = await negotiator_service.get_negotiation_by_id(negotiation.id)
                assert final_retrieved.status == NegotiationStatus.ACCEPTED
                assert final_retrieved.end_time is not None
                assert len(final_retrieved.offers) == 3
                
                print("✅ Negotiation database service integration test passed")


# Legacy tests (keeping for backward compatibility)
# Test negotiation start -> rounds -> completion flow
@pytest.mark.asyncio
@patch('tasks.negotiation_tasks.perform_negotiation_step.delay')
async def test_negotiation_flow_end_to_end(
    mock_celery_delay: MagicMock,
    db_session: AsyncSession,
    test_user: User,
    admin_user: User,
    test_product: Product,
    test_product_variant: ProductVariant
):
    """
    Legacy test: Test negotiation start -> rounds -> completion flow.
    """
    negotiator_service = NegotiatorService(db_session)
    
    buyer_id = test_user.id
    seller_id = admin_user.id
    product_id = test_product.id
    product_variant_id = test_product_variant.id
    initial_offer = 100.0
    
    # 1. Simulate negotiation initiation
    created_negotiation = await negotiator_service.create_negotiation(
        buyer_id=buyer_id,
        seller_id=seller_id,
        product_id=product_id,
        product_variant_id=product_variant_id,
        quantity=1,
        initial_offer=initial_offer
    )
    
    assert created_negotiation.buyer_id == buyer_id
    assert created_negotiation.seller_id == seller_id
    assert created_negotiation.product_id == product_id
    assert created_negotiation.current_price == initial_offer
    assert created_negotiation.status == NegotiationStatus.PENDING
    
    # After initial offer, the Celery task to process the round should be dispatched
    mock_celery_delay.assert_called_once_with(str(created_negotiation.id))
    mock_celery_delay.reset_mock() # Reset mock for next round

    # 2. Simulate buyer making a counter-offer
    offer_price_round1 = 95.0
    with patch('services.negotiator_service.websocket_manager.send_to_user', new_callable=AsyncMock) as mock_send_to_user: # Corrected patch target
        updated_negotiation_buyer_offer = await negotiator_service.record_offer(
            negotiation_id=created_negotiation.id,
            user_id=buyer_id,
            offer_price=offer_price_round1
        )
        assert updated_negotiation_buyer_offer.current_price == offer_price_round1
        assert updated_negotiation_buyer_offer.last_offer_by == buyer_id
        assert updated_negotiation_buyer_offer.status == NegotiationStatus.IN_PROGRESS # Adjusted assertion to expect IN_PROGRESS for the first offer
        
        # Verify WebSocket update was sent
        assert mock_send_to_user.call_count == 2 # Called for buyer and seller
        
        # Helper to check JSON content without strict timestamp comparison
        def assert_json_message_contains(mock_call, expected_negotiation_dict, expected_event_type="negotiation_update"):
            args, _ = mock_call
            message_str = args[1]
            message_dict = json.loads(message_str)
            assert message_dict["type"] == expected_event_type
            
            # Compare relevant fields of negotiation dict, ignore dynamic timestamps
            negotiation_in_message = message_dict["negotiation"]
            for key in expected_negotiation_dict:
                if key not in ["created_at", "updated_at", "start_time", "end_time"]:
                    assert negotiation_in_message[key] == expected_negotiation_dict[key], f"Mismatch for key {key}"
            
            # Assert timestamps are present and valid format
            for key in ["created_at", "updated_at", "start_time"]:
                assert key in negotiation_in_message
                datetime.fromisoformat(negotiation_in_message[key].replace('Z', '+00:00')) # Ensure it's a valid ISO format
        
        # Check calls for buyer
        mock_send_to_user.assert_any_call(
            str(buyer_id), 
            unittest.mock.ANY # Use ANY because timestamp will be different
        )
        assert_json_message_contains(mock_send_to_user.call_args_list[0], updated_negotiation_buyer_offer.to_dict(), "negotiation_update")

        # Check calls for seller
        mock_send_to_user.assert_any_call(
            str(seller_id), 
            unittest.mock.ANY # Use ANY because timestamp will be different
        )
        assert_json_message_contains(mock_send_to_user.call_args_list[1], updated_negotiation_buyer_offer.to_dict(), "negotiation_update")

        mock_send_to_user.reset_mock() 
    
    mock_celery_delay.assert_called_once_with(str(created_negotiation.id))
    mock_celery_delay.reset_mock()

    # 3. Simulate seller making a counter-offer (assuming previous offer was from buyer)
    counter_offer_price_round2 = 97.0
    with patch('services.negotiator_service.websocket_manager.send_to_user', new_callable=AsyncMock) as mock_send_to_user: # Corrected patch target
        updated_negotiation_seller_offer = await negotiator_service.record_offer(
            negotiation_id=created_negotiation.id,
            user_id=seller_id,
            offer_price=counter_offer_price_round2
        )
        assert updated_negotiation_seller_offer.current_price == counter_offer_price_round2
        assert updated_negotiation_seller_offer.last_offer_by == seller_id
        assert updated_negotiation_seller_offer.status == NegotiationStatus.COUNTERED

        # Verify WebSocket update was sent
        assert mock_send_to_user.call_count == 2 # Called for buyer and seller
        mock_send_to_user.assert_any_call(
            str(buyer_id), 
            unittest.mock.ANY
        )
        assert_json_message_contains(mock_send_to_user.call_args_list[0], updated_negotiation_seller_offer.to_dict(), "negotiation_update")

        mock_send_to_user.assert_any_call(
            str(seller_id), 
            unittest.mock.ANY
        )
        assert_json_message_contains(mock_send_to_user.call_args_list[1], updated_negotiation_seller_offer.to_dict(), "negotiation_update")

        mock_send_to_user.reset_mock() 
    
    mock_celery_delay.assert_called_once_with(str(created_negotiation.id))
    mock_celery_delay.reset_mock()

    # 4. Simulate negotiation completion (buyer accepts)
    with patch('services.negotiator_service.websocket_manager.send_to_user', new_callable=AsyncMock) as mock_send_to_user: # Corrected patch target
        completed_negotiation = await negotiator_service.update_negotiation_status(
            negotiation_id=created_negotiation.id,
            new_status=NegotiationStatus.ACCEPTED
        )
        assert completed_negotiation.status == NegotiationStatus.ACCEPTED
        assert completed_negotiation.end_time is not None

        # Verify WebSocket update was sent for status change
        assert mock_send_to_user.call_count == 2 # Called for buyer and seller
        mock_send_to_user.assert_any_call(
            str(buyer_id), 
            unittest.mock.ANY
        )
        assert_json_message_contains(mock_send_to_user.call_args_list[0], completed_negotiation.to_dict(), "negotiation_status_update")

        mock_send_to_user.assert_any_call(
            str(seller_id), 
            unittest.mock.ANY
        )
        assert_json_message_contains(mock_send_to_user.call_args_list[1], completed_negotiation.to_dict(), "negotiation_status_update")
    
    print(f"\nNegotiation flow end-to-end test passed for negotiation ID: {created_negotiation.id}")


# Verify negotiation tasks route to dedicated worker
@pytest.mark.asyncio
@patch('tasks.negotiation_tasks.perform_negotiation_step.delay') # Patch the correct Celery task
async def test_negotiation_task_routing(mock_celery_delay: MagicMock, db_session: AsyncSession):
    """
    Verify negotiation tasks route to dedicated worker.
    This test assumes that the NegotiatorService dispatches tasks to the Celery worker.
    """
    negotiator_service = NegotiatorService(db_session)
    negotiation_id = UUID("deadbeef-dead-beef-dead-beef00000000")
    
    # Simulate a call to a method in NegotiatorService that would trigger the Celery task
    negotiator_service.dispatch_negotiation_round_processing(negotiation_id)
    
    # Assert that the Celery task was called correctly with the negotiation ID
    mock_celery_delay.assert_called_once_with(str(negotiation_id))
        
    print("\nNegotiation task routing test passed (mocked Celery task call).")


# Test WebSocket updates during negotiation
@pytest.mark.asyncio
async def test_websocket_updates_during_negotiation(db_session: AsyncSession):
    """
    Test WebSocket updates during negotiation.
    This test verifies that the websocket manager's send_to_user is called with negotiation updates.
    """
    negotiator_service = NegotiatorService(db_session)
    negotiation_id = UUID("deadbeef-dead-beef-dead-beef00000000")
    buyer_id = UUID("12345678-1234-5678-1234-567812345678")
    seller_id = UUID("87654321-4321-8765-4321-876543215678")
    
    mock_negotiation = MagicMock(spec=Negotiation)
    mock_negotiation.id = negotiation_id
    mock_negotiation.buyer_id = buyer_id
    mock_negotiation.seller_id = seller_id
    mock_negotiation.to_dict.return_value = { # Mock the to_dict method
        "id": str(negotiation_id),
        "buyer_id": str(buyer_id),
        "seller_id": str(seller_id),
        "status": "in_progress",
        "current_price": 95.0,
        "last_offer_by": str(buyer_id),
        "offers": [],
        "start_time": datetime.now().isoformat(), # Add dynamic timestamps to mock
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "end_time": None
    }

    with patch('services.negotiator_service.websocket_manager.send_to_user', new_callable=AsyncMock) as mock_send_to_user: # Corrected patch target
        # Simulate a negotiation update that would trigger WebSocket messages
        # For instance, a new offer being recorded
        await negotiator_service.notify_negotiation_update(mock_negotiation)
        
        # Assert that send_to_user was called for both buyer and seller
        assert mock_send_to_user.call_count == 2 # Called for buyer and seller
        
        # Helper to check JSON content without strict timestamp comparison
        def assert_json_message_contains(mock_call, expected_negotiation_dict, expected_event_type="negotiation_update"):
            args, _ = mock_call
            message_str = args[1]
            message_dict = json.loads(message_str)
            assert message_dict["type"] == expected_event_type
            
            # Compare relevant fields of negotiation dict, ignore dynamic timestamps
            negotiation_in_message = message_dict["negotiation"]
            for key in expected_negotiation_dict:
                if key not in ["created_at", "updated_at", "start_time", "end_time"]:
                    assert negotiation_in_message[key] == expected_negotiation_dict[key], f"Mismatch for key {key}"
            
            # Assert timestamps are present and valid format
            for key in ["created_at", "updated_at", "start_time"]:
                assert key in negotiation_in_message
                datetime.fromisoformat(negotiation_in_message[key].replace('Z', '+00:00')) # Ensure it's a valid ISO format
        
        # Check calls for buyer
        mock_send_to_user.assert_any_call(
            str(buyer_id), 
            unittest.mock.ANY # Use ANY because timestamp will be different
        )
        assert_json_message_contains(mock_send_to_user.call_args_list[0], mock_negotiation.to_dict.return_value, "negotiation_update")

        # Check calls for seller
        mock_send_to_user.assert_any_call(
            str(seller_id), 
            unittest.mock.ANY # Use ANY because timestamp will be different
        )
        assert_json_message_contains(mock_send_to_user.call_args_list[1], mock_negotiation.to_dict.return_value, "negotiation_update")
        
    print("\nWebSocket updates during negotiation test passed (mocked WebSocket calls).")
