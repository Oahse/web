"""
Security monitoring and management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db # NEW
from core.config import SecurityValidator # NEW

from core.dependencies import require_admin, get_current_user
from core.config import get_security_config, get_security_monitor, get_security_validator
from core.utils.response import Response
from core.utils.logging import structured_logger
from core.utils.correlation import get_correlation_id
from models.user import User

router = APIRouter(prefix="/api/security", tags=["security"])
security = HTTPBearer()


class SecurityEventResponse(BaseModel):
    """Response model for security events"""
    timestamp: float
    type: str
    details: Dict[str, Any]
    severity: str


class SecuritySummaryResponse(BaseModel):
    """Response model for security summary"""
    total_events: int
    threat_indicators: Dict[str, int]
    recent_events: List[SecurityEventResponse]
    security_level: str


class SecurityConfigResponse(BaseModel):
    """Response model for security configuration"""
    security_level: str
    rate_limiting_enabled: bool
    input_sanitization_enabled: bool
    max_file_size_mb: int
    password_min_length: int
    session_timeout_minutes: int


class SecurityTestRequest(BaseModel):
    """Request model for security testing"""
    test_type: str
    test_data: Optional[Dict[str, Any]] = None


@router.get("/status", response_model=SecuritySummaryResponse)
async def get_security_status(
    request: Request,
    current_user: User = Depends(require_admin)
):
    """
    Get current security status and threat indicators
    Requires admin privileges
    """
    correlation_id = get_correlation_id()

    try:
        monitor = get_security_monitor()
        summary = monitor.get_security_summary()

        # Convert events to response format
        recent_events = [
            SecurityEventResponse(
                timestamp=event['timestamp'],
                type=event['type'],
                details=event['details'],
                severity=event['severity']
            )
            for event in summary['recent_events']
        ]

        response_data = SecuritySummaryResponse(
            total_events=summary['total_events'],
            threat_indicators=summary['threat_indicators'],
            recent_events=recent_events,
            security_level=summary['security_level']
        )

        structured_logger.info(
            message="Security status accessed",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url)
        )

        return Response(
            success=True,
            data=response_data,
            message="Security status retrieved successfully"
        )

    except Exception as e:
        structured_logger.error(
            message="Error retrieving security status",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving security status"
        )


@router.get("/config", response_model=SecurityConfigResponse)
async def get_security_config_info(
    request: Request,
    current_user: User = Depends(require_admin)
):
    """
    Get current security configuration (non-sensitive parts)
    Requires admin privileges
    """
    correlation_id = get_correlation_id()

    try:
        config = get_security_config()

        response_data = SecurityConfigResponse(
            security_level=config.security_level.value,
            rate_limiting_enabled=config.enable_rate_limiting,
            input_sanitization_enabled=config.enable_input_sanitization,
            max_file_size_mb=config.max_file_size_mb,
            password_min_length=config.password_min_length,
            session_timeout_minutes=config.session_timeout_minutes
        )

        structured_logger.info(
            message="Security configuration accessed",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url)
        )

        return Response(
            success=True,
            data=response_data,
            message="Security configuration retrieved successfully"
        )

    except Exception as e:
        structured_logger.error(
            message="Error retrieving security configuration",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving security configuration"
        )


@router.post("/test", response_model=None)
async def test_security_feature(
    request: Request,
    # test_request: SecurityTestRequest,
    # current_user: User = Depends(require_admin),
    # db: AsyncSession = Depends(get_db), # NEW: Add db dependency
    # validator: SecurityValidator = Depends(get_security_validator) # NEW: Use async dependency
):
    """
    Test security features (for development and testing)
    Requires admin privileges
    """
    correlation_id = get_correlation_id()

    try:
        # validator is now injected
        monitor = get_security_monitor()

        test_results = {}

        if test_request.test_type == "input_validation":
            # Test input validation
            test_data = test_request.test_data or {}
            test_input = test_data.get("input", "test input")

            from core.utils.sanitization import InputSanitizer
            sanitizer = InputSanitizer()

            validation_result = sanitizer.validate_input_security(
                test_input, "test_field")
            test_results = {
                "input": test_input,
                "is_safe": validation_result['is_safe'],
                "security_issues": validation_result['security_issues'],
                "warnings": validation_result['warnings'],
                "sanitized_value": validation_result['sanitized_value']
            }

        elif test_request.test_type == "password_strength":
            # Test password strength validation
            test_password = test_request.test_data.get(
                "password", "testpassword") if test_request.test_data else "testpassword"

            password_result = validator.validate_password_strength(
                test_password)
            test_results = {
                "password": "***hidden***",  # Don't return actual password
                "is_valid": password_result['is_valid'],
                "errors": password_result['errors'],
                "warnings": password_result['warnings'],
                "strength_score": password_result['strength_score']
            }

        elif test_request.test_type == "file_upload":
            # Test file upload validation
            test_data = test_request.test_data or {}
            filename = test_data.get("filename", "test.txt")
            file_size = test_data.get("file_size", 1024)

            file_result = await validator.validate_file_upload(filename, file_size) # NEW: Await the call
            test_results = {
                "filename": filename,
                "file_size": file_size,
                "is_valid": file_result['is_valid'],
                "errors": file_result['errors'],
                "warnings": file_result['warnings']
            }

        elif test_request.test_type == "security_event":
            # Test security event recording
            event_type = test_request.test_data.get(
                "event_type", "test_event") if test_request.test_data else "test_event"
            event_details = test_request.test_data.get(
                "details", {"test": True}) if test_request.test_data else {"test": True}

            monitor.record_security_event(event_type, event_details)
            test_results = {
                "event_recorded": True,
                "event_type": event_type,
                "details": event_details
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown test type: {test_request.test_type}"
            )

        structured_logger.info(
            message=f"Security test performed: {test_request.test_type}",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            metadata={"test_type": test_request.test_type}
        )

        return Response(
            success=True,
            data=test_results,
            message=f"Security test '{test_request.test_type}' completed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        structured_logger.error(
            message=f"Error performing security test: {test_request.test_type}",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing security test"
        )


@router.post("/events/{event_type}")
async def record_security_event(
    request: Request,
    event_type: str,
    event_details: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Record a security event
    Can be used by the application to report security incidents
    """
    correlation_id = get_correlation_id()

    try:
        monitor = get_security_monitor()

        # Add user context to event details
        enhanced_details = {
            **event_details,
            "user_id": str(current_user.id),
            "user_role": current_user.role.value,
            "endpoint": str(request.url),
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        monitor.record_security_event(event_type, enhanced_details)

        structured_logger.warning(
            message=f"Security event recorded: {event_type}",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            metadata={"event_type": event_type, "details": enhanced_details}
        )

        return Response(
            success=True,
            data={"event_type": event_type, "recorded": True},
            message="Security event recorded successfully"
        )

    except Exception as e:
        structured_logger.error(
            message=f"Error recording security event: {event_type}",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording security event"
        )


@router.get("/events")
async def get_security_events(
    request: Request,
    limit: int = 50,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: User = Depends(require_admin)
):
    """
    Get security events with optional filtering
    Requires admin privileges
    """
    correlation_id = get_correlation_id()

    try:
        monitor = get_security_monitor()
        summary = monitor.get_security_summary()

        events = summary['recent_events']

        # Apply filters
        if event_type:
            events = [e for e in events if e['type'] == event_type]

        if severity:
            events = [e for e in events if e['severity'] == severity]

        # Limit results
        events = events[:limit]

        # Convert to response format
        response_events = [
            SecurityEventResponse(
                timestamp=event['timestamp'],
                type=event['type'],
                details=event['details'],
                severity=event['severity']
            )
            for event in events
        ]

        structured_logger.info(
            message="Security events accessed",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            metadata={"limit": limit,
                      "event_type": event_type, "severity": severity}
        )

        return Response(
            success=True,
            data={
                "events": response_events,
                "total_events": len(response_events),
                "filters_applied": {
                    "event_type": event_type,
                    "severity": severity,
                    "limit": limit
                }
            },
            message="Security events retrieved successfully"
        )

    except Exception as e:
        structured_logger.error(
            message="Error retrieving security events",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving security events"
        )


@router.delete("/events")
async def clear_security_events(
    request: Request,
    confirm: bool = False,
    current_user: User = Depends(require_admin)
):
    """
    Clear security events (use with caution)
    Requires admin privileges and explicit confirmation
    """
    correlation_id = get_correlation_id()

    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must set confirm=true to clear security events"
        )

    try:
        monitor = get_security_monitor()

        # Clear events (in a real implementation, you might want to archive them)
        monitor.security_events.clear()
        monitor.threat_indicators = {
            'sql_injection_attempts': 0,
            'xss_attempts': 0,
            'brute_force_attempts': 0,
            'suspicious_file_uploads': 0,
            'rate_limit_violations': 0
        }

        structured_logger.warning(
            message="Security events cleared",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            metadata={"confirmed": confirm}
        )

        return Response(
            success=True,
            data={"events_cleared": True},
            message="Security events cleared successfully"
        )

    except Exception as e:
        structured_logger.error(
            message="Error clearing security events",
            correlation_id=correlation_id,
            user_id=str(current_user.id),
            endpoint=str(request.url),
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing security events"
        )
