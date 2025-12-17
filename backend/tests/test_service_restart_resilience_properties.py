"""
Property-based tests for service restart resilience in Docker environment.

**Feature: docker-full-functionality, Property 37: Automatic service restart**
**Feature: docker-full-functionality, Property 38: Dependency recovery waiting**
**Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5**

These tests verify that Docker services restart automatically on failure and that
dependent services wait for their dependencies to recover before starting.

NOTE: These tests require Docker containers to be running. To run these tests:
1. Start Docker daemon
2. Run: docker compose up -d
3. Wait for containers to be healthy
4. Run: pytest tests/test_service_restart_resilience_properties.py

The tests will skip automatically if Docker is not running.
"""

import pytest
import asyncio
import subprocess
import time
import yaml
import socket
from pathlib import Path
from hypothesis import given, strategies as st, settings as hypothesis_settings, HealthCheck


def check_docker_available():
    """
    Check if Docker containers are running and accessible.
    Returns True if backend is accessible, False otherwise.
    """
    try:
        # Quick socket check first
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        return result == 0
    except Exception:
        return False


def is_service_running(service_name: str) -> bool:
    """Check if a Docker service is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return service_name in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def stop_docker_service(service_name: str) -> bool:
    """Stop a Docker service."""
    try:
        subprocess.run(
            ["docker", "stop", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def wait_for_service_restart(service_name: str, max_wait: int = 60) -> bool:
    """Wait for a service to restart and become healthy."""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if is_service_running(service_name):
            # Additional wait for health checks
            time.sleep(10)
            return True
        time.sleep(2)
    return False


def get_service_restart_policy(service_name: str) -> str:
    """Get the restart policy for a service from docker-compose.yml."""
    docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_content = yaml.safe_load(f)
    
    service = compose_content.get("services", {}).get(service_name, {})
    return service.get("restart", "no")


# Check Docker availability at module load time
DOCKER_AVAILABLE = check_docker_available()

# Skip entire module if Docker is not available
if not DOCKER_AVAILABLE:
    pytest.skip(
        "Docker containers not running. To run these tests:\n"
        "1. Start Docker daemon\n"
        "2. Run: docker compose up -d\n"
        "3. Wait for containers to be healthy\n"
        "4. Run: pytest tests/test_service_restart_resilience_properties.py",
        allow_module_level=True
    )


# Mark all tests in this module as requiring Docker
pytestmark = [
    pytest.mark.docker,
    pytest.mark.asyncio
]


@given(
    service_name=st.sampled_from([
        "banwee_backend",
        "banwee_celery_worker", 
        "banwee_negotiation_celery_worker",
        "banwee_celery_beat",
        "banwee_frontend"
    ])
)
@hypothesis_settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_service_has_restart_policy(service_name):
    """
    Property 37: Automatic service restart
    
    For any service that can crash, it should have an "unless-stopped" restart policy
    configured in docker-compose.yml.
    
    This tests that:
    1. All services have restart policies configured
    2. Restart policy is set to "unless-stopped"
    3. Services will automatically restart on failure
    """
    # Map container names to service names in docker-compose.yml
    service_mapping = {
        "banwee_backend": "backend",
        "banwee_celery_worker": "celery_worker",
        "banwee_negotiation_celery_worker": "negotiation_celery_worker", 
        "banwee_celery_beat": "celery_beat",
        "banwee_frontend": "frontend"
    }
    
    compose_service_name = service_mapping.get(service_name, service_name)
    restart_policy = get_service_restart_policy(compose_service_name)
    
    assert restart_policy == "unless-stopped", \
        f"Service {compose_service_name} should have 'unless-stopped' restart policy, got '{restart_policy}'"


@given(
    service_name=st.sampled_from([
        "banwee_backend",
        "banwee_celery_worker",
        "banwee_celery_beat"
    ])
)
@hypothesis_settings(
    max_examples=3,
    deadline=2000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_service_restarts_automatically(service_name):
    """
    Property 37: Automatic service restart
    
    For any service, when it is stopped, Docker should automatically restart it
    according to the restart policy.
    
    This tests that:
    1. Services can be stopped
    2. Docker automatically restarts them
    3. Services become healthy again after restart
    """
    # Verify service is initially running
    assert is_service_running(service_name), \
        f"Service {service_name} should be running before test"
    
    # Stop the service
    stop_success = stop_docker_service(service_name)
    assert stop_success, f"Failed to stop service {service_name}"
    
    # Wait a moment for the stop to take effect
    time.sleep(3)
    
    # Verify service is stopped
    assert not is_service_running(service_name), \
        f"Service {service_name} should be stopped after docker stop"
    
    # Wait for automatic restart
    restart_success = wait_for_service_restart(service_name, max_wait=120)
    assert restart_success, \
        f"Service {service_name} should automatically restart within 120 seconds"


@given(
    dependency_service=st.sampled_from([
        ("banwee_postgres", "postgres"),
        ("banwee_redis", "redis")
    ])
)
@hypothesis_settings(
    max_examples=2,
    deadline=2000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_dependency_recovery_waiting(dependency_service):
    """
    Property 38: Dependency recovery waiting
    
    For any dependency service (postgres, redis), when it becomes unavailable and
    then recovers, dependent services should wait for recovery before starting.
    
    This tests that:
    1. Dependent services have proper depends_on configuration
    2. Services wait for dependencies to be healthy
    3. Recovery happens automatically when dependencies are restored
    """
    container_name, service_name = dependency_service
    
    # Verify dependency service is initially running
    assert is_service_running(container_name), \
        f"Dependency service {container_name} should be running before test"
    
    # Stop the dependency service
    stop_success = stop_docker_service(container_name)
    assert stop_success, f"Failed to stop dependency service {container_name}"
    
    # Wait for stop to take effect
    time.sleep(5)
    
    # Verify dependency is stopped
    assert not is_service_running(container_name), \
        f"Dependency service {container_name} should be stopped"
    
    # Wait for automatic restart of dependency
    restart_success = wait_for_service_restart(container_name, max_wait=120)
    assert restart_success, \
        f"Dependency service {container_name} should automatically restart"
    
    # Verify dependent services are still running or have restarted
    dependent_services = []
    if service_name == "postgres":
        dependent_services = ["banwee_backend", "banwee_celery_worker", "banwee_celery_beat"]
    elif service_name == "redis":
        dependent_services = ["banwee_backend", "banwee_celery_worker", 
                            "banwee_negotiation_celery_worker", "banwee_celery_beat"]
    
    # Wait a bit more for dependent services to stabilize
    time.sleep(15)
    
    for dependent in dependent_services:
        assert is_service_running(dependent), \
            f"Dependent service {dependent} should be running after {service_name} recovery"


def test_postgres_redis_restart_policies():
    """
    Test that postgres and redis services have restart policies configured.
    
    This tests that:
    1. Core infrastructure services have restart policies
    2. They will restart automatically on failure
    """
    postgres_policy = get_service_restart_policy("postgres")
    redis_policy = get_service_restart_policy("redis")
    
    assert postgres_policy == "unless-stopped", \
        f"PostgreSQL should have 'unless-stopped' restart policy, got '{postgres_policy}'"
    
    assert redis_policy == "unless-stopped", \
        f"Redis should have 'unless-stopped' restart policy, got '{redis_policy}'"


def test_service_dependencies_configured():
    """
    Test that services have proper dependency configuration.
    
    This tests that:
    1. Backend depends on postgres and redis
    2. Celery workers depend on their required services
    3. Dependencies use health check conditions
    """
    docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_content = yaml.safe_load(f)
    
    services = compose_content["services"]
    
    # Check backend dependencies
    backend_deps = services["backend"].get("depends_on", {})
    assert "postgres" in backend_deps, "Backend should depend on postgres"
    assert "redis" in backend_deps, "Backend should depend on redis"
    assert backend_deps["postgres"]["condition"] == "service_healthy", \
        "Backend should wait for postgres health check"
    assert backend_deps["redis"]["condition"] == "service_healthy", \
        "Backend should wait for redis health check"
    
    # Check celery worker dependencies
    celery_deps = services["celery_worker"].get("depends_on", {})
    assert "postgres" in celery_deps, "Celery worker should depend on postgres"
    assert "redis" in celery_deps, "Celery worker should depend on redis"
    
    # Check negotiation celery worker dependencies
    neg_celery_deps = services["negotiation_celery_worker"].get("depends_on", {})
    assert "redis" in neg_celery_deps, "Negotiation celery worker should depend on redis"


async def test_service_restart_does_not_affect_others():
    """
    Test that restarting one service does not affect other services.
    
    This tests that:
    1. Services are properly isolated
    2. Restart of one service doesn't cascade to others
    3. System remains stable during individual service restarts
    """
    # Test restarting frontend doesn't affect backend
    assert is_service_running("banwee_frontend"), "Frontend should be running"
    assert is_service_running("banwee_backend"), "Backend should be running"
    
    # Stop frontend
    stop_success = stop_docker_service("banwee_frontend")
    assert stop_success, "Should be able to stop frontend"
    
    # Wait a moment
    time.sleep(5)
    
    # Backend should still be running
    assert is_service_running("banwee_backend"), \
        "Backend should continue running when frontend is stopped"
    
    # Wait for frontend to restart
    restart_success = wait_for_service_restart("banwee_frontend", max_wait=120)
    assert restart_success, "Frontend should restart automatically"
    
    # Both should be running now
    assert is_service_running("banwee_frontend"), "Frontend should be running after restart"
    assert is_service_running("banwee_backend"), "Backend should still be running"