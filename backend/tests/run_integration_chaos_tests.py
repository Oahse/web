#!/usr/bin/env python3
"""
Test runner for integration and chaos tests
Runs comprehensive test suites for checkout integration testing
"""
import asyncio
import subprocess
import sys
import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
import pytest
import docker
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestEnvironment:
    """Manages test environment setup and teardown"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.containers = {}
        self.test_db_name = "test_banwee_db"
        
    async def setup_test_infrastructure(self):
        """Setup test infrastructure (Redis, PostgreSQL)"""
        logger.info("Setting up test infrastructure...")
        
        # Start PostgreSQL test container
        await self._start_postgres()
        
        # Start Redis test container
        await self._start_redis()
        
        # Wait for services to be ready
        await self._wait_for_services()
        
        logger.info("Test infrastructure ready")
    
    async def _start_postgres(self):
        """Start PostgreSQL test container"""
        try:
            container = self.docker_client.containers.run(
                "postgres:15",
                environment={
                    "POSTGRES_DB": self.test_db_name,
                    "POSTGRES_USER": "test_user",
                    "POSTGRES_PASSWORD": "test_password"
                },
                ports={"5432/tcp": 5433},  # Use different port for tests
                detach=True,
                remove=True,
                name="test_postgres"
            )
            self.containers["postgres"] = container
            logger.info("PostgreSQL test container started")
        except Exception as e:
            logger.error(f"Failed to start PostgreSQL: {e}")
            raise
    
    async def _start_redis(self):
        """Start Redis test container"""
        try:
            container = self.docker_client.containers.run(
                "redis:7-alpine",
                ports={"6379/tcp": 6380},  # Use different port for tests
                detach=True,
                remove=True,
                name="test_redis"
            )
            self.containers["redis"] = container
            logger.info("Redis test container started")
        except Exception as e:
            logger.error(f"Failed to start Redis: {e}")
            raise
    
    async def _wait_for_services(self):
        """Wait for all services to be ready"""
        logger.info("Waiting for services to be ready...")
        
        # Wait for PostgreSQL
        await self._wait_for_postgres()
        
        # Wait for Redis
        await self._wait_for_redis()
        
        # Wait for Kafka
        await self._wait_for_kafka()
        
        logger.info("All services are ready")
    
    async def _wait_for_postgres(self):
        """Wait for PostgreSQL to be ready"""
        import psycopg2
        
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5433,
                    database=self.test_db_name,
                    user="test_user",
                    password="test_password"
                )
                conn.close()
                logger.info("PostgreSQL is ready")
                return
            except psycopg2.OperationalError:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                else:
                    raise Exception("PostgreSQL failed to start")
    
    async def _wait_for_redis(self):
        """Wait for Redis to be ready"""
        import redis
        
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                r = redis.Redis(host="localhost", port=6380)
                r.ping()
                logger.info("Redis is ready")
                return
            except redis.ConnectionError:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)
                else:
                    raise Exception("Redis failed to start")
    
    async def _wait_for_kafka(self):
        """Wait for Kafka to be ready"""
        from kafka import KafkaProducer
        from kafka.errors import NoBrokersAvailable
        
        max_attempts = 60
        for attempt in range(max_attempts):
            try:
                producer = KafkaProducer(
                    bootstrap_servers=['localhost:9093'],
                    value_serializer=lambda v: v.encode('utf-8')
                )
                producer.close()
                logger.info("Kafka is ready")
                return
            except NoBrokersAvailable:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                else:
                    raise Exception("Kafka failed to start")
    
    async def teardown_test_infrastructure(self):
        """Teardown test infrastructure"""
        logger.info("Tearing down test infrastructure...")
        
        for name, container in self.containers.items():
            try:
                container.stop()
                logger.info(f"Stopped {name} container")
            except Exception as e:
                logger.error(f"Failed to stop {name} container: {e}")
        
        self.containers.clear()
        logger.info("Test infrastructure torn down")


class TestRunner:
    """Runs integration and chaos tests"""
    
    def __init__(self):
        self.test_env = TestEnvironment()
        self.test_results = {}
    
    async def run_all_tests(self):
        """Run all integration and chaos tests"""
        logger.info("Starting comprehensive test suite...")
        
        try:
            # Setup test environment
            await self.test_env.setup_test_infrastructure()
            
            # Set test environment variables
            self._set_test_env_vars()
            
            # Run integration tests
            await self._run_integration_tests()
            
            # Run chaos tests
            await self._run_chaos_tests()
            
            # Run frontend integration tests
            await self._run_frontend_tests()
            
            # Generate test report
            self._generate_test_report()
            
        finally:
            # Cleanup
            await self.test_env.teardown_test_infrastructure()
    
    def _set_test_env_vars(self):
        """Set environment variables for testing"""
        os.environ.update({
            "DATABASE_URL": "postgresql://test_user:test_password@localhost:5433/test_banwee_db",
            "REDIS_URL": "redis://localhost:6380",
            "KAFKA_BOOTSTRAP_SERVERS": "localhost:9093",
            "TESTING": "true",
            "LOG_LEVEL": "INFO"
        })
    
    async def _run_integration_tests(self):
        """Run backend integration tests"""
        logger.info("Running backend integration tests...")
        
        test_files = [
            "tests/integration/test_checkout_integration.py",
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                result = await self._run_pytest(test_file, "integration")
                self.test_results[f"integration_{test_file}"] = result
            else:
                logger.warning(f"Test file not found: {test_file}")
    
    async def _run_chaos_tests(self):
        """Run consumer chaos tests"""
        logger.info("Running consumer chaos tests...")
        
        test_files = [
            "tests/chaos/test_consumer_random_kills.py",
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                result = await self._run_pytest(test_file, "chaos")
                self.test_results[f"chaos_{test_file}"] = result
            else:
                logger.warning(f"Test file not found: {test_file}")
    
    async def _run_frontend_tests(self):
        """Run frontend integration tests"""
        logger.info("Running frontend integration tests...")
        
        # Change to frontend directory
        frontend_dir = Path("../frontend")
        if frontend_dir.exists():
            result = await self._run_vitest()
            self.test_results["frontend_integration"] = result
        else:
            logger.warning("Frontend directory not found")
    
    async def _run_pytest(self, test_file: str, test_type: str) -> Dict[str, Any]:
        """Run pytest for a specific test file"""
        cmd = [
            "python", "-m", "pytest",
            test_file,
            "-v",
            "--tb=short",
            "--durations=10",
            f"--junitxml=test_results_{test_type}_{Path(test_file).stem}.xml"
        ]
        
        if test_type == "chaos":
            # Add chaos-specific options
            cmd.extend([
                "--maxfail=5",  # Stop after 5 failures for chaos tests
                "--timeout=300"  # 5 minute timeout for chaos tests
            ])
        
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "success": process.returncode == 0,
                "duration": duration,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "return_code": process.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to run {test_file}: {e}")
            return {
                "success": False,
                "duration": 0,
                "error": str(e),
                "return_code": -1
            }
    
    async def _run_vitest(self) -> Dict[str, Any]:
        """Run Vitest for frontend tests"""
        cmd = ["npm", "run", "test:integration"]
        
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd="../frontend",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "success": process.returncode == 0,
                "duration": duration,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "return_code": process.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to run frontend tests: {e}")
            return {
                "success": False,
                "duration": 0,
                "error": str(e),
                "return_code": -1
            }
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating test report...")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - successful_tests
        total_duration = sum(result["duration"] for result in self.test_results.values())
        
        report = f"""
=== INTEGRATION AND CHAOS TEST REPORT ===

Summary:
- Total Test Suites: {total_tests}
- Successful: {successful_tests}
- Failed: {failed_tests}
- Total Duration: {total_duration:.2f} seconds

Detailed Results:
"""
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            report += f"\n{test_name}: {status} ({result['duration']:.2f}s)"
            
            if not result["success"]:
                if "error" in result:
                    report += f"\n  Error: {result['error']}"
                if result.get("stderr"):
                    report += f"\n  Stderr: {result['stderr'][:200]}..."
        
        report += f"\n\n=== END REPORT ===\n"
        
        # Write report to file
        with open("test_report.txt", "w") as f:
            f.write(report)
        
        # Print to console
        print(report)
        
        # Exit with appropriate code
        if failed_tests > 0:
            logger.error(f"{failed_tests} test suite(s) failed")
            sys.exit(1)
        else:
            logger.info("All test suites passed!")
            sys.exit(0)


async def main():
    """Main entry point"""
    runner = TestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    # Check dependencies
    try:
        import docker
        import pytest
        import psycopg2
        import redis
        import kafka
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Install with: pip install docker pytest psycopg2-binary redis-py")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())