# Docker Property-Based Tests

## Overview

This directory contains property-based tests that verify Docker deployment functionality. These tests require Docker containers to be running and are marked with the `@pytest.mark.docker` marker.

## Docker Test Files

- `test_docker_api_proxy_properties.py` - Tests API proxy from frontend to backend
- `test_docker_database_connection_properties.py` - Tests database connectivity
- `test_docker_data_persistence_properties.py` - Tests data persistence across restarts
- `test_docker_environment_properties.py` - Tests environment variable accessibility
- `test_docker_health_checks_properties.py` - Tests health check reporting
- `test_docker_migrations_properties.py` - Tests database migrations on container start

## Running Docker Tests

### Prerequisites

1. Docker Desktop or Docker Engine installed and running
2. Docker Compose installed
3. All required environment variables configured (see `.env.example`)

### Steps to Run

1. **Start Docker containers:**
   ```bash
   docker compose up -d
   ```

2. **Wait for containers to be healthy:**
   ```bash
   docker compose ps
   ```
   All services should show "healthy" status.

3. **Run the Docker tests:**
   ```bash
   # Run all Docker tests
   pytest -m docker -v
   
   # Run a specific Docker test file
   pytest tests/test_docker_api_proxy_properties.py -v
   
   # Run with detailed skip reasons
   pytest -m docker -v -rs
   ```

4. **Stop containers when done:**
   ```bash
   docker compose down
   ```

## Skipping Docker Tests

If Docker is not running, these tests will automatically skip with a helpful message. You can also explicitly skip Docker tests:

```bash
# Run all tests EXCEPT Docker tests
pytest -m "not docker"
```

## CI/CD Considerations

In CI/CD pipelines, you may want to:

1. **Include Docker tests** (recommended for deployment validation):
   ```yaml
   - name: Run all tests including Docker
     run: |
       docker compose up -d
       pytest -v
       docker compose down
   ```

2. **Exclude Docker tests** (for faster unit test runs):
   ```yaml
   - name: Run unit tests only
     run: pytest -m "not docker" -v
   ```

## Troubleshooting

### Tests Skip with "Docker containers not running"

**Solution:** Start Docker containers:
```bash
docker compose up -d
```

### Tests Fail with Connection Errors

**Possible causes:**
1. Containers are starting but not yet healthy - wait a few seconds
2. Port conflicts - check if ports 8000 (backend) or 5173 (frontend) are in use
3. Environment variables missing - check `.env` files

**Check container status:**
```bash
docker compose ps
docker compose logs backend
docker compose logs frontend
```

### Tests Timeout

**Possible causes:**
1. Containers are slow to start - increase timeout in test
2. Resource constraints - allocate more memory/CPU to Docker
3. Network issues - check Docker network configuration

## Test Design

These tests use:
- **Hypothesis** for property-based testing
- **aiohttp** for async HTTP requests
- **pytest-asyncio** for async test support

Each test verifies a universal property that should hold across all valid inputs, ensuring robust Docker deployment functionality.
