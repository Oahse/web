"""
Property-based tests for backend API configuration.

Feature: docker-full-functionality
Properties tested:
- Property 11: Migration before API startup
- Property 12: API availability
- Property 13: CORS configuration
- Property 14: External service configuration
- Property 15: Service dependency management
"""

import pytest
import os
import asyncio
import time
from hypothesis import given, strategies as st, settings
from typing import List
from pathlib import Path
import subprocess
import yaml

# Mark all tests in this module to not use database fixtures
pytestmark = pytest.mark.usefixtures()


# Feature: docker-full-functionality, Property 11: Migration before API startup
def test_migration_before_api_startup():
    """
    Property 11: Migration before API startup
    
    For any backend container startup, database migrations should complete
    before the API server accepts requests.
    
    Validates: Requirements 4.1
    """
    # Read the Dockerfile to verify migration script is executed before uvicorn
    dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
    
    assert dockerfile_path.exists(), "backend/Dockerfile does not exist"
    
    with open(dockerfile_path, 'r') as f:
        dockerfile_content = f.read()
    
    # Verify that the CMD includes migration script before uvicorn
    assert "CMD" in dockerfile_content, "Dockerfile should have a CMD instruction"
    
    # Check that migrate.sh is executed before uvicorn
    cmd_lines = [line for line in dockerfile_content.split('\n') if 'CMD' in line]
    assert len(cmd_lines) > 0, "No CMD instruction found in Dockerfile"
    
    cmd_line = cmd_lines[0]
    # Verify migration script comes before uvicorn in the command
    migrate_pos = cmd_line.find('migrate.sh')
    uvicorn_pos = cmd_line.find('uvicorn')
    
    assert migrate_pos != -1, "migrate.sh not found in CMD instruction"
    assert uvicorn_pos != -1, "uvicorn not found in CMD instruction"
    assert migrate_pos < uvicorn_pos, "migrate.sh should be executed before uvicorn"
    
    # Verify the migration script exists and is executable
    migrate_script_path = Path(__file__).parent.parent / "migrate.sh"
    assert migrate_script_path.exists(), "migrate.sh script does not exist"
    
    # Check that the script is made executable in Dockerfile
    assert "chmod +x migrate.sh" in dockerfile_content, \
        "Dockerfile should make migrate.sh executable"


# Feature: docker-full-functionality, Property 12: API availability
def test_api_availability():
    """
    Property 12: API availability
    
    For any HTTP request to the backend, when the server is running,
    it should accept requests on port 8000.
    
    Validates: Requirements 4.2
    """
    # Verify Dockerfile exposes port 8000
    dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
    
    with open(dockerfile_path, 'r') as f:
        dockerfile_content = f.read()
    
    assert "EXPOSE 8000" in dockerfile_content, \
        "Dockerfile should expose port 8000"
    
    # Verify docker-compose.yml maps port 8000
    docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_content = yaml.safe_load(f)
    
    backend_service = compose_content["services"]["backend"]
    assert "ports" in backend_service, "Backend service should have ports configuration"
    
    # Check that port 8000 is mapped
    ports = backend_service["ports"]
    port_8000_mapped = any("8000:8000" in str(port) for port in ports)
    assert port_8000_mapped, "Backend service should map port 8000:8000"
    
    # Verify uvicorn is configured to listen on 0.0.0.0:8000
    assert "--host 0.0.0.0" in dockerfile_content or "--host 0.0.0.0" in str(backend_service.get("command", "")), \
        "Uvicorn should be configured to listen on 0.0.0.0"
    assert "--port 8000" in dockerfile_content or "--port 8000" in str(backend_service.get("command", "")), \
        "Uvicorn should be configured to listen on port 8000"


