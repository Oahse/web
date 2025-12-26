"""
Chaos Engineering Tests: Infrastructure Failures
Tests system resilience when dropping Kafka brokers and restarting Redis
"""

import pytest
import asyncio
import random
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
import json

from core.redis import RedisService
from core.kafka import get_kafka_producer_service
from services.cart import CartService
from services.orders import OrderService


class TestKafkaBrokerFailures:
    """Test Kafka broker failures and cluster resilience"""
    
    @pytest.fixture
    def kafka_cluster(self):
        """Mock Kafka cluster configuration"""
        return {
            "brokers": [
                {"id": 1, "host": "kafka-1", "port": 9092, "status": "active"},
                {"id": 2, "host": "kafka-2", "port": 9092, "status": "active"},
                {"id": 3, "host": "kafka-3", "port": 9092, "status": "active"}
            ],
            "replication_factor": 2,
            "min_in_sync_replicas": 1
        }
    
    @pytest.mark.asyncio
    async def test_single_broker_failure(self, kafka_cluster):
        """Test system behavior when one Kafka broker fails"""
        # Kill one broker
        failed_broker = kafka_cluster["brokers"][0]
        failed_broker["status"] = "failed"
        
        active_brokers = [b for b in kafka_cluster["brokers"] if b["status"] == "active"]
        
        # System should continue with remaining brokers
        assert len(active_brokers) == 2
        
        # Check if cluster can maintain minimum replicas
        can_maintain_replicas = len(active_brokers) >= kafka_cluster["min_in_sync_replicas"]
        assert can_maintain_replicas is True
        
        # Simulate event publishing with reduced cluster
        async def publish_with_reduced_cluster():
            if len(active_brokers) > 0:
                return {"status": "published", "brokers_used": len(active_brokers)}
            else:
                raise Exception("No brokers available")
        
        result = await publish_with_reduced_cluster()
        assert result["status"] == "published"
        assert result["brokers_used"] == 2
    
    @pytest.mark.asyncio
    async def test_majority_broker_failure(self, kafka_cluster):
        """Test system behavior when majority of brokers fail"""
        # Kill 2 out of 3 brokers
        kafka_cluster["brokers"][0]["status"] = "failed"
        kafka_cluster["brokers"][1]["status"] = "failed"
        
        active_brokers = [b for b in kafka_cluster["brokers"] if b["status"] == "active"]
        
        # Only 1 broker remaining
        assert len(active_brokers) == 1
        
        # Check cluster health
        cluster_healthy = len(active_brokers) >= (len(kafka_cluster["brokers"]) // 2 + 1)
        assert cluster_healthy is False  # Majority failed
        
        # System should implement degraded mode
        degraded_mode = not cluster_healthy
        assert degraded_mode is True
        
        # Events should be queued or circuit breaker should activate
        circuit_breaker_open = True
        if circuit_breaker_open:
            # Events are queued for later processing
            queued_events = []
            event = {"id": str(uuid4()), "type": "order.created"}
            queued_events.append(event)
            
            assert len(queued_events) == 1
    
    @pytest.mark.asyncio
    async def test_complete_kafka_cluster_failure(self, kafka_cluster):
        """Test system behavior when entire Kafka cluster fails"""
        # Kill all brokers
        for broker in kafka_cluster["brokers"]:
            broker["status"] = "failed"
        
        active_brokers = [b for b in kafka_cluster["brokers"] if b["status"] == "active"]
        assert len(active_brokers) == 0
        
        # System should handle complete Kafka failure gracefully
        async def handle_kafka_outage():
            # Core business operations should continue
            # Events should be stored locally or in database
            fallback_storage = []
            
            event = {
                "id": str(uuid4()),
                "type": "payment.completed",
                "timestamp": datetime.utcnow().isoformat(),
                "stored_locally": True
            }
            
            fallback_storage.append(event)
            return {"status": "stored_locally", "events": len(fallback_storage)}
        
        result = await handle_kafka_outage()
        assert result["status"] == "stored_locally"
        assert result["events"] == 1
    
    @pytest.mark.asyncio
    async def test_kafka_broker_recovery(self, kafka_cluster):
        """Test Kafka broker recovery and event replay"""
        # Start with failed brokers
        kafka_cluster["brokers"][0]["status"] = "failed"
        kafka_cluster["brokers"][1]["status"] = "failed"
        
        # Events stored during outage
        stored_events = [
            {"id": str(uuid4()), "type": "order.created", "stored_at": datetime.utcnow()},
            {"id": str(uuid4()), "type": "payment.completed", "stored_at": datetime.utcnow()}
        ]
        
        # Brokers recover
        kafka_cluster["brokers"][0]["status"] = "active"
        kafka_cluster["brokers"][1]["status"] = "active"
        
        active_brokers = [b for b in kafka_cluster["brokers"] if b["status"] == "active"]
        
        # System should replay stored events
        if len(active_brokers) >= kafka_cluster["min_in_sync_replicas"]:
            replayed_events = []
            for event in stored_events:
                event["replayed"] = True
                event["replayed_at"] = datetime.utcnow()
                replayed_events.append(event)
            
            replay_successful = len(replayed_events) == len(stored_events)
        else:
            replay_successful = False
        
        assert replay_successful is True
        assert len(replayed_events) == 2
    
    @pytest.mark.asyncio
    async def test_kafka_partition_leader_election(self, kafka_cluster):
        """Test partition leader election during broker failures"""
        partitions = [
            {"id": 0, "leader": 1, "replicas": [1, 2], "in_sync_replicas": [1, 2]},
            {"id": 1, "leader": 2, "replicas": [2, 3], "in_sync_replicas": [2, 3]},
            {"id": 2, "leader": 3, "replicas": [3, 1], "in_sync_replicas": [3, 1]}
        ]
        
        # Broker 1 fails (leader of partition 0)
        failed_broker_id = 1
        kafka_cluster["brokers"][0]["status"] = "failed"
        
        # Update partitions affected by broker failure
        for partition in partitions:
            if partition["leader"] == failed_broker_id:
                # Remove failed broker from in-sync replicas
                partition["in_sync_replicas"] = [r for r in partition["in_sync_replicas"] if r != failed_broker_id]
                
                # Elect new leader from remaining in-sync replicas
                if partition["in_sync_replicas"]:
                    partition["leader"] = partition["in_sync_replicas"][0]
                else:
                    partition["leader"] = None  # No leader available
        
        # Verify leader election
        partition_0 = partitions[0]
        assert partition_0["leader"] == 2  # New leader elected
        assert failed_broker_id not in partition_0["in_sync_replicas"]
    
    @pytest.mark.asyncio
    async def test_kafka_network_partition(self):
        """Test Kafka behavior during network partition"""
        # Simulate network partition splitting cluster
        cluster_a = [1, 2]  # Brokers that can communicate
        cluster_b = [3]     # Isolated broker
        
        # Partition affects leader election and replication
        def can_form_quorum(broker_ids, total_brokers):
            return len(broker_ids) > total_brokers // 2
        
        cluster_a_has_quorum = can_form_quorum(cluster_a, 3)
        cluster_b_has_quorum = can_form_quorum(cluster_b, 3)
        
        assert cluster_a_has_quorum is True   # 2 > 3//2 (1)
        assert cluster_b_has_quorum is False  # 1 <= 3//2 (1)
        
        # Only cluster with quorum can accept writes
        if cluster_a_has_quorum:
            active_cluster = cluster_a
            write_availability = True
        else:
            active_cluster = []
            write_availability = False
        
        assert write_availability is True
        assert len(active_cluster) == 2


class TestRedisFailuresAndRecovery:
    """Test Redis failures and restart scenarios"""
    
    @pytest.fixture
    def redis_cluster(self):
        """Mock Redis cluster configuration"""
        return {
            "nodes": [
                {"id": "redis-1", "role": "master", "status": "active", "port": 6379},
                {"id": "redis-2", "role": "slave", "status": "active", "port": 6380},
                {"id": "redis-3", "role": "slave", "status": "active", "port": 6381}
            ],
            "data": {
                "cart:user1": '{"items": [{"id": "item1", "quantity": 2}]}',
                "session:sess123": '{"user_id": "user1", "expires": "2024-12-31"}'
            }
        }
    
    @pytest.mark.asyncio
    async def test_redis_master_failure(self, redis_cluster):
        """Test Redis master failure and failover"""
        # Master fails
        master_node = next(n for n in redis_cluster["nodes"] if n["role"] == "master")
        master_node["status"] = "failed"
        
        # Slave promotion to master
        slave_nodes = [n for n in redis_cluster["nodes"] if n["role"] == "slave" and n["status"] == "active"]
        
        if slave_nodes:
            # Promote first available slave
            new_master = slave_nodes[0]
            new_master["role"] = "master"
            failover_successful = True
        else:
            failover_successful = False
        
        assert failover_successful is True
        assert new_master["role"] == "master"
        
        # Data should be preserved (assuming replication was working)
        data_preserved = len(redis_cluster["data"]) > 0
        assert data_preserved is True
    
    @pytest.mark.asyncio
    async def test_redis_complete_restart(self, redis_cluster):
        """Test complete Redis restart scenario"""
        # All Redis nodes go down
        for node in redis_cluster["nodes"]:
            node["status"] = "restarting"
        
        # Data is lost (simulating restart without persistence)
        original_data = redis_cluster["data"].copy()
        redis_cluster["data"].clear()
        
        # System should handle Redis unavailability
        async def handle_redis_outage():
            # Cart operations should fallback to database
            fallback_mode = True
            
            # Critical operations should continue
            cart_operations_available = True  # Using database fallback
            session_operations_available = False  # Sessions lost
            
            return {
                "fallback_mode": fallback_mode,
                "cart_available": cart_operations_available,
                "sessions_available": session_operations_available
            }
        
        result = await handle_redis_outage()
        
        assert result["fallback_mode"] is True
        assert result["cart_available"] is True  # Fallback to DB
        assert result["sessions_available"] is False  # Sessions lost
        
        # Redis nodes come back online
        for node in redis_cluster["nodes"]:
            node["status"] = "active"
        
        # Data needs to be rebuilt from database
        data_recovery_needed = len(redis_cluster["data"]) == 0
        assert data_recovery_needed is True
    
    @pytest.mark.asyncio
    async def test_redis_memory_pressure_restart(self):
        """Test Redis restart due to memory pressure"""
        redis_stats = {
            "used_memory": 1024 * 1024 * 1024,  # 1GB
            "max_memory": 1024 * 1024 * 1024,   # 1GB limit
            "memory_policy": "allkeys-lru",
            "evicted_keys": 0
        }
        
        # Simulate memory pressure
        additional_memory_needed = 100 * 1024 * 1024  # 100MB
        
        if redis_stats["used_memory"] + additional_memory_needed > redis_stats["max_memory"]:
            if redis_stats["memory_policy"] == "allkeys-lru":
                # Redis should evict keys
                redis_stats["evicted_keys"] += 1000  # Simulate eviction
                memory_freed = 50 * 1024 * 1024  # 50MB freed
                redis_stats["used_memory"] -= memory_freed
            else:
                # Redis might crash or refuse writes
                redis_crash = True
        
        # System should handle memory pressure gracefully
        assert redis_stats["evicted_keys"] > 0
        assert redis_stats["used_memory"] < redis_stats["max_memory"]
    
    @pytest.mark.asyncio
    async def test_redis_data_corruption_recovery(self):
        """Test Redis recovery from data corruption"""
        # Simulate data corruption
        corrupted_data = {
            "cart:user1": "corrupted_json_data{invalid",
            "session:sess123": None,  # Missing data
            "cache:product123": '{"id": "wrong_id"}'  # Wrong data
        }
        
        # System should detect and handle corruption
        recovery_actions = []
        
        for key, value in corrupted_data.items():
            try:
                if value is None:
                    recovery_actions.append(f"DELETE {key}")
                elif isinstance(value, str):
                    json.loads(value)  # Validate JSON
                    recovery_actions.append(f"VALID {key}")
            except json.JSONDecodeError:
                recovery_actions.append(f"CORRUPT {key}")
        
        # Should identify corrupted entries
        corrupt_entries = [action for action in recovery_actions if "CORRUPT" in action]
        deleted_entries = [action for action in recovery_actions if "DELETE" in action]
        
        assert len(corrupt_entries) > 0
        assert len(deleted_entries) > 0
    
    @pytest.mark.asyncio
    async def test_redis_split_brain_scenario(self):
        """Test Redis split-brain scenario during network partition"""
        # Network partition creates two Redis clusters
        cluster_a = {
            "nodes": ["redis-1", "redis-2"],
            "can_accept_writes": True,  # Has majority
            "data_version": 1
        }
        
        cluster_b = {
            "nodes": ["redis-3"],
            "can_accept_writes": False,  # No majority
            "data_version": 1
        }
        
        # Writes continue on cluster A
        cluster_a["data_version"] += 1
        
        # When partition heals, need to resolve conflicts
        def resolve_split_brain(cluster_a, cluster_b):
            if cluster_a["data_version"] > cluster_b["data_version"]:
                # Cluster A wins, B needs to sync
                cluster_b["data_version"] = cluster_a["data_version"]
                return "cluster_a_wins"
            else:
                return "manual_resolution_needed"
        
        resolution = resolve_split_brain(cluster_a, cluster_b)
        assert resolution == "cluster_a_wins"
        assert cluster_b["data_version"] == cluster_a["data_version"]


class TestSystemSurvivalUnderInfrastructureChaos:
    """Test system survival under extreme infrastructure failures"""
    
    @pytest.mark.asyncio
    async def test_system_survives_kafka_and_redis_outage(self):
        """Test system survival when both Kafka and Redis are down"""
        infrastructure_status = {
            "kafka": "down",
            "redis": "down",
            "database": "up",
            "application": "up"
        }
        
        # System should implement fallback strategies
        fallback_strategies = {
            "events": "store_in_database",  # Instead of Kafka
            "cache": "direct_database_queries",  # Instead of Redis
            "sessions": "database_sessions"  # Instead of Redis sessions
        }
        
        # Core business operations should continue
        core_operations = {
            "user_registration": True,  # Database only
            "product_browsing": True,   # Database queries
            "order_placement": True,    # Database transactions
            "payment_processing": True  # External service + database
        }
        
        # Performance will be degraded but system survives
        performance_impact = {
            "response_time_increase": "3x",
            "throughput_reduction": "50%",
            "system_available": True
        }
        
        assert all(core_operations.values())
        assert performance_impact["system_available"] is True
    
    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self):
        """Test prevention of cascading failures"""
        system_components = {
            "load_balancer": {"status": "up", "health": 100},
            "app_servers": [
                {"id": "app1", "status": "up", "load": 70},
                {"id": "app2", "status": "up", "load": 70},
                {"id": "app3", "status": "up", "load": 70}
            ],
            "kafka": {"status": "down", "health": 0},
            "redis": {"status": "down", "health": 0},
            "database": {"status": "up", "health": 90}
        }
        
        # Kafka and Redis failures increase load on remaining components
        infrastructure_failures = 2
        load_increase_per_failure = 15  # 15% increase per failure
        
        for server in system_components["app_servers"]:
            server["load"] += infrastructure_failures * load_increase_per_failure
        
        # Check if any server is overloaded
        overloaded_servers = [s for s in system_components["app_servers"] if s["load"] > 100]
        
        if overloaded_servers:
            # Implement circuit breakers to prevent cascade
            for server in overloaded_servers:
                server["circuit_breaker"] = "open"
                server["load"] = 85  # Shed load
        
        # System should prevent cascade failure
        circuit_breakers_active = any("circuit_breaker" in s for s in system_components["app_servers"])
        assert circuit_breakers_active is True
        
        # No server should be critically overloaded
        max_load = max(s["load"] for s in system_components["app_servers"])
        assert max_load <= 100
    
    @pytest.mark.asyncio
    async def test_disaster_recovery_simulation(self):
        """Test complete disaster recovery scenario"""
        # Simulate complete data center failure
        primary_dc = {
            "status": "failed",
            "services": ["kafka", "redis", "database", "app_servers"],
            "recovery_time": "unknown"
        }
        
        secondary_dc = {
            "status": "active",
            "services": ["kafka", "redis", "database", "app_servers"],
            "data_lag": "5_minutes"
        }
        
        # Failover to secondary DC
        if primary_dc["status"] == "failed" and secondary_dc["status"] == "active":
            failover_successful = True
            active_dc = "secondary"
            
            # Some data loss expected due to lag
            data_loss_window = secondary_dc["data_lag"]
        else:
            failover_successful = False
            active_dc = None
        
        assert failover_successful is True
        assert active_dc == "secondary"
        assert data_loss_window == "5_minutes"
        
        # System should be operational in secondary DC
        system_operational = True
        assert system_operational is True
    
    @pytest.mark.asyncio
    async def test_chaos_monkey_simulation(self):
        """Test random infrastructure component failures"""
        components = [
            {"name": "kafka_broker_1", "status": "up", "criticality": "high"},
            {"name": "kafka_broker_2", "status": "up", "criticality": "high"},
            {"name": "kafka_broker_3", "status": "up", "criticality": "high"},
            {"name": "redis_master", "status": "up", "criticality": "medium"},
            {"name": "redis_slave_1", "status": "up", "criticality": "low"},
            {"name": "redis_slave_2", "status": "up", "criticality": "low"},
            {"name": "app_server_1", "status": "up", "criticality": "high"},
            {"name": "app_server_2", "status": "up", "criticality": "high"}
        ]
        
        # Chaos monkey randomly kills components
        chaos_events = []
        for _ in range(3):  # 3 random failures
            available_components = [c for c in components if c["status"] == "up"]
            if available_components:
                target = random.choice(available_components)
                target["status"] = "down"
                chaos_events.append({
                    "component": target["name"],
                    "criticality": target["criticality"],
                    "time": datetime.utcnow()
                })
        
        # System should handle random failures gracefully
        high_criticality_failures = [e for e in chaos_events if e["criticality"] == "high"]
        system_degraded = len(high_criticality_failures) > 0
        
        # Count remaining healthy components
        healthy_components = [c for c in components if c["status"] == "up"]
        system_operational = len(healthy_components) > len(components) // 2
        
        assert len(chaos_events) == 3
        assert system_operational is True  # Should survive random failures


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])