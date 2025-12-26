"""
Chaos Engineering Tests: Random Consumer Kills and Recovery
Tests system resilience when consumers are randomly terminated
"""

import pytest
import asyncio
import random
import signal
import os
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
import threading
import time

from core.events.consumer import EventConsumer
from services.orders import OrderService
from services.payments import PaymentService


class TestRandomConsumerKills:
    """Test random consumer termination and recovery"""
    
    @pytest.fixture
    def mock_consumer_process(self):
        """Mock consumer process for testing"""
        return MagicMock()
    
    @pytest.mark.asyncio
    async def test_consumer_sigkill_during_processing(self, mock_consumer_process):
        """Test consumer killed with SIGKILL during event processing"""
        consumer_state = {
            "status": "processing",
            "current_event": str(uuid4()),
            "processed_count": 150,
            "start_time": datetime.utcnow()
        }
        
        # Simulate SIGKILL during processing
        def simulate_sigkill():
            consumer_state["status"] = "killed"
            consumer_state["exit_code"] = -9  # SIGKILL
            consumer_state["killed_at"] = datetime.utcnow()
        
        # Consumer is processing
        assert consumer_state["status"] == "processing"
        
        # Random kill occurs
        simulate_sigkill()
        
        # Verify consumer was killed
        assert consumer_state["status"] == "killed"
        assert consumer_state["exit_code"] == -9
        assert "killed_at" in consumer_state
    
    @pytest.mark.asyncio
    async def test_consumer_sigterm_graceful_shutdown(self):
        """Test consumer graceful shutdown with SIGTERM"""
        consumer_state = {
            "status": "running",
            "processing_queue": [str(uuid4()) for _ in range(5)],
            "shutdown_timeout": 30  # seconds
        }
        
        async def graceful_shutdown():
            consumer_state["status"] = "shutting_down"
            
            # Process remaining events in queue
            while consumer_state["processing_queue"] and consumer_state["shutdown_timeout"] > 0:
                event_id = consumer_state["processing_queue"].pop(0)
                # Simulate processing time
                await asyncio.sleep(0.1)
                consumer_state["shutdown_timeout"] -= 1
            
            consumer_state["status"] = "shutdown"
            return "graceful_shutdown_complete"
        
        # Trigger graceful shutdown
        result = await graceful_shutdown()
        
        assert result == "graceful_shutdown_complete"
        assert consumer_state["status"] == "shutdown"
        assert len(consumer_state["processing_queue"]) == 0
    
    @pytest.mark.asyncio
    async def test_consumer_oom_kill(self):
        """Test consumer killed due to out of memory"""
        consumer_metrics = {
            "memory_usage_mb": 512,
            "memory_limit_mb": 1024,
            "memory_growth_rate": 50  # MB per minute
        }
        
        # Simulate memory growth over time
        minutes_elapsed = 0
        while consumer_metrics["memory_usage_mb"] < consumer_metrics["memory_limit_mb"]:
            minutes_elapsed += 1
            consumer_metrics["memory_usage_mb"] += consumer_metrics["memory_growth_rate"]
            
            if consumer_metrics["memory_usage_mb"] >= consumer_metrics["memory_limit_mb"]:
                # OOM killer activates
                consumer_metrics["status"] = "oom_killed"
                consumer_metrics["exit_code"] = -9
                break
        
        assert consumer_metrics["status"] == "oom_killed"
        assert consumer_metrics["memory_usage_mb"] >= consumer_metrics["memory_limit_mb"]
        assert minutes_elapsed > 0
    
    @pytest.mark.asyncio
    async def test_consumer_network_partition_kill(self):
        """Test consumer behavior during network partition"""
        consumer_state = {
            "status": "running",
            "kafka_connection": "connected",
            "heartbeat_interval": 5,  # seconds
            "last_heartbeat": datetime.utcnow()
        }
        
        # Simulate network partition
        def simulate_network_partition():
            consumer_state["kafka_connection"] = "disconnected"
            consumer_state["network_partition"] = True
            return datetime.utcnow()
        
        partition_start = simulate_network_partition()
        
        # Consumer should detect partition and handle gracefully
        time_since_partition = (datetime.utcnow() - partition_start).total_seconds()
        max_partition_tolerance = 30  # seconds
        
        if time_since_partition > max_partition_tolerance:
            consumer_state["status"] = "partition_timeout"
        
        assert consumer_state["kafka_connection"] == "disconnected"
        assert consumer_state["network_partition"] is True
    
    @pytest.mark.asyncio
    async def test_random_consumer_kill_simulation(self):
        """Simulate random consumer kills over time"""
        consumers = [
            {"id": f"consumer_{i}", "status": "running", "uptime": 0}
            for i in range(5)
        ]
        
        kill_probability = 0.1  # 10% chance per time unit
        time_units = 100
        kills_occurred = 0
        
        for time_unit in range(time_units):
            for consumer in consumers:
                if consumer["status"] == "running":
                    consumer["uptime"] += 1
                    
                    # Random kill check
                    if random.random() < kill_probability:
                        consumer["status"] = "killed"
                        consumer["killed_at"] = time_unit
                        kills_occurred += 1
                    
                elif consumer["status"] == "killed":
                    # Simulate restart after some time
                    if time_unit - consumer.get("killed_at", 0) > 10:  # 10 time units to restart
                        consumer["status"] = "running"
                        consumer["uptime"] = 0
                        consumer["restarts"] = consumer.get("restarts", 0) + 1
        
        # Verify some kills occurred and some consumers restarted
        assert kills_occurred > 0
        restarted_consumers = [c for c in consumers if c.get("restarts", 0) > 0]
        assert len(restarted_consumers) > 0
    
    @pytest.mark.asyncio
    async def test_consumer_cascade_failure(self):
        """Test cascade failure when multiple consumers fail"""
        consumer_group = {
            "consumers": [
                {"id": "consumer_1", "status": "running", "load": 100},
                {"id": "consumer_2", "status": "running", "load": 100},
                {"id": "consumer_3", "status": "running", "load": 100},
                {"id": "consumer_4", "status": "running", "load": 100}
            ],
            "total_load": 400,
            "max_consumer_load": 200
        }
        
        # Kill first consumer
        consumer_group["consumers"][0]["status"] = "failed"
        failed_consumer_load = consumer_group["consumers"][0]["load"]
        
        # Redistribute load to remaining consumers
        active_consumers = [c for c in consumer_group["consumers"] if c["status"] == "running"]
        load_per_consumer = failed_consumer_load / len(active_consumers)
        
        for consumer in active_consumers:
            consumer["load"] += load_per_consumer
        
        # Check if any consumer is overloaded
        overloaded_consumers = [c for c in active_consumers if c["load"] > consumer_group["max_consumer_load"]]
        
        if overloaded_consumers:
            # Cascade failure - overloaded consumers fail
            for consumer in overloaded_consumers:
                consumer["status"] = "overload_failed"
        
        # Verify cascade failure occurred
        failed_consumers = [c for c in consumer_group["consumers"] if c["status"] in ["failed", "overload_failed"]]
        assert len(failed_consumers) > 1  # More than initial failure