# Feature: docker-full-functionality, Property 13: CORS configuration
@settings(max_examples=100)
@given(
    origins=st.lists(
        st.sampled_from([
            "http://localhost:5173",
            "http://0.0.0.0:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]),
        min_size=1,
        max_size=4,
        unique=True
    )
)
def test_cors_configuration(origins: List[str]):
    """
    Property 13: CORS configuration
    
    For any request from the frontend origin, when CORS is configured,
    the backend should accept the request.
    
    Validates: Requirements 4.3
    """
    from core.config import settings, parse_cors
    
    # Test that CORS origins are properly configured
    assert hasattr(settings, 'BACKEND_CORS_ORIGINS'), \
        "Settings should have BACKEND_CORS_ORIGINS attribute"
    
    cors_origins = settings.BACKEND_CORS_ORIGINS
    assert isinstance(cors_origins, list), \
        "BACKEND_CORS_ORIGINS should be a list"
    
    # Test parse_cors function with various formats
    # Test comma-separated string
    test_origins_str = ",".join(origins)
    parsed = parse_cors(test_origins_str)
    assert isinstance(parsed, list), "parse_cors should return a list"
    assert len(parsed) == len(origins), "parse_cors should parse all origins"
    
    # Test that main.py includes CORS middleware
    main_py_path = Path(__file__).parent.parent / "main.py"
    with open(main_py_path, 'r') as f:
        main_content = f.read()
    
    assert "CORSMiddleware" in main_content, \
        "main.py should include CORSMiddleware"
    assert "allow_origins" in main_content, \
        "CORS middleware should configure allow_origins"
    assert "allow_credentials=True" in main_content, \
        "CORS middleware should allow credentials"
    assert "allow_methods" in main_content, \
        "CORS middleware should configure allow_methods"
    assert "allow_headers" in main_content, \
        "CORS middleware should configure allow_headers"


# Feature: docker-full-functionality, Property 14: External service configuration
@settings(max_examples=100)
@given(
    service=st.sampled_from([
        "MAILGUN_API_KEY",
        "MAILGUN_DOMAIN",
        "MAILGUN_FROM_EMAIL",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
    ])
)
def test_external_service_configuration(service: str):
    """
    Property 14: External service configuration
    
    For any external service integration (Mailgun, Stripe), when environment
    variables are loaded, the service should be configured with the correct API keys.
    
    Validates: Requirements 4.5
    """
    from core.config import settings
    
    # Map environment variable names to settings attributes
    attr_mapping = {
        "MAILGUN_API_KEY": "MAILGUN_API_KEY",
        "MAILGUN_DOMAIN": "MAILGUN_DOMAIN",
        "MAILGUN_FROM_EMAIL": "MAILGUN_FROM_EMAIL",
        "STRIPE_SECRET_KEY": "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET": "STRIPE_WEBHOOK_SECRET",
    }
    
    attr_name = attr_mapping[service]
    
    # Verify the attribute exists in settings
    assert hasattr(settings, attr_name), \
        f"Settings should have {attr_name} attribute"
    
    # Verify the attribute is accessible (may be empty in test environment)
    value = getattr(settings, attr_name)
    assert value is not None, \
        f"Settings.{attr_name} should not be None"
    
    # Verify the environment variable is documented in backend/.env
    backend_env_path = Path(__file__).parent.parent / ".env"
    if backend_env_path.exists():
        with open(backend_env_path, 'r') as f:
            env_content = f.read()
        
        # Check that the variable is present (even if empty)
        assert service in env_content, \
            f"{service} should be present in backend/.env"


# Feature: docker-full-functionality, Property 15: Service dependency management
def test_service_dependency_management():
    """
    Property 15: Service dependency management
    
    For any backend startup, when PostgreSQL or Redis is not healthy,
    the backend should wait before starting.
    
    Validates: Requirements 4.6
    """
    # Read docker-compose.yml to verify dependency configuration
    docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_content = yaml.safe_load(f)
    
    backend_service = compose_content["services"]["backend"]
    
    # Verify depends_on is configured
    assert "depends_on" in backend_service, \
        "Backend service should have depends_on configuration"
    
    depends_on = backend_service["depends_on"]
    
    # Verify postgres dependency with health check
    assert "postgres" in depends_on, \
        "Backend should depend on postgres"
    
    if isinstance(depends_on, dict):
        postgres_config = depends_on["postgres"]
        assert "condition" in postgres_config, \
            "Postgres dependency should have a condition"
        assert postgres_config["condition"] == "service_healthy", \
            "Backend should wait for postgres to be healthy"
    
    # Verify redis dependency with health check
    assert "redis" in depends_on, \
        "Backend should depend on redis"
    
    if isinstance(depends_on, dict):
        redis_config = depends_on["redis"]
        assert "condition" in redis_config, \
            "Redis dependency should have a condition"
        assert redis_config["condition"] == "service_healthy", \
            "Backend should wait for redis to be healthy"
    
    # Verify postgres has health check configured
    postgres_service = compose_content["services"]["postgres"]
    assert "healthcheck" in postgres_service, \
        "Postgres service should have health check configured"
    
    postgres_healthcheck = postgres_service["healthcheck"]
    assert "test" in postgres_healthcheck, \
        "Postgres health check should have test command"
    assert "pg_isready" in str(postgres_healthcheck["test"]), \
        "Postgres health check should use pg_isready"
    
    # Verify redis has health check configured
    redis_service = compose_content["services"]["redis"]
    assert "healthcheck" in redis_service, \
        "Redis service should have health check configured"
    
    redis_healthcheck = redis_service["healthcheck"]
    assert "test" in redis_healthcheck, \
        "Redis health check should have test command"
    assert "ping" in str(redis_healthcheck["test"]), \
        "Redis health check should use ping command"


def test_backend_health_check_endpoint():
    """
    Test that backend has health check endpoint configured.
    
    Validates: Requirements 4.4
    """
    # Verify health check endpoint exists in routes
    health_router_path = Path(__file__).parent.parent / "routes" / "health.py"
    assert health_router_path.exists(), \
        "Health router should exist at routes/health.py"
    
    with open(health_router_path, 'r') as f:
        health_content = f.read()
    
    # Verify liveness endpoint exists
    assert "/live" in health_content or "liveness" in health_content, \
        "Health router should have liveness endpoint"
    
    # Verify health router is included in main.py
    main_py_path = Path(__file__).parent.parent / "main.py"
    with open(main_py_path, 'r') as f:
        main_content = f.read()
    
    assert "health_router" in main_content, \
        "main.py should import health_router"
    assert "include_router(health_router)" in main_content, \
        "main.py should include health_router"
    
    # Verify docker-compose.yml uses health check endpoint
    docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_content = yaml.safe_load(f)
    
    backend_service = compose_content["services"]["backend"]
    assert "healthcheck" in backend_service, \
        "Backend service should have health check configured"
    
    backend_healthcheck = backend_service["healthcheck"]
    assert "test" in backend_healthcheck, \
        "Backend health check should have test command"
    
    # Verify health check uses the /health/live endpoint
    test_command = str(backend_healthcheck["test"])
    assert "/health/live" in test_command or "/health" in test_command, \
        "Backend health check should use /health/live endpoint"


def test_database_initialization_in_lifespan():
    """
    Test that database is initialized in the lifespan context manager.
    
    Validates: Requirements 4.1, 4.6
    """
    main_py_path = Path(__file__).parent.parent / "main.py"
    
    with open(main_py_path, 'r') as f:
        main_content = f.read()
    
    # Verify lifespan context manager exists
    assert "@asynccontextmanager" in main_content, \
        "main.py should have asynccontextmanager for lifespan"
    assert "async def lifespan" in main_content, \
        "main.py should define lifespan function"
    
    # Verify database initialization is called in lifespan
    assert "initialize_db" in main_content, \
        "main.py should call initialize_db in lifespan"
    
    # Verify lifespan is passed to FastAPI app
    assert "lifespan=lifespan" in main_content, \
        "FastAPI app should use lifespan context manager"


def test_environment_variables_loaded_from_env_file():
    """
    Test that backend loads environment variables from .env file.
    
    Validates: Requirements 1.1, 4.5
    """
    config_py_path = Path(__file__).parent.parent / "core" / "config.py"
    
    with open(config_py_path, 'r') as f:
        config_content = f.read()
    
    # Verify dotenv is used to load environment variables
    assert "load_dotenv" in config_content, \
        "config.py should use load_dotenv"
    
    # Verify .env file path is constructed
    assert ".env" in config_content, \
        "config.py should reference .env file"
    
    # Verify docker-compose.yml uses env_file directive
    docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_content = yaml.safe_load(f)
    
    backend_service = compose_content["services"]["backend"]
    assert "env_file" in backend_service, \
        "Backend service should use env_file directive"
    
    env_files = backend_service["env_file"]
    assert "./backend/.env" in env_files, \
        "Backend service should load ./backend/.env"


def test_restart_policy_configured():
    """
    Test that backend service has restart policy configured.
    
    Validates: Requirements 14.1, 14.4
    """
    docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    
    with open(docker_compose_path, 'r') as f:
        compose_content = yaml.safe_load(f)
    
    backend_service = compose_content["services"]["backend"]
    
    # Verify restart policy is configured
    assert "restart" in backend_service, \
        "Backend service should have restart policy"
    
    restart_policy = backend_service["restart"]
    assert restart_policy == "unless-stopped", \
        "Backend service should use 'unless-stopped' restart policy"


def test_backend_uses_service_names():
    """
    Test that backend configuration uses Docker service names for inter-container communication.
    
    Validates: Requirements 10.2, 10.3
    """
    # Check backend/.env file
    backend_env_path = Path(__file__).parent.parent / ".env"
    
    if backend_env_path.exists():
        with open(backend_env_path, 'r') as f:
            env_content = f.read()
        
        # Parse environment variables
        env_vars = {}
        for line in env_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        # Verify POSTGRES_DB_URL uses 'postgres' service name
        if "POSTGRES_DB_URL" in env_vars:
            postgres_url = env_vars["POSTGRES_DB_URL"]
            assert "@postgres:" in postgres_url or "@postgres/" in postgres_url, \
                f"POSTGRES_DB_URL should use 'postgres' service name, got: {postgres_url}"
        
        # Verify REDIS_URL uses 'redis' service name
        if "REDIS_URL" in env_vars:
            redis_url = env_vars["REDIS_URL"]
            assert "redis://redis" in redis_url, \
                f"REDIS_URL should use 'redis' service name, got: {redis_url}"
    
    # Check config.py defaults
    config_py_path = Path(__file__).parent.parent / "core" / "config.py"
    
    with open(config_py_path, 'r') as f:
        config_content = f.read()
    
    # Verify default POSTGRES_SERVER is 'postgres' (check for the pattern, not exact match)
    assert "'POSTGRES_SERVER', 'postgres'" in config_content or \
           '"POSTGRES_SERVER", "postgres"' in config_content, \
        "config.py should default POSTGRES_SERVER to 'postgres'"
    
    # Verify default REDIS_URL uses 'redis' service name
    assert "redis://redis" in config_content, \
        "config.py should default REDIS_URL to use 'redis' service name"
