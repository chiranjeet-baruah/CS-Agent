from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our models and services
from models import *
from database import db_manager, get_database
from ai_service import get_ai_coordinator, get_knowledge_service
from websocket_manager import get_connection_manager, get_websocket_handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        await db_manager.connect()
        await initialize_default_agents()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await db_manager.disconnect()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

app = FastAPI(
    title="Multi-Agent Customer Service AI Platform",
    description="Enterprise-grade customer service automation platform with AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_default_agents():
    """Initialize default AI agents if they don't exist"""
    try:
        existing_agents = await db_manager.get_agents()
        if len(existing_agents) == 0:
            # Create default agents
            agents_data = [
                {
                    "name": "General Support Agent",
                    "description": "Handles general customer inquiries and support requests",
                    "specialization": ["general", "faq", "information"],
                    "system_prompt": "You are a helpful customer service agent specializing in general inquiries. Provide clear, concise, and friendly responses. Always aim to resolve customer issues efficiently.",
                    "capabilities": [
                        {"name": "FAQ", "description": "Frequently asked questions", "confidence_score": 0.9},
                        {"name": "Basic Troubleshooting", "description": "Simple problem resolution", "confidence_score": 0.85},
                        {"name": "Information Retrieval", "description": "Finding and providing information", "confidence_score": 0.9}
                    ]
                },
                {
                    "name": "Technical Support Agent",
                    "description": "Specialized in technical issues and advanced troubleshooting",
                    "specialization": ["technical", "troubleshooting", "integration"],
                    "system_prompt": "You are a technical support specialist with deep knowledge of system troubleshooting, API integrations, and technical problem-solving. Provide detailed technical guidance while keeping explanations accessible.",
                    "capabilities": [
                        {"name": "Technical Diagnostics", "description": "System analysis and diagnostics", "confidence_score": 0.95},
                        {"name": "Advanced Troubleshooting", "description": "Complex problem resolution", "confidence_score": 0.9},
                        {"name": "System Integration", "description": "API and system integration support", "confidence_score": 0.85}
                    ]
                },
                {
                    "name": "Billing Support Agent",
                    "description": "Handles billing inquiries, payments, and subscription management",
                    "specialization": ["billing", "payments", "subscriptions"],
                    "system_prompt": "You are a billing support specialist who helps customers with payment issues, subscription management, and billing inquiries. Be empathetic and solution-focused when dealing with financial concerns.",
                    "capabilities": [
                        {"name": "Payment Processing", "description": "Payment-related assistance", "confidence_score": 0.9},
                        {"name": "Subscription Management", "description": "Subscription handling", "confidence_score": 0.95},
                        {"name": "Invoice Queries", "description": "Invoice and billing questions", "confidence_score": 0.9}
                    ]
                }
            ]
            
            for agent_data in agents_data:
                agent = Agent(
                    **agent_data,
                    configuration=AgentConfiguration(
                        system_prompt=agent_data["system_prompt"],
                        model_provider="openai",
                        model_name="gpt-4o-mini"
                    ),
                    capabilities=[AgentCapability(**cap) for cap in agent_data["capabilities"]]
                )
                await db_manager.create_agent(agent)
            
            logger.info("Default agents created successfully")
    except Exception as e:
        logger.error(f"Error initializing default agents: {e}")

# Basic endpoints
@app.get("/")
async def root():
    return {"message": "Multi-Agent Customer Service AI Platform API", "status": "active", "timestamp": datetime.utcnow()}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "cs-agent-api"
    }

# Dashboard endpoints
@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: DatabaseManager = Depends(get_database)):
    """Get dashboard statistics"""
    return await db.get_dashboard_stats()

# Agent management endpoints
@app.get("/api/agents", response_model=List[Agent])
async def get_agents(status: Optional[AgentStatus] = None, db: DatabaseManager = Depends(get_database)):
    """Get list of AI agents"""
    return await db.get_agents(status=status)

