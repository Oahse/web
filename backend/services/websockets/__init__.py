"""
WebSocket Services Package

This package provides comprehensive WebSocket functionality including:
- Connection management
- Real-time messaging
- Kafka integration
- Event broadcasting
"""

from .index import (
    ConnectionManager,
    WebSocketConnection,
    WebSocketMessage,
    MessageType,
    ConnectionStatus,
    manager
)

from .websocket_integration import (
    WebSocketIntegrationService,
    websocket_integration
)

from .websocket_kafka_consumer import (
    WebSocketKafkaConsumer,
    websocket_kafka_consumer,
    start_websocket_kafka_consumer,
    stop_websocket_kafka_consumer
)

__all__ = [
    # Core classes
    'ConnectionManager',
    'WebSocketConnection', 
    'WebSocketMessage',
    'MessageType',
    'ConnectionStatus',
    
    # Service classes
    'WebSocketIntegrationService',
    'WebSocketKafkaConsumer',
    
    # Global instances
    'manager',
    'websocket_integration',
    'websocket_kafka_consumer',
    
    # Startup/shutdown functions
    'start_websocket_kafka_consumer',
    'stop_websocket_kafka_consumer'
]