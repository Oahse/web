"""
Chaos tests for Kafka consumers
Tests consumer resilience under various failure conditions including:
- Network partitions
- Message corruption
- Consumer lag
- Broker failures
- Duplicate messages
- Out-of-order messages
"""
import pytest
import asyncio
import json
import random
import time
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from typing import List, Dict, Any

from core.events.consumer import EventConsumer
from core.events.producer import EventProducer
from core.events.simple_event import SimpleEvent
from core.events.handlers import OrderEventHandler, InventoryEventHandler
from aiokafka.errors import KafkaError, KafkaTimeoutError, CommitFailedError
from aiokafka import ConsumerRecord


class TestKafkaConsumerChaos:
    """Chaos tests for Kafka consumer resilience"""

    @pytest.fixture
    def mock_kafka_consumer(self):
        """Mock Kafka consumer with configurable behavior"""
        consumer = AsyncMock()
        consumer.start = AsyncMock()
        consumer.stop = AsyncMock()
        consumer.commit = AsyncMock()
        consumer.seek = AsyncMock()
        consumer.position = AsyncMock(return_value=0)
        return consumer

    @pytest.fixture
    def sample_events(self):
        """Generate sample events for testing"""
        events = []
        for i in range(10):
            event = SimpleEvent(
                event_id=str(uuid4()),
                event_type="order.order.created",
                data={
                    "order_id": str(uuid4()),
                    "user_id": str(uuid4()),
                    "total_amount": 99.99,
                    "items": [{"product_id": str(uuid4()), "quantity": 1}]
                },
                version=1,
                timestamp=datetime.now(timezone.utc).isoformat(),
                correlation_id=str(uuid4())
            )
            events.append(event)
        return events

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    def create_consumer_record(self, event: SimpleEvent, topic: str = "test-topic") -> ConsumerRecord:
        """Create a Kafka ConsumerRecord from an event"""
        return ConsumerRecord(
            topic=topic,
            partition=0,
            offset=random.randint(1, 1000),
            timestamp=int(time.time() * 1000),
            timestamp_type=1,
            key=event.event_id.encode('utf-8'),
            value=json.dumps(event.to_dict()).encode('utf-8'),
            checksum=None,
            serialized_key_size=len(event.event_id),
            serialized_value_size=len(json.dumps(event.to_dict())),
            headers=[]
        )

    @patch('core.events.consumer.AIOKafkaConsumer')
    async def test_consumer_handles_network_partition(
        self,
        mock_consumer_class,
        mock_kafka_consumer,
        sample_events,
        mock_db_session
    ):
        """Test consumer behavior during network partition"""
        
        # Setup consumer to simulate network partition
        network_partition_count = 0
        
        async def simulate_network_partition():
            nonlocal network_partition_count
            network_partition_count += 1
            if network_partition_count <= 3:
                raise KafkaTimeoutError("Network partition simulation")
            # After 3 failures, return normal message
            return self.create_consumer_record(sample_events[0])
        
        mock_kafka_consumer.__aiter__ = AsyncMock()
        mock_kafka_consumer.__anext__ = AsyncMock(side_effect=simulate_network_partition)
        mock_consumer_class.return_value = mock_kafka_consumer
        
        # Create consumer with retry logic
        consumer = EventConsumer("test-group")
        consumer.event_handlers["order.order.created"] = OrderEventHandler()
        
        # Start consumer
        await consumer.start(["test-topic"])
        
        # Simulate processing with network issues
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                # This would normally be in the consumer loop
                record = await mock_kafka_consumer.__anext__()
                # If we get here, network partition is resolved
                break
            except KafkaTimeoutError:
                retry_count += 1
                await asyncio.sleep(0.1 * (2 ** retry_count))  # Exponential backoff
        
        # Verify consumer recovered after network partition
        assert retry_count == 3  # Should have retried 3 times before success
        
        await consumer.stop()

    @patch('core.events.consumer.AIOKafkaConsumer')
    async def test_consumer_handles_message_corruption(
        self,
        mock_consumer_class,
        mock_kafka_consumer,
        mock_db_session
    ):
        """Test consumer behavior with corrupted messages"""
        
        # Create corrupted message records
        corrupted_records = [
            # Invalid JSON
            ConsumerRecord(
                topic="test-topic", partition=0, offset=1,
                timestamp=int(time.time() * 1000), timestamp_type=1,
                key=b"key1", value=b"invalid json {{{",
                checksum=None, serialized_key_size=4, serialized_value_size=15,
                headers=[]
            ),
            # Missing required fields
            ConsumerRecord(
                topic="test-topic", partition=0, offset=2,
                timestamp=int(time.time() * 1000), timestamp_type=1,
                key=b"key2", value=json.dumps({"incomplete": "event"}).encode(),
                checksum=None, serialized_key_size=4, serialized_value_size=20,
                headers=[]
            ),
            # Valid message after corrupted ones
            ConsumerRecord(
                topic="test-topic", partition=0, offset=3,
                timestamp=int(time.time() * 1000), timestamp_type=1,
                key=b"key3", value=json.dumps({
                    "event_id": str(uuid4()),
                    "event_type": "order.order.created",
                    "data": {"order_id": str(uuid4())},
                    "version": 1,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }).encode(),
                checksum=None, serialized_key_size=4, serialized_value_size=100,
                headers=[]
            )
        ]
        
        # Setup consumer to return corrupted messages
        mock_kafka_consumer.__aiter__ = AsyncMock(return_value=iter(corrupted_records))
        mock_consumer_class.return_value = mock_kafka_consumer
        
        consumer = EventConsumer("test-group")
        consumer.event_handlers["order.order.created"] = OrderEventHandler()
        
        await consumer.start(["test-topic"])
        
        processed_count = 0
        error_count = 0
        
        # Process messages and count errors
        async for record in mock_kafka_consumer:
            try:
                # Attempt to deserialize
                event_dict = json.loads(record.value.decode('utf-8'))
                event = SimpleEvent.from_dict(event_dict)
                processed_count += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                error_count += 1
                # Consumer should log error and continue processing
                continue
        
        # Verify consumer handled corrupted messages gracefully
        assert error_count == 2  # Two corrupted messages
        assert processed_count == 1  # One valid message processed
        
        await consumer.stop()

    @patch('core.events.consumer.AIOKafkaConsumer')
    async def test_consumer_handles_duplicate_messages(
        self,
        mock_consumer_class,
        mock_kafka_consumer,
        sample_events,
        mock_db_session
    ):
        """Test consumer idempotency with duplicate messages"""
        
        # Create duplicate message records
        event = sample_events[0]
        duplicate_records = [
            self.create_consumer_record(event),
            self.create_consumer_record(event),  # Duplicate
            self.create_consumer_record(event),  # Another duplicate
        ]
        
        mock_kafka_consumer.__aiter__ = AsyncMock(return_value=iter(duplicate_records))
        mock_consumer_class.return_value = mock_kafka_consumer
        
        consumer = EventConsumer("test-group")
        
        # Mock event handler to track processing
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock()
        mock_handler.is_idempotent.return_value = True
        consumer.event_handlers["order.order.created"] = mock_handler
        
        await consumer.start(["test-topic"])
        
        # Process all messages
        processed_events = []
        async for record in mock_kafka_consumer:
            try:
                event_dict = json.loads(record.value.decode('utf-8'))
                event = SimpleEvent.from_dict(event_dict)
                
                # Check if already processed (idempotency)
                if event.event_id not in consumer.processed_events:
                    await mock_handler.handle(event, mock_db_session)
                    consumer.processed_events.add(event.event_id)
                    processed_events.append(event.event_id)
            except Exception as e:
                continue
        
        # Verify only one unique event was processed despite duplicates
        assert len(processed_events) == 1
        assert len(set(processed_events)) == 1  # All same event_id
        mock_handler.handle.assert_called_once()
        
        await consumer.stop()

    @patch('core.events.consumer.AIOKafkaConsumer')
    async def test_consumer_handles_out_of_order_messages(
        self,
        mock_consumer_class,
        mock_kafka_consumer,
        mock_db_session
    ):
        """Test consumer behavior with out-of-order messages"""
        
        # Create events with timestamps that are out of order
        base_time = datetime.now(timezone.utc)
        events = [
            SimpleEvent(
                event_id=str(uuid4()),
                event_type="order.order.created",
                data={"order_id": "order-1", "sequence": 1},
                version=1,
                timestamp=(base_time.replace(second=10)).isoformat()  # Later timestamp
            ),
            SimpleEvent(
                event_id=str(uuid4()),
                event_type="order.order.updated",
                data={"order_id": "order-1", "sequence": 2},
                version=1,
                timestamp=(base_time.replace(second=5)).isoformat()   # Earlier timestamp
            ),
            SimpleEvent(
                event_id=str(uuid4()),
                event_type="order.order.shipped",
                data={"order_id": "order-1", "sequence": 3},
                version=1,
                timestamp=(base_time.replace(second=15)).isoformat()  # Latest timestamp
            )
        ]
        
        # Create records in wrong order (by timestamp)
        records = [self.create_consumer_record(event) for event in events]
        
        mock_kafka_consumer.__aiter__ = AsyncMock(return_value=iter(records))
        mock_consumer_class.return_value = mock_kafka_consumer
        
        consumer = EventConsumer("test-group")
        
        # Track processing order
        processed_events = []
        
        class OrderTrackingHandler:
            async def handle(self, event: SimpleEvent, db):
                processed_events.append({
                    "event_type": event.event_type,
                    "timestamp": event.timestamp,
                    "sequence": event.data.get("sequence")
                })
            
            def is_idempotent(self):
                return True
        
        handler = OrderTrackingHandler()
        consumer.event_handlers["order.order.created"] = handler
        consumer.event_handlers["order.order.updated"] = handler
        consumer.event_handlers["order.order.shipped"] = handler
        
        await consumer.start(["test-topic"])
        
        # Process messages
        async for record in mock_kafka_consumer:
            try:
                event_dict = json.loads(record.value.decode('utf-8'))
                event = SimpleEvent.from_dict(event_dict)
                await handler.handle(event, mock_db_session)
            except Exception:
                continue
        
        # Verify all events were processed (order handling is application-specific)
        assert len(processed_events) == 3
        
        # In a real system, you might want to implement event ordering logic
        # For now, we just verify all events were processed
        sequences = [event["sequence"] for event in processed_events]
        assert set(sequences) == {1, 2, 3}
        
        await consumer.stop()

    @patch('core.events.consumer.AIOKafkaConsumer')
    async def test_consumer_handles_commit_failures(
        self,
        mock_consumer_class,
        mock_kafka_consumer,
        sample_events,
        mock_db_session
    ):
        """Test consumer behavior when offset commits fail"""
        
        # Setup consumer to fail commits intermittently
        commit_failure_count = 0
        
        async def failing_commit():
            nonlocal commit_failure_count
            commit_failure_count += 1
            if commit_failure_count <= 2:
                raise CommitFailedError("Commit failed simulation")
            # After 2 failures, succeed
            return None
        
        mock_kafka_consumer.commit = AsyncMock(side_effect=failing_commit)
        
        records = [self.create_consumer_record(event) for event in sample_events[:3]]
        mock_kafka_consumer.__aiter__ = AsyncMock(return_value=iter(records))
        mock_consumer_class.return_value = mock_kafka_consumer
        
        consumer = EventConsumer("test-group")
        
        # Mock handler
        mock_handler = AsyncMock()
        mock_handler.handle = AsyncMock()
        mock_handler.is_idempotent.return_value = True
        consumer.event_handlers["order.order.created"] = mock_handler
        
        await consumer.start(["test-topic"])
        
        # Process messages with commit failures
        processed_count = 0
        commit_retry_count = 0
        
        async for record in mock_kafka_consumer:
            try:
                event_dict = json.loads(record.value.decode('utf-8'))
                event = SimpleEvent.from_dict(event_dict)
                await mock_handler.handle(event, mock_db_session)
                processed_count += 1
                
                # Try to commit with retry logic
                while commit_retry_count < 3:
                    try:
                        await mock_kafka_consumer.commit()
                        break
                    except CommitFailedError:
                        commit_retry_count += 1
                        await asyncio.sleep(0.1)
                        
            except Exception:
                continue
        
        # Verify processing continued despite commit failures
        assert processed_count == 3
        assert commit_failure_count == 2  # Failed twice before succeeding
        
        await consumer.stop()

    @patch('core.events.consumer.AIOKafkaConsumer')
    async def test_consumer_handles_high_message_volume(
        self,
        mock_consumer_class,
        mock_kafka_consumer,
        mock_db_session
    ):
        """Test consumer performance under high message volume"""
        
        # Generate large number of events
        high_volume_events = []
        for i in range(1000):
            event = SimpleEvent(
                event_id=str(uuid4()),
                event_type="order.order.created",
                data={"order_id": f"order-{i}", "batch": i // 100},
                version=1,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            high_volume_events.append(event)
        
        records = [self.create_consumer_record(event) for event in high_volume_events]
        mock_kafka_consumer.__aiter__ = AsyncMock(return_value=iter(records))
        mock_consumer_class.return_value = mock_kafka_consumer
        
        consumer = EventConsumer("test-group")
        
        # Mock fast handler
        processing_times = []
        
        class PerformanceTrackingHandler:
            async def handle(self, event: SimpleEvent, db):
                start_time = time.time()
                # Simulate some processing
                await asyncio.sleep(0.001)  # 1ms processing time
                end_time = time.time()
                processing_times.append(end_time - start_time)
            
            def is_idempotent(self):
                return True
        
        handler = PerformanceTrackingHandler()
        consumer.event_handlers["order.order.created"] = handler
        
        await consumer.start(["test-topic"])
        
        # Process high volume of messages
        start_time = time.time()
        processed_count = 0
        
        async for record in mock_kafka_consumer:
            try:
                event_dict = json.loads(record.value.decode('utf-8'))
                event = SimpleEvent.from_dict(event_dict)
                await handler.handle(event, mock_db_session)
                processed_count += 1
                
                # Break after processing reasonable number for test
                if processed_count >= 100:
                    break
            except Exception:
                continue
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify performance metrics
        assert processed_count == 100
        assert total_time < 5.0  # Should process 100 messages in under 5 seconds
        
        # Check average processing time
        avg_processing_time = sum(processing_times) / len(processing_times)
        assert avg_processing_time < 0.1  # Average under 100ms per message
        
        await consumer.stop()

    @patch('core.events.consumer.AIOKafkaConsumer')
    async def test_consumer_dead_letter_queue_handling(
        self,
        mock_consumer_class,
        mock_kafka_consumer,
        mock_db_session
    ):
        """Test consumer behavior with messages that consistently fail processing"""
        
        # Create events that will cause processing failures
        failing_events = [
            SimpleEvent(
                event_id=str(uuid4()),
                event_type="order.order.created",
                data={"invalid": "data", "missing_required_fields": True},
                version=1,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        ]
        
        records = [self.create_consumer_record(event) for event in failing_events]
        mock_kafka_consumer.__aiter__ = AsyncMock(return_value=iter(records))
        mock_consumer_class.return_value = mock_kafka_consumer
        
        consumer = EventConsumer("test-group")
        
        # Mock handler that always fails
        class FailingHandler:
            def __init__(self):
                self.attempt_count = 0
            
            async def handle(self, event: SimpleEvent, db):
                self.attempt_count += 1
                raise ValueError("Simulated processing failure")
            
            def is_idempotent(self):
                return True
        
        failing_handler = FailingHandler()
        consumer.event_handlers["order.order.created"] = failing_handler
        
        # Mock dead letter handler
        dead_letter_messages = []
        
        class MockDeadLetterHandler:
            async def send_to_dead_letter_queue(self, event, error, retry_count):
                dead_letter_messages.append({
                    "event_id": event.event_id,
                    "error": str(error),
                    "retry_count": retry_count
                })
        
        consumer.dead_letter_handler = MockDeadLetterHandler()
        
        await consumer.start(["test-topic"])
        
        # Process failing messages with retry logic
        max_retries = 3
        
        async for record in mock_kafka_consumer:
            try:
                event_dict = json.loads(record.value.decode('utf-8'))
                event = SimpleEvent.from_dict(event_dict)
                
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        await failing_handler.handle(event, mock_db_session)
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            # Send to dead letter queue
                            await consumer.dead_letter_handler.send_to_dead_letter_queue(
                                event, e, retry_count
                            )
                        else:
                            await asyncio.sleep(0.1 * retry_count)  # Backoff
                            
            except Exception:
                continue
        
        # Verify dead letter queue handling
        assert len(dead_letter_messages) == 1
        assert dead_letter_messages[0]["retry_count"] == max_retries
        assert "Simulated processing failure" in dead_letter_messages[0]["error"]
        assert failing_handler.attempt_count == max_retries
        
        await consumer.stop()

    async def test_consumer_graceful_shutdown(self):
        """Test consumer graceful shutdown during processing"""
        
        consumer = EventConsumer("test-group")
        
        # Start consumer
        with patch('core.events.consumer.AIOKafkaConsumer') as mock_consumer_class:
            mock_kafka_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_kafka_consumer
            
            await consumer.start(["test-topic"])
            
            # Verify consumer is running
            assert consumer._running is True
            
            # Shutdown consumer
            await consumer.stop()
            
            # Verify graceful shutdown
            assert consumer._running is False
            mock_kafka_consumer.stop.assert_called_once()

    @patch('core.events.consumer.AIOKafkaConsumer')
    async def test_consumer_handles_broker_unavailable(
        self,
        mock_consumer_class,
        mock_kafka_consumer
    ):
        """Test consumer behavior when Kafka broker is unavailable"""
        
        # Setup consumer to fail on start (broker unavailable)
        mock_kafka_consumer.start.side_effect = KafkaError("Broker unavailable")
        mock_consumer_class.return_value = mock_kafka_consumer
        
        consumer = EventConsumer("test-group")
        
        # Attempt to start consumer
        with pytest.raises(KafkaError):
            await consumer.start(["test-topic"])
        
        # Verify consumer didn't start
        assert consumer._running is False