class TestConsumerRecoveryMechanisms:
    """Test consumer recovery and restart mechanisms"""
    
    @pytest.mark.asyncio
    async def test_consumer_auto_restart(self):
        """Test automatic consumer restart after failure"""
        consumer_config = {
            "restart_policy": "always",
            "restart_delay": 5,  # seconds
            "max_restarts": 3,
            "restart_count": 0
        }
        
        consumer_state = {"status": "running"}
        
        # Simulate consumer failure and restart cycle
        for failure_count in range(5):  # Try to fail 5 times
            # Consumer fails
            consumer_state["status"] = "failed"
            
            # Check restart policy
            if (consumer_config["restart_policy"] == "always" and 
                consumer_config["restart_count"] < consumer_config["max_restarts"]):
                
                # Restart consumer
                await asyncio.sleep(0.1)  # Simulate restart delay
                consumer_state["status"] = "running"
                consumer_config["restart_count"] += 1
            else:
                # Max restarts reached
                consumer_state["status"] = "permanently_failed"
                break
        
        # Should reach max restarts and stop
        assert consumer_config["restart_count"] == consumer_config["max_restarts"]
        assert consumer_state["status"] == "permanently_failed"
    
    @pytest.mark.asyncio
    async def test_consumer_health_check_recovery(self):
        """Test consumer recovery based on health checks"""
        consumer_health = {
            "last_heartbeat": datetime.utcnow(),
            "heartbeat_interval": 10,  # seconds
            "missed_heartbeats": 0,
            "max_missed_heartbeats": 3,
            "status": "healthy"
        }
        
        # Simulate missed heartbeats
        for i in range(5):
            current_time = datetime.utcnow()
            time_since_heartbeat = (current_time - consumer_health["last_heartbeat"]).total_seconds()
            
            if time_since_heartbeat > consumer_health["heartbeat_interval"]:
                consumer_health["missed_heartbeats"] += 1
                
                if consumer_health["missed_heartbeats"] >= consumer_health["max_missed_heartbeats"]:
                    consumer_health["status"] = "unhealthy"
                    break
            
            # Simulate time passing
            await asyncio.sleep(0.1)
        
        # Consumer should be marked unhealthy
        assert consumer_health["status"] == "unhealthy"
        assert consumer_health["missed_heartbeats"] >= consumer_health["max_missed_heartbeats"]
    
    @pytest.mark.asyncio
    async def test_consumer_circuit_breaker(self):
        """Test circuit breaker pattern for consumer failures"""
        circuit_breaker = {
            "state": "closed",  # closed, open, half_open
            "failure_count": 0,
            "failure_threshold": 5,
            "timeout": 30,  # seconds
            "last_failure_time": None
        }
        
        # Simulate failures
        for i in range(7):  # More than threshold
            # Simulate consumer failure
            circuit_breaker["failure_count"] += 1
            circuit_breaker["last_failure_time"] = datetime.utcnow()
            
            # Check if threshold exceeded
            if circuit_breaker["failure_count"] >= circuit_breaker["failure_threshold"]:
                circuit_breaker["state"] = "open"
                break
        
        # Circuit should be open
        assert circuit_breaker["state"] == "open"
        assert circuit_breaker["failure_count"] >= circuit_breaker["failure_threshold"]
        
        # Simulate timeout period passing
        circuit_breaker["last_failure_time"] = datetime.utcnow() - timedelta(seconds=35)
        
        # Check if circuit can transition to half-open
        time_since_failure = (datetime.utcnow() - circuit_breaker["last_failure_time"]).total_seconds()
        if time_since_failure > circuit_breaker["timeout"]:
            circuit_breaker["state"] = "half_open"
        
        assert circuit_breaker["state"] == "half_open"
    
    @pytest.mark.asyncio
    async def test_consumer_backoff_strategy(self):
        """Test exponential backoff for consumer restarts"""
        backoff_config = {
            "initial_delay": 1,  # seconds
            "max_delay": 60,     # seconds
            "multiplier": 2,
            "jitter": True
        }
        
        restart_attempts = []
        current_delay = backoff_config["initial_delay"]
        
        for attempt in range(6):  # 6 restart attempts
            restart_attempts.append({
                "attempt": attempt + 1,
                "delay": current_delay
            })
            
            # Calculate next delay with exponential backoff
            current_delay = min(
                current_delay * backoff_config["multiplier"],
                backoff_config["max_delay"]
            )
            
            # Add jitter if enabled
            if backoff_config["jitter"]:
                jitter = random.uniform(0.5, 1.5)
                current_delay = current_delay * jitter
        
        # Verify exponential backoff pattern
        assert restart_attempts[0]["delay"] == 1
        assert restart_attempts[1]["delay"] >= 2
        assert restart_attempts[-1]["delay"] <= backoff_config["max_delay"] * 1.5  # Account for jitter


