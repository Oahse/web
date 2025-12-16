# Service Restart Resilience Implementation

This document describes the implementation of service restart resilience for the Banwee Docker deployment.

## Overview

All Docker services are now configured with automatic restart policies to ensure high availability and resilience against service failures.

## Restart Policies Configured

All services in `docker-compose.yml` now have the `restart: unless-stopped` policy:

- **postgres**: PostgreSQL database service
- **redis**: Redis cache and message broker
- **backend**: FastAPI backend application
- **celery_worker**: General Celery worker for emails, notifications, orders
- **negotiation_celery_worker**: Dedicated Celery worker for negotiation tasks
- **celery_beat**: Celery Beat scheduler for periodic tasks
- **frontend**: React/Vite frontend application

## Restart Policy Behavior

The `unless-stopped` policy means:
- Services automatically restart if they crash or exit unexpectedly
- Services do NOT restart if they are manually stopped with `docker stop`
- Services restart when the Docker daemon starts (after system reboot)
- Services maintain their restart behavior across Docker daemon restarts

## Dependency Management

Services are configured with proper dependency chains:

### Backend Service
- Depends on: `postgres` (with health check), `redis` (with health check)
- Will wait for both dependencies to be healthy before starting
- Will restart automatically if dependencies recover after failure

### Celery Workers
- **General Worker**: Depends on `postgres` and `redis` (with health checks)
- **Negotiation Worker**: Depends on `redis` (with health check)
- **Celery Beat**: Depends on `postgres` and `redis` (with health checks)

### Frontend Service
- Depends on: `backend`
- Will start after backend is available

## Health Checks

All core services have health checks configured:

- **PostgreSQL**: `pg_isready -U banwee` (every 10s, 5 retries)
- **Redis**: `redis-cli ping` (every 10s, 5 retries)
- **Backend**: HTTP check on `/health/live` (every 30s, 3 retries)
- **Frontend**: HTTP check on port 5173 (every 30s, 3 retries)

## Testing

Property-based tests are implemented in `backend/tests/test_service_restart_resilience_properties.py`:

### Property 37: Automatic Service Restart
- Verifies all services have `unless-stopped` restart policy
- Tests that services automatically restart after being stopped
- Validates restart behavior for all application services

### Property 38: Dependency Recovery Waiting
- Tests that dependent services wait for dependencies to recover
- Verifies proper dependency chain behavior
- Ensures system stability during dependency failures

## Usage

To test the restart resilience:

1. Start all services: `docker compose up -d`
2. Stop a service: `docker stop banwee_backend`
3. Observe automatic restart: `docker ps` (service should reappear)
4. Check logs: `docker logs banwee_backend`

## Failure Scenarios Handled

1. **Service Crash**: Service automatically restarts
2. **Dependency Failure**: Dependent services wait for recovery
3. **System Reboot**: All services restart automatically
4. **Docker Daemon Restart**: Services maintain restart behavior
5. **Network Issues**: Services retry connections after restart

## Monitoring

Monitor service health and restart events:

```bash
# Check service status
docker ps

# Check restart count
docker stats

# View service logs
docker logs <service_name>

# Monitor restart events
docker events --filter container=banwee_backend
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **14.1**: Services automatically restart using "unless-stopped" policy
- **14.2**: Dependent services wait for PostgreSQL recovery
- **14.3**: Dependent services wait for Redis recovery  
- **14.4**: Backend restarts automatically without manual intervention
- **14.5**: Celery workers restart automatically without manual intervention