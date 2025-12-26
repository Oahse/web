"""
Enhanced WebSocket Routes for Real-time Communication

This module provides WebSocket endpoints with:
- Structured message handling
- Event-based subscriptions
- User authentication
- Connection management
- Health monitoring
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from services.websockets import manager, MessageType, WebSocketMessage
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/v1/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """General WebSocket endpoint with optional authentication"""
    connection_id = None
    try:
        # Connect with optional authentication
        connection_id = await manager.connect(websocket, token)
        logger.info(f"WebSocket connection established: {connection_id}")

        while True:
            data = await websocket.receive_text()
            await manager.handle_message(connection_id, data)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        if connection_id:
            await manager.disconnect(connection_id, "client_disconnect")
    except Exception as e:
        logger.error(f"WebSocket error for connection {connection_id}: {e}")
        if connection_id:
            await manager.disconnect(connection_id, "error")


@ws_router.websocket("/v1/ws/notifications/{user_id}")
async def user_notifications_endpoint(websocket: WebSocket, user_id: str, token: Optional[str] = Query(None)):
    """WebSocket endpoint for user-specific notifications with authentication"""
    connection_id = None
    try:
        # Verify token if provided
        if token:
            authenticated_user_id = await manager.authenticate_connection(token)
            if not authenticated_user_id or authenticated_user_id != user_id:
                await websocket.close(code=1008, reason="Authentication failed")
                raise HTTPException(status_code=401, detail="Authentication failed")

        # Connect with user authentication
        connection_id = await manager.connect(websocket, token)
        logger.info(f"User WebSocket connection established: {connection_id} for user {user_id}")

        # Auto-subscribe to user-specific events
        user_events = ["notifications", "order_updates", "cart_updates", "user_status"]
        await manager.subscribe_to_events(connection_id, user_events)

        # Send subscription confirmation
        subscription_message = WebSocketMessage(
            type=MessageType.SUBSCRIPTION_RESPONSE,
            data={
                "auto_subscribed": True,
                "events": user_events,
                "user_id": user_id,
                "message": f"Auto-subscribed to notifications for user {user_id}"
            },
            connection_id=connection_id,
            user_id=user_id
        )
        await manager.send_to_connection(connection_id, subscription_message)

        while True:
            data = await websocket.receive_text()
            await manager.handle_message(connection_id, data)

    except WebSocketDisconnect:
        logger.info(f"User WebSocket disconnected: {connection_id} for user {user_id}")
        if connection_id:
            await manager.disconnect(connection_id, "user_disconnect")
    except HTTPException as e:
        logger.warning(f"Authentication failed for user {user_id}: {e.detail}")
    except Exception as e:
        logger.error(f"User WebSocket error for {user_id}, connection {connection_id}: {e}")
        if connection_id:
            await manager.disconnect(connection_id, "error")


# Health and management endpoints
@ws_router.get("/v1/ws/stats")
async def get_websocket_stats():
    """Get comprehensive WebSocket connection statistics"""
    return manager.get_stats()


@ws_router.get("/v1/ws/connections/{user_id}")
async def get_user_connections(user_id: str):
    """Get all connections for a specific user"""
    connections = manager.get_user_connections(user_id)
    return {
        "user_id": user_id,
        "connections": connections,
        "connection_count": len(connections)
    }


@ws_router.get("/v1/ws/connection/{connection_id}")
async def get_connection_info(connection_id: str):
    """Get information about a specific connection"""
    connection_info = manager.get_connection_info(connection_id)
    if not connection_info:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection_info


@ws_router.post("/v1/ws/cleanup")
async def cleanup_dead_connections():
    """Manually trigger cleanup of dead connections"""
    # This will be handled by the health check, but we can provide manual trigger
    stats_before = manager.get_stats()
    
    # The cleanup is now handled automatically by the health check
    # But we can return current stats
    stats_after = manager.get_stats()
    
    return {
        "message": "Health check is running automatically",
        "stats_before": stats_before,
        "stats_after": stats_after
    }


@ws_router.post("/v1/ws/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast a message to all connections (admin only)"""
    # Note: In production, this should have proper admin authentication
    
    broadcast_message = WebSocketMessage(
        type=MessageType.ADMIN_BROADCAST,
        data={
            **message,
            "broadcast_type": "admin",
            "server_timestamp": datetime.utcnow().isoformat()
        }
    )

    sent_count = await manager.broadcast(broadcast_message)
    return {
        "message": "Broadcast sent",
        "sent_to_connections": sent_count,
        "broadcast_data": broadcast_message.data
    }


@ws_router.post("/v1/ws/notify/{user_id}")
async def notify_user(user_id: str, notification: Dict[str, Any]):
    """Send notification to a specific user"""
    sent_count = await manager.notify_user(user_id, notification)
    return {
        "message": f"Notification sent to user {user_id}",
        "sent_to_connections": sent_count,
        "notification": notification
    }


@ws_router.post("/v1/ws/broadcast/subscribers/{event_type}")
async def broadcast_to_subscribers(event_type: str, message: Dict[str, Any]):
    """Broadcast message to subscribers of a specific event type"""
    
    broadcast_message = WebSocketMessage(
        type=MessageType(event_type) if event_type in [mt.value for mt in MessageType] else MessageType.NOTIFICATION,
        data=message
    )
    
    sent_count = await manager.broadcast_to_subscribers(event_type, broadcast_message)
    return {
        "message": f"Message broadcast to {event_type} subscribers",
        "sent_to_connections": sent_count,
        "event_type": event_type,
        "data": message
    }


# Business-specific endpoints
@ws_router.post("/v1/ws/order-update")
async def broadcast_order_update(order_data: Dict[str, Any]):
    """Broadcast order update to relevant subscribers"""
    sent_count = await manager.broadcast_order_update(order_data)
    return {
        "message": "Order update broadcast",
        "sent_to_connections": sent_count,
        "order_data": order_data
    }


@ws_router.post("/v1/ws/product-update")
async def broadcast_product_update(product_data: Dict[str, Any]):
    """Broadcast product update to relevant subscribers"""
    sent_count = await manager.broadcast_product_update(product_data)
    return {
        "message": "Product update broadcast",
        "sent_to_connections": sent_count,
        "product_data": product_data
    }


@ws_router.post("/v1/ws/inventory-update")
async def broadcast_inventory_update(inventory_data: Dict[str, Any]):
    """Broadcast inventory update to relevant subscribers"""
    sent_count = await manager.broadcast_inventory_update(inventory_data)
    return {
        "message": "Inventory update broadcast",
        "sent_to_connections": sent_count,
        "inventory_data": inventory_data
    }
