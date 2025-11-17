# routers/websockets.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from services.websockets import ConnectionManager
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

ws_router = APIRouter()
manager = ConnectionManager()

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """General WebSocket endpoint with optional authentication"""
    connection_id = None
    try:
        # Connect with optional authentication
        connection_id = await manager.connect(websocket, token)
        logger.info(f"WebSocket connection established: {connection_id}")
        
        while True:
            data = await websocket.receive_text()
            manager.stats["total_messages_received"] += 1
            
            try:
                # Parse JSON message
                message = json.loads(data)
                message_type = message.get("type", "message")
                
                if message_type == "ping":
                    # Handle ping and update connection status
                    await manager.handle_ping(connection_id, message.get("timestamp"))
                    
                elif message_type == "subscribe":
                    # Subscribe to event types
                    event_types = message.get("events", [])
                    success = await manager.subscribe_to_events(connection_id, event_types)
                    response = {
                        "type": "subscription_response",
                        "success": success,
                        "events": event_types,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_to_connection(connection_id, json.dumps(response))
                    
                elif message_type == "unsubscribe":
                    # Unsubscribe from event types
                    event_types = message.get("events", [])
                    success = await manager.unsubscribe_from_events(connection_id, event_types)
                    response = {
                        "type": "unsubscription_response",
                        "success": success,
                        "events": event_types,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_to_connection(connection_id, json.dumps(response))
                    
                elif message_type == "cart_update":
                    # Broadcast cart updates to user's connections
                    user_id = message.get("user_id")
                    if user_id:
                        await manager.broadcast_cart_update(user_id, message.get("data", {}))
                    
                elif message_type == "order_update":
                    # Broadcast order updates to user's connections
                    user_id = message.get("user_id")
                    if user_id:
                        await manager.broadcast_order_update(user_id, message.get("data", {}))
                    
                elif message_type == "product_update":
                    # Broadcast product updates to all connections
                    await manager.broadcast_product_update(message.get("data", {}))
                    
                else:
                    # Echo back unknown message types
                    echo_response = {
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_to_connection(connection_id, json.dumps(echo_response))
                    
            except json.JSONDecodeError:
                # Handle plain text messages
                text_response = {
                    "type": "text_message",
                    "content": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_to_connection(connection_id, json.dumps(text_response))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        if connection_id:
            await manager.disconnect(connection_id, "client_disconnect")
    except Exception as e:
        logger.error(f"WebSocket error for connection {connection_id}: {e}")
        if connection_id:
            await manager.disconnect(connection_id, "error")

@ws_router.websocket("/ws/notifications/{user_id}")
async def user_notifications(websocket: WebSocket, user_id: str, token: Optional[str] = Query(None)):
    """WebSocket endpoint for user-specific notifications with authentication"""
    connection_id = None
    try:
        # Connect with user authentication
        connection_id = await manager.connect_user(websocket, user_id, token)
        logger.info(f"User WebSocket connection established: {connection_id} for user {user_id}")
        
        # Auto-subscribe to user-specific events
        user_events = ["order_updates", "cart_updates", "notifications", "user_status"]
        await manager.subscribe_to_events(connection_id, user_events)
        
        # Send subscription confirmation
        subscription_message = {
            "type": "auto_subscribed",
            "events": user_events,
            "user_id": user_id,
            "message": f"Auto-subscribed to notifications for user {user_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_to_connection(connection_id, json.dumps(subscription_message))
        
        while True:
            data = await websocket.receive_text()
            manager.stats["total_messages_received"] += 1
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "message")
                
                if message_type == "ping":
                    await manager.handle_ping(connection_id, message.get("timestamp"))
                    
                elif message_type == "subscribe":
                    # Subscribe to additional notification types
                    event_types = message.get("events", [])
                    success = await manager.subscribe_to_events(connection_id, event_types)
                    response = {
                        "type": "subscription_response",
                        "success": success,
                        "events": event_types,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_to_connection(connection_id, json.dumps(response))
                    
                elif message_type == "unsubscribe":
                    # Unsubscribe from notification types
                    event_types = message.get("events", [])
                    success = await manager.unsubscribe_from_events(connection_id, event_types)
                    response = {
                        "type": "unsubscription_response",
                        "success": success,
                        "events": event_types,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_to_connection(connection_id, json.dumps(response))
                    
                elif message_type == "get_status":
                    # Get connection status
                    connection_info = manager.get_connection_info(connection_id)
                    status_response = {
                        "type": "status_response",
                        "connection_info": connection_info,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_to_connection(connection_id, json.dumps(status_response))
                    
                else:
                    # Handle other user-specific messages
                    echo_response = {
                        "type": "user_echo",
                        "user_id": user_id,
                        "original_message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_to_connection(connection_id, json.dumps(echo_response))
                    
            except json.JSONDecodeError:
                error_response = {
                    "type": "parse_error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_to_connection(connection_id, json.dumps(error_response))
            
    except WebSocketDisconnect:
        logger.info(f"User WebSocket disconnected: {connection_id} for user {user_id}")
        if connection_id:
            await manager.disconnect_user(connection_id, user_id)
    except HTTPException as e:
        logger.warning(f"Authentication failed for user {user_id}: {e.detail}")
        # Connection will be closed by the HTTPException
    except Exception as e:
        logger.error(f"User WebSocket error for {user_id}, connection {connection_id}: {e}")
        if connection_id:
            await manager.disconnect_user(connection_id, user_id)

# Health and management endpoints
@ws_router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return manager.get_stats()

@ws_router.get("/ws/connections/{user_id}")
async def get_user_connections(user_id: str):
    """Get all connections for a specific user"""
    connections = manager.get_user_connections(user_id)
    return {
        "user_id": user_id,
        "connections": connections,
        "connection_count": len(connections)
    }

@ws_router.post("/ws/cleanup")
async def cleanup_dead_connections():
    """Manually trigger cleanup of dead connections"""
    await manager.cleanup_dead_connections()
    return {"message": "Dead connections cleanup completed"}

@ws_router.post("/ws/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast a message to all connections (admin only)"""
    # Note: In production, this should have proper admin authentication
    message_json = json.dumps({
        **message,
        "timestamp": datetime.utcnow().isoformat(),
        "type": message.get("type", "admin_broadcast")
    })
    
    sent_count = await manager.broadcast(message_json)
    return {
        "message": "Broadcast sent",
        "sent_to_connections": sent_count
    }
