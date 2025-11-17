"""
Structured logging utility for the application
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


class StructuredLogger:
    """
    Structured logger that outputs JSON formatted logs
    """
    
    def __init__(self, name: str = "banwee"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """
        Create a structured log entry
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "message": message,
            "service": "banwee-api",
        }
        
        if user_id:
            log_entry["user_id"] = user_id
            
        if endpoint:
            log_entry["endpoint"] = endpoint
            
        if metadata:
            log_entry["metadata"] = metadata
            
        if exception:
            log_entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
            }
            
        return log_entry
    
    def info(
        self,
        message: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log info message"""
        log_entry = self._create_log_entry(
            "info", message, user_id, endpoint, metadata
        )
        self.logger.info(json.dumps(log_entry))
    
    def warning(
        self,
        message: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """Log warning message"""
        log_entry = self._create_log_entry(
            "warning", message, user_id, endpoint, metadata, exception
        )
        self.logger.warning(json.dumps(log_entry))
    
    def error(
        self,
        message: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """Log error message"""
        log_entry = self._create_log_entry(
            "error", message, user_id, endpoint, metadata, exception
        )
        self.logger.error(json.dumps(log_entry))
    
    def critical(
        self,
        message: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """Log critical message"""
        log_entry = self._create_log_entry(
            "critical", message, user_id, endpoint, metadata, exception
        )
        self.logger.critical(json.dumps(log_entry))


# Create global logger instance
structured_logger = StructuredLogger()