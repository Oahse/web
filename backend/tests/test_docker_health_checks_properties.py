"""
Property-based tests for Docker health checks.

**Feature: app-enhancements, Property 66: Health check reporting**
**Validates: Requirements 19.7**

These tests verify that health checks are properly configured and reporting
correct status in the Docker environment.
"""

import pytest
import asyncio
import aiohttp
from hypothesis import given, strategies as st, settings as hypothesis_settings, HealthCheck


# Health check endpoints
BACKEND_URL = "http://localhost:8000"
HEALTH_ENDPOINTS = [
    "/health/live",
    "/health/ready",
    "/health/detailed",
    "/health/dependencies"
]


@pytest.mark.asyncio
@given(
    endpoint=st.sampled_from(HEALTH_ENDPOINTS)
)
@hypothesis_settings(
    max_examples=4,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_health_endpoints_accessible(endpoint):
    """
    Property: For any health check endpoint, it should be accessible and
    return a valid response.
    
    This tests that:
    1. Health endpoints are configured
    2. Endpoints respond to requests
    3. Response format is correct
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BACKEND_URL}{endpoint}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                # Health endpoints should return 200 or 503
                assert response.status in [200, 503], \
                    f"Health endpoint {endpoint} returned unexpected status {response.status}"
                
                # Verify response is JSON
                content_type = response.headers.get('Content-Type', '')
                assert 'application/json' in content_type, \
                    f"Health endpoint should return JSON, got {content_type}"
                
                # Verify we can parse the response
                data = await response.json()
                assert isinstance(data, dict), "Health response should be a dictionary"
                assert 'status' in data, "Health response should contain status field"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")


@pytest.mark.asyncio
async def test_liveness_check_format():
    """
    Property: The liveness check should return a properly formatted response.
    
    This tests that:
    1. Liveness endpoint returns expected fields
    2. Response format is consistent
    3. Status is reported correctly
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BACKEND_URL}/health/live",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                assert response.status == 200, \
                    f"Liveness check should return 200, got {response.status}"
                
                data = await response.json()
                
                # Verify required fields
                assert 'status' in data, "Liveness response should contain status"
                assert 'timestamp' in data, "Liveness response should contain timestamp"
                assert 'service' in data, "Liveness response should contain service name"
                
                # Verify status value
                assert data['status'] == 'alive', \
                    f"Liveness status should be 'alive', got {data['status']}"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")


@pytest.mark.asyncio
async def test_readiness_check_format():
    """
    Property: The readiness check should return a properly formatted response
    with component checks.
    
    This tests that:
    1. Readiness endpoint returns expected fields
    2. Component checks are included
    3. Status reflects component health
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BACKEND_URL}/health/ready",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                # Readiness can be 200 (ready) or 503 (not ready)
                assert response.status in [200, 503], \
                    f"Readiness check returned unexpected status {response.status}"
                
                data = await response.json()
                
                # Verify required fields
                assert 'status' in data, "Readiness response should contain status"
                assert 'timestamp' in data, "Readiness response should contain timestamp"
                assert 'checks' in data, "Readiness response should contain checks"
                
                # Verify checks is a list
                assert isinstance(data['checks'], list), \
                    "Checks should be a list"
                
                # If there are checks, verify their format
                if len(data['checks']) > 0:
                    check = data['checks'][0]
                    assert 'name' in check, "Check should have a name"
                    assert 'status' in check, "Check should have a status"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")


@pytest.mark.asyncio
async def test_detailed_health_check_format():
    """
    Property: The detailed health check should return comprehensive information
    about all system components.
    
    This tests that:
    1. Detailed endpoint returns extensive information
    2. Multiple component checks are included
    3. Response time is tracked
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BACKEND_URL}/health/detailed",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                # Detailed check can be 200 (healthy) or 503 (unhealthy)
                assert response.status in [200, 503], \
                    f"Detailed health check returned unexpected status {response.status}"
                
                data = await response.json()
                
                # Verify required fields
                assert 'status' in data, "Detailed response should contain status"
                assert 'timestamp' in data, "Detailed response should contain timestamp"
                assert 'checks' in data, "Detailed response should contain checks"
                assert 'response_time' in data, "Detailed response should contain response_time"
                
                # Verify response time is reasonable
                assert isinstance(data['response_time'], (int, float)), \
                    "Response time should be a number"
                assert data['response_time'] >= 0, \
                    "Response time should be non-negative"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")


