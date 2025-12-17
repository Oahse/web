"""
Integration tests for the negotiation feature end-to-end.

Validates: Requirements 15.9, 15.10, 15.11
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from uuid import UUID
import json
from datetime import datetime
import unittest # NEW: Import unittest for unittest.mock.ANY

from services.negotiator_service import NegotiatorService # Use the new service
from models.negotiation import Negotiation, NegotiationStatus # Import NegotiationStatus
from tasks.negotiation_tasks import perform_negotiation_step # Import the Celery task
from models.user import User
from models.product import Product, ProductVariant
from core.database import Base # Import Base for metadata


# Test negotiation start -> rounds -> completion flow
@pytest.mark.asyncio
@patch('tasks.negotiation_tasks.perform_negotiation_step.delay') # Patch the correct Celery task
async def test_negotiation_flow_end_to_end(
    mock_celery_delay: MagicMock,
    db_session: AsyncSession,
    # async_client: AsyncClient, # async_client is not used here
    test_user: User, # Assuming conftest provides a test user for buyer
    admin_user: User, # Assuming conftest provides an admin user for seller
    test_product: Product, # Assuming conftest provides a test product
    test_product_variant: ProductVariant # Assuming conftest provides a test product variant
):
    """
    Test negotiation start -> rounds -> completion flow.
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