@app.get("/api/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, db: DatabaseManager = Depends(get_database)):
    """Get specific agent by ID"""
    agent = await db.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.post("/api/agents", response_model=Dict[str, str])
async def create_agent(agent: Agent, db: DatabaseManager = Depends(get_database)):
    """Create a new agent"""
    agent_id = await db.create_agent(agent)
    return {"agent_id": agent_id, "message": "Agent created successfully"}

# Conversation management endpoints
@app.post("/api/conversations", response_model=Dict[str, str])
async def create_conversation(
    request: CreateConversationRequest,
    db: DatabaseManager = Depends(get_database)
):
    """Create a new conversation"""
    try:
        # Get or create customer
        customer = await db.get_or_create_customer(
            email=request.customer_email,
            name=request.customer_name
        )
        
        # Create initial message
        initial_message = Message(
            conversation_id="",  # Will be set after conversation creation
            sender_id=customer.id,
            sender_type=MessageType.user,
            content=request.initial_message,
            metadata=request.metadata
        )
        
        # Create conversation
        conversation = Conversation(
            customer_id=customer.id,
            channel=request.channel,
            priority=request.priority,
            messages=[initial_message],
            subject=request.initial_message[:100] + "..." if len(request.initial_message) > 100 else request.initial_message
        )
        
        conversation_id = await db.create_conversation(conversation)
        
        # Update message with conversation ID
        initial_message.conversation_id = conversation_id
        
        return {
            "conversation_id": conversation_id,
            "customer_id": customer.id,
            "message": "Conversation created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")

@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str, db: DatabaseManager = Depends(get_database)):
    """Get conversation by ID"""
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.get("/api/conversations", response_model=ConversationListResponse)
async def get_conversations(
    status: Optional[ConversationStatus] = None,
    agent_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: DatabaseManager = Depends(get_database)
):
    """Get conversations with filtering and pagination"""
    try:
        if customer_id:
            conversations = await db.get_conversations_by_customer(customer_id)
        else:
            conversations = await db.get_active_conversations(agent_id=agent_id)
        
        # Simple filtering (in production, this would be done in database query)
        if status:
            conversations = [c for c in conversations if c.status == status]
        
        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_conversations = conversations[start_idx:end_idx]
        
        return ConversationListResponse(
            conversations=paginated_conversations,
            total=len(conversations),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")

@app.post("/api/conversations/{conversation_id}/messages", response_model=AgentResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    db: DatabaseManager = Depends(get_database)
):
    """Send a message in a conversation and get AI response"""
    try:
        # Get conversation
        conversation = await db.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get customer info for context
        customer = await db.get_customer_by_email("customer@example.com")  # This would be from auth
        customer_context = {
            "tier": customer.tier if customer else "free",
            "conversation_count": len(conversation.messages),
            "channel": conversation.channel.value
        }
        
        # Create user message
        user_message = Message(
            conversation_id=conversation_id,
            sender_id=conversation.customer_id,
            sender_type=MessageType.user,
            content=request.content,
            attachments=request.attachments,
            metadata=request.metadata
        )
        
        # Analyze sentiment and intent
        ai_coordinator = await get_ai_coordinator(db)
        sentiment, sentiment_confidence = await ai_coordinator.analyze_sentiment(request.content)
        intent, intent_confidence = await ai_coordinator.detect_intent(request.content)
        
        user_message.sentiment = sentiment
        user_message.intent = intent
        user_message.confidence_score = intent_confidence
        
        # Add message to conversation
        await db.add_message_to_conversation(conversation_id, user_message)
        
        # Generate AI response
        agent_response = await ai_coordinator.generate_response(
            conversation_id, request.content, customer_context
        )
        
        # Create agent message
        agent_message = Message(
            conversation_id=conversation_id,
            sender_id=agent_response.agent_id,
            sender_type=MessageType.agent,
            content=agent_response.message,
            is_ai_generated=True,
            processing_time_ms=agent_response.processing_time_ms,
            confidence_score=agent_response.confidence
        )
        
        # Add agent response to conversation
        await db.add_message_to_conversation(conversation_id, agent_message)
        
        # Send real-time updates via WebSocket
        connection_manager = get_connection_manager()
        
        # Broadcast user message
        await connection_manager.send_message_to_conversation(
            conversation_id, conversation.customer_id, MessageType.user, request.content
        )
        
        # Broadcast agent response
        await connection_manager.send_message_to_conversation(
            conversation_id, agent_response.agent_id, MessageType.agent, agent_response.message
        )
        
        # Handle escalation if needed
        if agent_response.requires_human_escalation:
            await connection_manager.send_escalation_notice(conversation_id, agent_response.escalation_reason)
            await db.update_conversation_status(conversation_id, ConversationStatus.escalated)
        
        return agent_response
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    user_type: str = Query(..., description="user type: 'agent' or 'customer'"),
    user_id: str = Query(..., description="user ID")
):
    """WebSocket endpoint for real-time conversation updates"""
    connection_manager = get_connection_manager()
    websocket_handler = get_websocket_handler()
    
    try:
        await connection_manager.connect_to_conversation(websocket, conversation_id, user_type, user_id)
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle the message
                await websocket_handler.handle_message(
                    websocket, message_data, conversation_id, user_id, user_type
                )
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "An error occurred processing your message"
                }))
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        connection_manager.disconnect_from_conversation(websocket, conversation_id, user_id)