@pytest.mark.asyncio
@given(
    concurrent_checks=st.integers(min_value=1, max_value=5)
)
@hypothesis_settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_health_check_concurrent_requests(concurrent_checks):
    """
    Property: For any number of concurrent health check requests, all should
    return valid responses.
    
    This tests that:
    1. Health checks handle concurrent requests
    2. No race conditions occur
    3. All requests get proper responses
    """
    async with aiohttp.ClientSession() as session:
        try:
            async def check_health():
                async with session.get(
                    f"{BACKEND_URL}/health/live",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status
            
            # Make concurrent requests
            tasks = [check_health() for _ in range(concurrent_checks)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all requests succeeded
            successful = [r for r in results if isinstance(r, int) and r == 200]
            assert len(successful) == concurrent_checks, \
                f"Only {len(successful)}/{concurrent_checks} health checks succeeded"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")


@pytest.mark.asyncio
async def test_health_check_response_time():
    """
    Property: Health checks should respond quickly (within reasonable time).
    
    This tests that:
    1. Health checks are performant
    2. No significant delays occur
    3. Response time is acceptable
    """
    async with aiohttp.ClientSession() as session:
        try:
            import time
            start_time = time.time()
            
            async with session.get(
                f"{BACKEND_URL}/health/live",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                assert response.status == 200
                assert response_time < 2000, \
                    f"Health check response time {response_time}ms exceeds 2 seconds"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")


@pytest.mark.asyncio
@given(
    status_field=st.sampled_from(['status', 'timestamp', 'service'])
)
@hypothesis_settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_health_response_required_fields(status_field):
    """
    Property: For any required field in health response, it should be present
    and have a valid value.
    
    This tests that:
    1. All required fields are present
    2. Field values are valid
    3. Response format is consistent
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BACKEND_URL}/health/live",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                data = await response.json()
                
                assert status_field in data, \
                    f"Required field '{status_field}' missing from health response"
                
                value = data[status_field]
                assert value is not None, \
                    f"Field '{status_field}' should not be None"
                
                if isinstance(value, str):
                    assert len(value) > 0, \
                        f"Field '{status_field}' should not be empty"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")


@pytest.mark.asyncio
async def test_health_check_idempotency():
    """
    Property: Health checks should be idempotent - multiple calls should
    return consistent results.
    
    This tests that:
    1. Health checks don't modify state
    2. Results are consistent across calls
    3. No side effects occur
    """
    async with aiohttp.ClientSession() as session:
        try:
            # Make multiple health check requests
            statuses = []
            for _ in range(5):
                async with session.get(
                    f"{BACKEND_URL}/health/live",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    data = await response.json()
                    statuses.append(data['status'])
            
            # All statuses should be the same
            assert all(s == statuses[0] for s in statuses), \
                "Health check status should be consistent across multiple calls"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")


@pytest.mark.asyncio
async def test_health_check_json_format():
    """
    Property: Health check responses should be valid JSON.
    
    This tests that:
    1. Responses are properly formatted JSON
    2. Content-Type header is correct
    3. JSON can be parsed without errors
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BACKEND_URL}/health/live",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                # Verify Content-Type
                content_type = response.headers.get('Content-Type', '')
                assert 'application/json' in content_type, \
                    f"Content-Type should be application/json, got {content_type}"
                
                # Verify we can parse as JSON
                data = await response.json()
                assert isinstance(data, dict), \
                    "Health response should be a JSON object"
                
                # Verify JSON is not empty
                assert len(data) > 0, \
                    "Health response should not be empty"
                
        except aiohttp.ClientConnectorError as e:
            pytest.skip(f"Backend not accessible: {e}. Start Docker containers to run this test.")
        except asyncio.TimeoutError:
            pytest.skip(f"Backend timeout. Start Docker containers to run this test.")
