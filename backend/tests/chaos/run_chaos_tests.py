"""
Chaos Engineering Test Runner
Orchestrates chaos tests to validate system resilience
"""

import asyncio
import subprocess
import sys
import time
import random
from datetime import datetime
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chaos_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ChaosTestRunner:
    """Orchestrates chaos engineering tests"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.utcnow()
        
    def run_test_suite(self, test_file, description):
        """Run a specific chaos test suite"""
        logger.info(f"🔥 Starting chaos test: {description}")
        
        start_time = time.time()
        
        try:
            # Run pytest with specific configuration for chaos tests
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file,
                "-v",
                "--tb=short",
                "--maxfail=5",  # Stop after 5 failures
                "--timeout=300",  # 5 minute timeout per test
                "-x"  # Stop on first failure for chaos tests
            ], capture_output=True, text=True, timeout=600)  # 10 minute total timeout
            
            end_time = time.time()
            duration = end_time - start_time
            
            test_result = {
                "test_file": test_file,
                "description": description,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.test_results.append(test_result)
            
            if result.returncode == 0:
                logger.info(f"✅ PASSED: {description} (Duration: {duration:.2f}s)")
            else:
                logger.error(f"❌ FAILED: {description} (Duration: {duration:.2f}s)")
                logger.error(f"Error output: {result.stderr}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ TIMEOUT: {description} exceeded time limit")
            return {
                "test_file": test_file,
                "description": description,
                "duration": 600,
                "return_code": -1,
                "error": "Test timeout",
                "passed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"💥 ERROR: {description} - {str(e)}")
            return {
                "test_file": test_file,
                "description": description,
                "error": str(e),
                "passed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_all_chaos_tests(self):
        """Run all chaos engineering tests"""
        logger.info("🚀 Starting Chaos Engineering Test Suite")
        logger.info("=" * 60)
        
        chaos_tests = [
            {
                "file": "tests/chaos/test_payment_kafka_failures.py",
                "description": "Payment Success with Kafka Failures"
            },
            {
                "file": "tests/chaos/test_kafka_event_duplication.py", 
                "description": "Kafka Event Duplication and Consumer Crashes"
            },
            {
                "file": "tests/chaos/test_consumer_random_kills.py",
                "description": "Random Consumer Kills and Recovery"
            },
            {
                "file": "tests/chaos/test_infrastructure_failures.py",
                "description": "Infrastructure Failures (Kafka/Redis)"
            }
        ]
        
        # Run tests sequentially to avoid resource conflicts
        for test_config in chaos_tests:
            self.run_test_suite(test_config["file"], test_config["description"])
            
            # Brief pause between test suites
            time.sleep(2)
        
        # Generate final report
        self.generate_report()
    
    def run_random_chaos_simulation(self, duration_minutes=10):
        """Run random chaos simulation for specified duration"""
        logger.info(f"🎲 Starting {duration_minutes}-minute random chaos simulation")
        
        end_time = time.time() + (duration_minutes * 60)
        chaos_events = []
        
        while time.time() < end_time:
            # Random chaos event
            chaos_type = random.choice([
                "kill_consumer",
                "network_partition", 
                "memory_pressure",
                "disk_full",
                "cpu_spike",
                "database_slowdown"
            ])
            
            chaos_event = {
                "type": chaos_type,
                "timestamp": datetime.utcnow().isoformat(),
                "duration": random.randint(10, 60)  # 10-60 seconds
            }
            
            logger.info(f"🔥 Chaos Event: {chaos_type} for {chaos_event['duration']}s")
            chaos_events.append(chaos_event)
            
            # Simulate chaos event
            await self.simulate_chaos_event(chaos_event)
            
            # Random interval between events
            time.sleep(random.randint(30, 120))  # 30-120 seconds
        
        logger.info(f"🏁 Random chaos simulation completed. Events: {len(chaos_events)}")
        return chaos_events
    
    async def simulate_chaos_event(self, event):
        """Simulate a specific chaos event"""
        event_type = event["type"]
        duration = event["duration"]
        
        if event_type == "kill_consumer":
            logger.info("💀 Simulating consumer kill...")
            # In real implementation, would actually kill consumer processes
            await asyncio.sleep(duration)
            
        elif event_type == "network_partition":
            logger.info("🌐 Simulating network partition...")
            # In real implementation, would use iptables or similar
            await asyncio.sleep(duration)
            
        elif event_type == "memory_pressure":
            logger.info("🧠 Simulating memory pressure...")
            # In real implementation, would consume memory
            await asyncio.sleep(duration)
            
        elif event_type == "disk_full":
            logger.info("💾 Simulating disk full...")
            # In real implementation, would fill disk space
            await asyncio.sleep(duration)
            
        elif event_type == "cpu_spike":
            logger.info("⚡ Simulating CPU spike...")
            # In real implementation, would create CPU load
            await asyncio.sleep(duration)
            
        elif event_type == "database_slowdown":
            logger.info("🐌 Simulating database slowdown...")
            # In real implementation, would add latency to DB
            await asyncio.sleep(duration)
        
        logger.info(f"✅ Chaos event {event_type} completed")
    
    def generate_report(self):
        """Generate comprehensive chaos test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("passed", False)])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(r.get("duration", 0) for r in self.test_results)
        
        report = {
            "chaos_test_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "total_duration_seconds": total_duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_results": self.test_results,
            "system_resilience_score": self.calculate_resilience_score()
        }
        
        # Save report to file
        report_file = f"chaos_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("🎯 CHAOS ENGINEERING TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {report['chaos_test_summary']['success_rate']:.1f}%")
        logger.info(f"Total Duration: {total_duration:.2f} seconds")
        logger.info(f"Resilience Score: {report['system_resilience_score']:.1f}/100")
        logger.info(f"Report saved to: {report_file}")
        
        # System survival assessment
        if report['system_resilience_score'] >= 80:
            logger.info("🎉 EXCELLENT: System demonstrates high resilience!")
        elif report['system_resilience_score'] >= 60:
            logger.info("👍 GOOD: System shows adequate resilience with room for improvement")
        else:
            logger.warning("⚠️  NEEDS IMPROVEMENT: System resilience requires attention")
        
        return report
    
    def calculate_resilience_score(self):
        """Calculate system resilience score based on test results"""
        if not self.test_results:
            return 0
        
        # Base score from pass rate
        pass_rate = len([r for r in self.test_results if r.get("passed", False)]) / len(self.test_results)
        base_score = pass_rate * 70  # 70 points for passing tests
        
        # Bonus points for specific resilience indicators
        bonus_points = 0
        
        # Bonus for handling payment success with Kafka failure
        payment_kafka_test = next((r for r in self.test_results if "payment_kafka" in r.get("test_file", "")), None)
        if payment_kafka_test and payment_kafka_test.get("passed", False):
            bonus_points += 10
        
        # Bonus for handling consumer crashes
        consumer_test = next((r for r in self.test_results if "consumer_random" in r.get("test_file", "")), None)
        if consumer_test and consumer_test.get("passed", False):
            bonus_points += 10
        
        # Bonus for infrastructure failure handling
        infra_test = next((r for r in self.test_results if "infrastructure" in r.get("test_file", "")), None)
        if infra_test and infra_test.get("passed", False):
            bonus_points += 10
        
        total_score = min(100, base_score + bonus_points)
        return total_score


def main():
    """Main entry point for chaos testing"""
    runner = ChaosTestRunner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--random":
        # Run random chaos simulation
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        asyncio.run(runner.run_random_chaos_simulation(duration))
    else:
        # Run standard chaos test suite
        runner.run_all_chaos_tests()


if __name__ == "__main__":
    main()