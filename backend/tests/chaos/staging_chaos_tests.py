"""
Staging Environment Chaos Tests
Real infrastructure chaos tests for staging environment
WARNING: Only run in staging/test environments, never in production!
"""

import asyncio
import subprocess
import docker
import redis
import time
import logging
from datetime import datetime
import json
import os
import signal
import psutil

logger = logging.getLogger(__name__)


class StagingChaosRunner:
    """Runs real chaos tests in staging environment"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.chaos_events = []
        
    async def kill_kafka_brokers_randomly(self, duration_minutes=5):
        """Randomly kill Kafka brokers in staging"""
        logger.info(f"🔥 Starting random Kafka broker kills for {duration_minutes} minutes")
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                # Find Kafka containers
                kafka_containers = self.docker_client.containers.list(
                    filters={"name": "kafka"}
                )
                
                if kafka_containers:
                    # Randomly select a broker to kill
                    import random
                    target_broker = random.choice(kafka_containers)
                    
                    logger.info(f"💀 Killing Kafka broker: {target_broker.name}")
                    
                    # Kill the container
                    target_broker.kill()
                    
                    self.chaos_events.append({
                        "type": "kafka_broker_kill",
                        "target": target_broker.name,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Wait before potentially restarting
                    await asyncio.sleep(random.randint(30, 120))
                    
                    # Randomly decide whether to restart immediately
                    if random.random() < 0.7:  # 70% chance to restart
                        logger.info(f"🔄 Restarting Kafka broker: {target_broker.name}")
                        target_broker.restart()
                        
                        self.chaos_events.append({
                            "type": "kafka_broker_restart",
                            "target": target_broker.name,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                
                # Wait before next potential kill
                await asyncio.sleep(random.randint(60, 180))
                
            except Exception as e:
                logger.error(f"Error during Kafka chaos: {e}")
                await asyncio.sleep(30)
    
    async def restart_redis_randomly(self, duration_minutes=5):
        """Randomly restart Redis instances"""
        logger.info(f"🔄 Starting random Redis restarts for {duration_minutes} minutes")
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                # Find Redis containers
                redis_containers = self.docker_client.containers.list(
                    filters={"name": "redis"}
                )
                
                if redis_containers:
                    import random
                    target_redis = random.choice(redis_containers)
                    
                    logger.info(f"🔄 Restarting Redis: {target_redis.name}")
                    
                    # Restart Redis container
                    target_redis.restart()
                    
                    self.chaos_events.append({
                        "type": "redis_restart",
                        "target": target_redis.name,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Wait for Redis to come back up
                    await asyncio.sleep(10)
                    
                    # Test Redis connectivity
                    await self.test_redis_connectivity()
                
                # Wait before next restart
                await asyncio.sleep(random.randint(120, 300))
                
            except Exception as e:
                logger.error(f"Error during Redis chaos: {e}")
                await asyncio.sleep(30)
    
    async def kill_consumers_randomly(self, duration_minutes=5):
        """Randomly kill consumer processes"""
        logger.info(f"💀 Starting random consumer kills for {duration_minutes} minutes")
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                # Find consumer processes
                consumer_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'consumer' in cmdline.lower() or 'kafka' in cmdline.lower():
                            consumer_processes.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if consumer_processes:
                    import random
                    target_process = random.choice(consumer_processes)
                    
                    logger.info(f"💀 Killing consumer process: PID {target_process.pid}")
                    
                    # Kill process with SIGKILL (simulates crash)
                    if random.random() < 0.5:
                        target_process.kill()  # SIGKILL
                        kill_type = "SIGKILL"
                    else:
                        target_process.terminate()  # SIGTERM
                        kill_type = "SIGTERM"
                    
                    self.chaos_events.append({
                        "type": "consumer_kill",
                        "target": f"PID_{target_process.pid}",
                        "kill_type": kill_type,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Wait before next kill
                await asyncio.sleep(random.randint(45, 90))
                
            except Exception as e:
                logger.error(f"Error during consumer chaos: {e}")
                await asyncio.sleep(30)
    
    async def create_network_partitions(self, duration_minutes=3):
        """Create network partitions between services"""
        logger.info(f"🌐 Creating network partitions for {duration_minutes} minutes")
        
        try:
            # Block traffic between Kafka brokers (simulate split-brain)
            partition_commands = [
                "iptables -A INPUT -s kafka-1 -j DROP",
                "iptables -A OUTPUT -d kafka-1 -j DROP"
            ]
            
            for cmd in partition_commands:
                try:
                    subprocess.run(cmd.split(), check=True)
                    logger.info(f"Applied network rule: {cmd}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to apply network rule: {e}")
            
            self.chaos_events.append({
                "type": "network_partition_start",
                "rules": partition_commands,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Wait for partition duration
            await asyncio.sleep(duration_minutes * 60)
            
            # Remove partition rules
            cleanup_commands = [
                "iptables -D INPUT -s kafka-1 -j DROP",
                "iptables -D OUTPUT -d kafka-1 -j DROP"
            ]
            
            for cmd in cleanup_commands:
                try:
                    subprocess.run(cmd.split(), check=True)
                    logger.info(f"Removed network rule: {cmd}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to remove network rule: {e}")
            
            self.chaos_events.append({
                "type": "network_partition_end",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error during network partition: {e}")
    
    async def simulate_memory_pressure(self, duration_minutes=2):
        """Simulate memory pressure on the system"""
        logger.info(f"🧠 Simulating memory pressure for {duration_minutes} minutes")
        
        try:
            # Allocate memory to create pressure
            memory_hogs = []
            target_memory_mb = 512  # 512MB
            
            for i in range(target_memory_mb):
                # Allocate 1MB chunks
                memory_chunk = bytearray(1024 * 1024)  # 1MB
                memory_hogs.append(memory_chunk)
                
                if i % 50 == 0:  # Log every 50MB
                    logger.info(f"Allocated {i}MB of memory")
                
                await asyncio.sleep(0.1)  # Small delay
            
            self.chaos_events.append({
                "type": "memory_pressure_start",
                "allocated_mb": len(memory_hogs),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Hold memory for duration
            await asyncio.sleep(duration_minutes * 60)
            
            # Release memory
            memory_hogs.clear()
            
            self.chaos_events.append({
                "type": "memory_pressure_end",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info("Memory pressure simulation completed")
            
        except Exception as e:
            logger.error(f"Error during memory pressure simulation: {e}")
    
    async def test_redis_connectivity(self):
        """Test Redis connectivity after chaos events"""
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            logger.info("✅ Redis connectivity test passed")
            return True
        except Exception as e:
            logger.warning(f"❌ Redis connectivity test failed: {e}")
            return False
    
    async def test_kafka_connectivity(self):
        """Test Kafka connectivity after chaos events"""
        try:
            # Simple Kafka connectivity test
            # In real implementation, would use kafka-python or similar
            result = subprocess.run([
                "kafka-topics", "--bootstrap-server", "localhost:9092", "--list"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("✅ Kafka connectivity test passed")
                return True
            else:
                logger.warning(f"❌ Kafka connectivity test failed: {result.stderr}")
                return False
        except Exception as e:
            logger.warning(f"❌ Kafka connectivity test failed: {e}")
            return False
    
    async def run_application_health_checks(self):
        """Run application health checks during chaos"""
        logger.info("🏥 Running application health checks")
        
        health_results = {}
        
        # Test API endpoints
        endpoints_to_test = [
            "http://localhost:8000/health",
            "http://localhost:8000/products/",
            "http://localhost:8000/cart/",
            "http://localhost:8000/orders/"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                import requests
                response = requests.get(endpoint, timeout=5)
                health_results[endpoint] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "healthy": response.status_code < 500
                }
                
                if response.status_code < 500:
                    logger.info(f"✅ {endpoint} - {response.status_code}")
                else:
                    logger.warning(f"❌ {endpoint} - {response.status_code}")
                    
            except Exception as e:
                health_results[endpoint] = {
                    "error": str(e),
                    "healthy": False
                }
                logger.warning(f"❌ {endpoint} - {str(e)}")
        
        return health_results
    
    async def run_comprehensive_chaos_test(self, duration_minutes=10):
        """Run comprehensive chaos test with multiple failure types"""
        logger.info(f"🚀 Starting comprehensive chaos test for {duration_minutes} minutes")
        
        # Start multiple chaos scenarios concurrently
        chaos_tasks = [
            asyncio.create_task(self.kill_kafka_brokers_randomly(duration_minutes)),
            asyncio.create_task(self.restart_redis_randomly(duration_minutes)),
            asyncio.create_task(self.kill_consumers_randomly(duration_minutes)),
        ]
        
        # Add network partitions and memory pressure at intervals
        asyncio.create_task(self.create_network_partitions(2))
        asyncio.create_task(self.simulate_memory_pressure(3))
        
        # Run health checks every 30 seconds
        health_check_task = asyncio.create_task(self.periodic_health_checks(duration_minutes))
        
        # Wait for all chaos tasks to complete
        await asyncio.gather(*chaos_tasks, health_check_task, return_exceptions=True)
        
        # Generate final report
        await self.generate_chaos_report()
    
    async def periodic_health_checks(self, duration_minutes):
        """Run periodic health checks during chaos"""
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            health_results = await self.run_application_health_checks()
            
            self.chaos_events.append({
                "type": "health_check",
                "results": health_results,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def generate_chaos_report(self):
        """Generate comprehensive chaos test report"""
        report = {
            "chaos_test_summary": {
                "total_events": len(self.chaos_events),
                "event_types": list(set(event["type"] for event in self.chaos_events)),
                "start_time": self.chaos_events[0]["timestamp"] if self.chaos_events else None,
                "end_time": self.chaos_events[-1]["timestamp"] if self.chaos_events else None
            },
            "events": self.chaos_events,
            "system_survival_assessment": await self.assess_system_survival()
        }
        
        # Save report
        report_file = f"staging_chaos_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Chaos test report saved to: {report_file}")
        
        # Print summary
        logger.info("=" * 60)
        logger.info("🎯 STAGING CHAOS TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Chaos Events: {report['chaos_test_summary']['total_events']}")
        logger.info(f"Event Types: {', '.join(report['chaos_test_summary']['event_types'])}")
        
        survival_score = report['system_survival_assessment']['survival_score']
        logger.info(f"System Survival Score: {survival_score}/100")
        
        if survival_score >= 80:
            logger.info("🎉 EXCELLENT: System survived chaos testing!")
        elif survival_score >= 60:
            logger.info("👍 GOOD: System showed resilience with some degradation")
        else:
            logger.warning("⚠️  NEEDS IMPROVEMENT: System struggled under chaos")
        
        return report
    
    async def assess_system_survival(self):
        """Assess how well the system survived chaos testing"""
        health_checks = [e for e in self.chaos_events if e["type"] == "health_check"]
        
        if not health_checks:
            return {"survival_score": 0, "assessment": "No health data available"}
        
        # Calculate average health across all checks
        total_endpoints = 0
        healthy_endpoints = 0
        
        for check in health_checks:
            for endpoint, result in check["results"].items():
                total_endpoints += 1
                if result.get("healthy", False):
                    healthy_endpoints += 1
        
        if total_endpoints == 0:
            survival_rate = 0
        else:
            survival_rate = healthy_endpoints / total_endpoints
        
        survival_score = survival_rate * 100
        
        # Assess different failure types
        kafka_kills = len([e for e in self.chaos_events if e["type"] == "kafka_broker_kill"])
        redis_restarts = len([e for e in self.chaos_events if e["type"] == "redis_restart"])
        consumer_kills = len([e for e in self.chaos_events if e["type"] == "consumer_kill"])
        
        assessment = {
            "survival_score": survival_score,
            "survival_rate": survival_rate,
            "chaos_events_survived": {
                "kafka_broker_kills": kafka_kills,
                "redis_restarts": redis_restarts,
                "consumer_kills": consumer_kills
            },
            "assessment": "System demonstrated resilience" if survival_score >= 70 else "System needs improvement"
        }
        
        return assessment


async def main():
    """Main entry point for staging chaos tests"""
    if os.getenv("ENVIRONMENT") != "staging":
        logger.error("❌ SAFETY CHECK: These tests should only run in staging environment!")
        logger.error("Set ENVIRONMENT=staging to proceed")
        return
    
    logger.warning("⚠️  WARNING: Running destructive chaos tests in staging environment")
    logger.warning("This will kill processes, restart services, and create network partitions")
    
    # Confirmation prompt
    confirmation = input("Type 'CHAOS' to confirm you want to proceed: ")
    if confirmation != "CHAOS":
        logger.info("Chaos tests cancelled")
        return
    
    runner = StagingChaosRunner()
    
    # Run comprehensive chaos test
    await runner.run_comprehensive_chaos_test(duration_minutes=10)


if __name__ == "__main__":
    asyncio.run(main())