from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import uuid

# Enum definitions
class AgentStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    busy = "busy"
    maintenance = "maintenance"

class ConversationStatus(str, Enum):
    active = "active"
    resolved = "resolved"
    escalated = "escalated"
    pending = "pending"
    closed = "closed"

class MessageType(str, Enum):
    user = "user"
    agent = "agent"
    system = "system"
    internal = "internal"

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class Channel(str, Enum):
    web_chat = "web_chat"
    email = "email"
    phone = "phone"
    sms = "sms"
    whatsapp = "whatsapp"
    api = "api"

class SentimentScore(str, Enum):
    very_negative = "very_negative"
    negative = "negative"
    neutral = "neutral"
    positive = "positive"
    very_positive = "very_positive"

# Base models
class BaseDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Agent Models
class AgentCapability(BaseModel):
    name: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)

class AgentConfiguration(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    model_provider: Literal["openai", "anthropic", "gemini"] = "openai"
    model_name: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    system_prompt: str
    context_window: int = Field(default=4000)
    response_timeout: int = Field(default=30)  # seconds

class Agent(BaseDocument):
    name: str
    description: str
    status: AgentStatus = AgentStatus.active
    capabilities: List[AgentCapability]
    specialization: List[str]  # Tags like "technical", "billing", "general"
    configuration: AgentConfiguration
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    is_primary: bool = False  # Primary agent for a specialization
    max_concurrent_conversations: int = Field(default=10)
    current_load: int = Field(default=0)

# Customer Models
class CustomerProfile(BaseDocument):
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    tier: str = "free"  # free, pro, enterprise
    preferences: Dict[str, Any] = Field(default_factory=dict)
    conversation_history_summary: Optional[str] = None
    satisfaction_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    total_conversations: int = Field(default=0)
    
# Message Models
class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str  # customer_id or agent_id
    sender_type: MessageType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attachments: List[str] = Field(default_factory=list)  # File URLs
    sentiment: Optional[SentimentScore] = None
    intent: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_ai_generated: bool = False
    processing_time_ms: Optional[int] = None

# Conversation Models
class ConversationSummary(BaseModel):
    key_points: List[str]
    resolution: Optional[str] = None
    next_steps: List[str] = Field(default_factory=list)
    sentiment_analysis: Optional[str] = None

class AgentHandoff(BaseModel):
    from_agent_id: str
    to_agent_id: str
    reason: str
    context: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Conversation(BaseDocument):
    customer_id: str
    assigned_agent_id: Optional[str] = None
    status: ConversationStatus = ConversationStatus.active
    priority: Priority = Priority.medium
    channel: Channel
    subject: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    summary: Optional[ConversationSummary] = None
    satisfaction_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    resolution_time_minutes: Optional[int] = None
    first_response_time_seconds: Optional[int] = None
    handoffs: List[AgentHandoff] = Field(default_factory=list)
    escalated_to_human: bool = False
    escalation_reason: Optional[str] = None
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

# Analytics Models
class AgentMetrics(BaseModel):
    agent_id: str
    date: str  # YYYY-MM-DD format
    conversations_handled: int = 0
    average_response_time_ms: float = 0.0
    customer_satisfaction_avg: float = 0.0
    resolution_rate: float = 0.0  # Percentage
    escalation_rate: float = 0.0  # Percentage
    messages_sent: int = 0
    active_time_minutes: int = 0

class SystemMetrics(BaseModel):
    date: str
    total_conversations: int = 0
    total_messages: int = 0
    average_response_time_ms: float = 0.0
    system_uptime_percentage: float = 0.0
    peak_concurrent_conversations: int = 0
    customer_satisfaction_avg: float = 0.0
    api_calls_made: int = 0
    costs_incurred: float = 0.0

# Knowledge Base Models
class KnowledgeArticle(BaseDocument):
    title: str
    content: str
    category: str
    tags: List[str] = Field(default_factory=list)
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    usage_count: int = Field(default=0)
    effectiveness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_active: bool = True
    last_updated_by: Optional[str] = None

# Integration Models
class IntegrationConfig(BaseDocument):
    name: str
    type: str  # crm, email, sms, etc.
    configuration: Dict[str, Any]
    is_active: bool = True
    last_sync: Optional[datetime] = None
    error_count: int = Field(default=0)

# Request/Response Models for API
class CreateConversationRequest(BaseModel):
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    channel: Channel
    initial_message: str
    priority: Priority = Priority.medium
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    attachments: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    message: str
    confidence: float
    processing_time_ms: int
    agent_id: str
    suggestions: List[str] = Field(default_factory=list)
    requires_human_escalation: bool = False
    escalation_reason: Optional[str] = None

class ConversationListResponse(BaseModel):
    conversations: List[Conversation]
    total: int
    page: int
    page_size: int

class DashboardStats(BaseModel):
    active_conversations: int
    active_agents: int
    avg_response_time_ms: float
    customer_satisfaction: float
    conversations_today: int
    messages_today: int
    escalation_rate: float
    resolution_rate: float

# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str  # "message", "typing", "status_update", etc.
    conversation_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TypingIndicator(BaseModel):
    conversation_id: str
    agent_id: str
    is_typing: bool