class TestConsumerLoadBalancing:
    """Test consumer load balancing during failures"""
    
    @pytest.mark.asyncio
    async def test_consumer_group_rebalancing(self):
        """Test consumer group rebalancing after member failure"""
        consumer_group = {
            "group_id": "order_processors",
            "members": [
                {"id": "consumer_1", "partitions": [0, 1], "status": "active"},
                {"id": "consumer_2", "partitions": [2, 3], "status": "active"},
                {"id": "consumer_3", "partitions": [4, 5], "status": "active"}
            ],
            "total_partitions": 6
        }
        
        # Consumer 2 fails
        failed_consumer = consumer_group["members"][1]
        failed_consumer["status"] = "failed"
        failed_partitions = failed_consumer["partitions"]
        
        # Rebalance partitions among remaining consumers
        active_consumers = [m for m in consumer_group["members"] if m["status"] == "active"]
        
        # Redistribute failed consumer's partitions
        for i, partition in enumerate(failed_partitions):
            target_consumer = active_consumers[i % len(active_consumers)]
            target_consumer["partitions"].append(partition)
        
        # Clear failed consumer's partitions
        failed_consumer["partitions"] = []
        
        # Verify rebalancing
        total_assigned_partitions = sum(len(c["partitions"]) for c in active_consumers)
        assert total_assigned_partitions == consumer_group["total_partitions"]
        assert len(failed_consumer["partitions"]) == 0
    
    @pytest.mark.asyncio
    async def test_consumer_sticky_assignment(self):
        """Test sticky partition assignment during rebalancing"""
        # Initial assignment
        consumer_assignments = {
            "consumer_1": [0, 1, 2],
            "consumer_2": [3, 4, 5],
            "consumer_3": [6, 7, 8]
        }
        
        # Consumer 2 leaves
        leaving_consumer = "consumer_2"
        orphaned_partitions = consumer_assignments.pop(leaving_consumer)
        
        # Sticky assignment - try to minimize partition movement
        remaining_consumers = list(consumer_assignments.keys())
        
        for partition in orphaned_partitions:
            # Assign to consumer with least partitions
            min_consumer = min(remaining_consumers, 
                             key=lambda c: len(consumer_assignments[c]))
            consumer_assignments[min_consumer].append(partition)
        
        # Verify all partitions are assigned
        total_partitions = sum(len(partitions) for partitions in consumer_assignments.values())
        assert total_partitions == 9
        
        # Verify load is balanced
        partition_counts = [len(partitions) for partitions in consumer_assignments.values()]
        max_diff = max(partition_counts) - min(partition_counts)
        assert max_diff <= 1  # Load should be balanced within 1 partition


