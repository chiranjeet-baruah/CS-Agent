import json
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from models import WebSocketMessage, TypingIndicator, MessageType
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        # Store active connections by conversation_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store agent connections for status updates
        self.agent_connections: Dict[str, WebSocket] = {}
        # Store customer connections
        self.customer_connections: Dict[str, WebSocket] = {}
        # Track typing indicators
        self.typing_indicators: Dict[str, Set[str]] = {}  # conversation_id -> set of agent_ids typing
    
    async def connect_to_conversation(self, websocket: WebSocket, conversation_id: str, user_type: str, user_id: str):
        """Connect a WebSocket to a conversation"""
        try:
            await websocket.accept()
            
            # Add to conversation connections
            if conversation_id not in self.active_connections:
                self.active_connections[conversation_id] = []
            self.active_connections[conversation_id].append(websocket)
            
            # Store user-specific connections
            if user_type == "agent":
                self.agent_connections[user_id] = websocket
            elif user_type == "customer":
                self.customer_connections[user_id] = websocket
            
            logger.info(f"{user_type} {user_id} connected to conversation {conversation_id}")
            
            # Send connection confirmation
            await self._send_to_websocket(websocket, {
                "type": "connection_confirmed",
                "conversation_id": conversation_id,
                "user_type": user_type,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error connecting to conversation {conversation_id}: {e}")
    
    def disconnect_from_conversation(self, websocket: WebSocket, conversation_id: str, user_id: str):
        """Disconnect a WebSocket from a conversation"""
        try:
            # Remove from conversation connections
            if conversation_id in self.active_connections:
                if websocket in self.active_connections[conversation_id]:
                    self.active_connections[conversation_id].remove(websocket)
                
                # Clean up empty conversation
                if not self.active_connections[conversation_id]:
                    del self.active_connections[conversation_id]
            
            # Remove from user-specific connections
            if user_id in self.agent_connections and self.agent_connections[user_id] == websocket:
                del self.agent_connections[user_id]
            
            if user_id in self.customer_connections and self.customer_connections[user_id] == websocket:
                del self.customer_connections[user_id]
            
            # Clear typing indicators
            if conversation_id in self.typing_indicators:
                self.typing_indicators[conversation_id].discard(user_id)
                if not self.typing_indicators[conversation_id]:
                    del self.typing_indicators[conversation_id]
            
            logger.info(f"User {user_id} disconnected from conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from conversation {conversation_id}: {e}")
    
    async def broadcast_to_conversation(self, conversation_id: str, message: Dict, exclude_websocket: Optional[WebSocket] = None):
        """Broadcast message to all connections in a conversation"""
        if conversation_id not in self.active_connections:
            return
        
        message_data = {
            **message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all connected clients in this conversation
        disconnected_websockets = []
        for websocket in self.active_connections[conversation_id]:
            if websocket != exclude_websocket:
                try:
                    await self._send_to_websocket(websocket, message_data)
                except Exception as e:
                    logger.error(f"Error sending message to websocket: {e}")
                    disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected_websockets:
            self.active_connections[conversation_id].remove(ws)
    
    async def send_message_to_conversation(self, conversation_id: str, sender_id: str, sender_type: MessageType, content: str, metadata: Optional[Dict] = None):
        """Send a new message to all participants in a conversation"""
        message = WebSocketMessage(
            type="new_message",
            conversation_id=conversation_id,
            data={
                "sender_id": sender_id,
                "sender_type": sender_type.value,
                "content": content,
                "metadata": metadata or {},
                "message_id": f"msg_{int(datetime.utcnow().timestamp() * 1000)}"
            }
        )
        
        await self.broadcast_to_conversation(conversation_id, message.model_dump())
    
    async def send_typing_indicator(self, conversation_id: str, agent_id: str, is_typing: bool):
        """Send typing indicator to conversation participants"""
        if conversation_id not in self.typing_indicators:
            self.typing_indicators[conversation_id] = set()
        
        if is_typing:
            self.typing_indicators[conversation_id].add(agent_id)
        else:
            self.typing_indicators[conversation_id].discard(agent_id)
        
        typing_message = {
            "type": "typing_indicator",
            "conversation_id": conversation_id,
            "data": {
                "agent_id": agent_id,
                "is_typing": is_typing,
                "typing_agents": list(self.typing_indicators[conversation_id])
            }
        }
        
        await self.broadcast_to_conversation(conversation_id, typing_message)
    
    async def send_status_update(self, conversation_id: str, status: str, message: str):
        """Send status update to conversation participants"""
        status_message = {
            "type": "status_update",
            "conversation_id": conversation_id,
            "data": {
                "status": status,
                "message": message
            }
        }
        
        await self.broadcast_to_conversation(conversation_id, status_message)
    
    async def send_agent_assignment(self, conversation_id: str, agent_id: str, agent_name: str):
        """Notify conversation participants about agent assignment"""
        assignment_message = {
            "type": "agent_assigned",
            "conversation_id": conversation_id,
            "data": {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "message": f"{agent_name} has joined the conversation"
            }
        }
        
        await self.broadcast_to_conversation(conversation_id, assignment_message)
    
    async def send_escalation_notice(self, conversation_id: str, reason: str):
        """Send escalation notice to conversation participants"""
        escalation_message = {
            "type": "escalation",
            "conversation_id": conversation_id,
            "data": {
                "reason": reason,
                "message": "This conversation has been escalated to a human agent"
            }
        }
        
        await self.broadcast_to_conversation(conversation_id, escalation_message)
    
    async def send_to_agent(self, agent_id: str, message: Dict):
        """Send message directly to a specific agent"""
        if agent_id in self.agent_connections:
            try:
                await self._send_to_websocket(self.agent_connections[agent_id], message)
            except Exception as e:
                logger.error(f"Error sending message to agent {agent_id}: {e}")
                # Remove disconnected agent
                del self.agent_connections[agent_id]
    
    async def broadcast_to_all_agents(self, message: Dict):
        """Broadcast message to all connected agents"""
        disconnected_agents = []
        for agent_id, websocket in self.agent_connections.items():
            try:
                await self._send_to_websocket(websocket, message)
            except Exception as e:
                logger.error(f"Error broadcasting to agent {agent_id}: {e}")
                disconnected_agents.append(agent_id)
        
        # Clean up disconnected agents
        for agent_id in disconnected_agents:
            del self.agent_connections[agent_id]
    
    async def get_conversation_participants(self, conversation_id: str) -> int:
        """Get number of participants in a conversation"""
        return len(self.active_connections.get(conversation_id, []))
    
    async def _send_to_websocket(self, websocket: WebSocket, message: Dict):
        """Send message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            raise

class WebSocketHandler:
    """Handles WebSocket message processing"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def handle_message(self, websocket: WebSocket, message_data: Dict, conversation_id: str, user_id: str, user_type: str):
        """Handle incoming WebSocket message"""
        try:
            message_type = message_data.get("type")
            
            if message_type == "typing_start":
                await self.connection_manager.send_typing_indicator(conversation_id, user_id, True)
            
            elif message_type == "typing_stop":
                await self.connection_manager.send_typing_indicator(conversation_id, user_id, False)
            
            elif message_type == "message":
                # This would integrate with the main message processing system
                content = message_data.get("content", "")
                await self.connection_manager.send_message_to_conversation(
                    conversation_id, user_id, MessageType(user_type), content
                )
            
            elif message_type == "status_request":
                # Send current conversation status
                await self._send_conversation_status(websocket, conversation_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def _send_conversation_status(self, websocket: WebSocket, conversation_id: str):
        """Send current conversation status to client"""
        try:
            participants = await self.connection_manager.get_conversation_participants(conversation_id)
            typing_agents = list(self.connection_manager.typing_indicators.get(conversation_id, set()))
            
            status_message = {
                "type": "conversation_status",
                "conversation_id": conversation_id,
                "data": {
                    "participants": participants,
                    "typing_agents": typing_agents,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await self.connection_manager._send_to_websocket(websocket, status_message)
        
        except Exception as e:
            logger.error(f"Error sending conversation status: {e}")

# Global connection manager instance
connection_manager = ConnectionManager()
websocket_handler = WebSocketHandler(connection_manager)

def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return connection_manager

def get_websocket_handler() -> WebSocketHandler:
    """Get the global WebSocket handler instance"""
    return websocket_handler