# Analytics endpoints
@app.get("/api/analytics/agents/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    days: int = Query(7, ge=1, le=90),
    db: DatabaseManager = Depends(get_database)
):
    """Get agent performance analytics"""
    ai_coordinator = await get_ai_coordinator(db)
    return await ai_coordinator.get_agent_performance_summary(agent_id, days)

@app.get("/api/analytics/conversations/summary")
async def get_conversation_analytics(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD format"),
    db: DatabaseManager = Depends(get_database)
):
    """Get conversation analytics summary"""
    # Placeholder - would implement real analytics
    return {
        "total_conversations": 150,
        "avg_resolution_time_minutes": 12.5,
        "customer_satisfaction_avg": 4.3,
        "escalation_rate": 8.2,
        "top_intents": [
            {"intent": "billing_inquiry", "count": 45},
            {"intent": "technical_support", "count": 38},
            {"intent": "general_inquiry", "count": 67}
        ]
    }

# Knowledge base endpoints
@app.get("/api/knowledge-base/search")
async def search_knowledge_base(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    db: DatabaseManager = Depends(get_database)
):
    """Search knowledge base articles"""
    knowledge_service = await get_knowledge_service(db)
    articles = await knowledge_service.search_relevant_articles(query, limit=limit)
    return {"articles": articles, "total": len(articles)}

@app.post("/api/knowledge-base/articles")
async def create_knowledge_article(
    article: KnowledgeArticle,
    db: DatabaseManager = Depends(get_database)
):
    """Create a new knowledge base article"""
    article_id = await db.create_knowledge_article(article)
    return {"article_id": article_id, "message": "Article created successfully"}

# System management endpoints
@app.post("/api/system/maintenance")
async def toggle_maintenance_mode(enabled: bool):
    """Toggle system maintenance mode"""
    # Implementation would update system-wide maintenance flag
    return {"maintenance_mode": enabled, "message": f"Maintenance mode {'enabled' if enabled else 'disabled'}"}

@app.get("/api/system/metrics")
async def get_system_metrics():
    """Get system-wide metrics"""
    return {
        "uptime_seconds": 86400,  # 24 hours
        "memory_usage_mb": 512,
        "cpu_usage_percent": 25.5,
        "active_connections": len(get_connection_manager().active_connections),
        "database_connections": 5,
        "response_time_p95_ms": 180
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)