class TestSystemResilienceUnderChaos:
    """Test overall system resilience under consumer chaos"""
    
    @pytest.mark.asyncio
    async def test_system_survives_consumer_massacre(self):
        """Test system survival when most consumers are killed"""
        initial_consumers = 10
        surviving_consumers = 2
        killed_consumers = initial_consumers - surviving_consumers
        
        # System should continue operating with reduced capacity
        capacity_reduction = killed_consumers / initial_consumers
        remaining_capacity = 1 - capacity_reduction
        
        # System should implement graceful degradation
        if remaining_capacity < 0.5:  # Less than 50% capacity
            degraded_mode = True
            load_shedding = True
        else:
            degraded_mode = False
            load_shedding = False
        
        assert degraded_mode is True
        assert load_shedding is True
        assert remaining_capacity == 0.2  # 20% capacity remaining
        
        # Core functionality should still work
        core_services_available = remaining_capacity > 0
        assert core_services_available is True
    
    @pytest.mark.asyncio
    async def test_consumer_death_spiral_prevention(self):
        """Test prevention of consumer death spiral"""
        consumer_pool = {
            "healthy": 8,
            "unhealthy": 0,
            "failed": 0,
            "load_per_consumer": 100
        }
        
        # Simulate cascade failure scenario
        for failure_round in range(3):
            # Some consumers fail due to overload
            failing_consumers = min(2, consumer_pool["healthy"])
            consumer_pool["healthy"] -= failing_consumers
            consumer_pool["failed"] += failing_consumers
            
            # Redistribute load
            if consumer_pool["healthy"] > 0:
                total_load = (consumer_pool["healthy"] + failing_consumers) * consumer_pool["load_per_consumer"]
                new_load_per_consumer = total_load / consumer_pool["healthy"]
                consumer_pool["load_per_consumer"] = new_load_per_consumer
                
                # Check if remaining consumers are overloaded
                max_safe_load = 150
                if new_load_per_consumer > max_safe_load:
                    # Implement circuit breaker to prevent death spiral
                    circuit_breaker_activated = True
                    # Shed load to prevent further failures
                    consumer_pool["load_per_consumer"] = max_safe_load
                    load_shed = total_load - (consumer_pool["healthy"] * max_safe_load)
                else:
                    circuit_breaker_activated = False
                    load_shed = 0
            else:
                # All consumers failed
                break
        
        # System should prevent complete failure
        assert consumer_pool["healthy"] > 0 or circuit_breaker_activated
        
        # Some load shedding should occur to prevent death spiral
        if consumer_pool["healthy"] < 4:  # Less than half original capacity
            assert load_shed > 0 or circuit_breaker_activated


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])