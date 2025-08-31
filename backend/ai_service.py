import os
import time
import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models import *
from database import DatabaseManager
import json

logger = logging.getLogger(__name__)

class MultiAgentCoordinator:
    """Coordinates multiple AI agents for customer service conversations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.emergent_llm_key = os.getenv("EMERGENT_LLM_KEY")
        self.active_chats: Dict[str, LlmChat] = {}
        
    async def initialize_agent_chat(self, agent: Agent, session_id: str) -> LlmChat:
        """Initialize AI chat for a specific agent"""
        try:
            chat = LlmChat(
                api_key=self.emergent_llm_key,
                session_id=session_id,
                system_message=agent.configuration.system_prompt
            )
            
            # Configure model based on agent configuration
            chat.with_model(
                agent.configuration.model_provider,
                agent.configuration.model_name
            )
            
            # Store the chat instance
            chat_key = f"{agent.id}_{session_id}"
            self.active_chats[chat_key] = chat
            
            return chat
            
        except Exception as e:
            logger.error(f"Error initializing agent chat: {e}")
            raise

    async def get_best_agent_for_conversation(self, conversation: Conversation, message_content: str) -> Optional[Agent]:
        """Use AI to determine the best agent for a conversation"""
        try:
            # Get all active agents
            agents = await self.db_manager.get_agents(status=AgentStatus.active)
            
            if not agents:
                return None
            
            # Simple load balancing for now - choose agent with lowest load
            # In production, this would use AI to analyze message intent and route appropriately
            available_agents = [a for a in agents if a.current_load < a.max_concurrent_conversations]
            
            if not available_agents:
                return None
                
            # Sort by current load and specialization match
            best_agent = min(available_agents, key=lambda a: a.current_load)
            
            return best_agent
            
        except Exception as e:
            logger.error(f"Error selecting best agent: {e}")
            return agents[0] if agents else None

    async def generate_response(self, conversation_id: str, message_content: str, customer_context: Optional[Dict] = None) -> AgentResponse:
        """Generate AI response for a customer message"""
        start_time = time.time()
        
        try:
            # Get conversation and assigned agent
            conversation = await self.db_manager.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            agent = None
            if conversation.assigned_agent_id:
                agent = await self.db_manager.get_agent(conversation.assigned_agent_id)
            
            # If no agent assigned, find the best one
            if not agent:
                agent = await self.get_best_agent_for_conversation(conversation, message_content)
                if agent:
                    await self.db_manager.assign_agent_to_conversation(conversation_id, agent.id)
                    await self.db_manager.update_agent_load(agent.id, 1)
            
            if not agent:
                raise ValueError("No available agents")
            
            # Get or create chat session
            chat_key = f"{agent.id}_{conversation.session_id}"
            chat = self.active_chats.get(chat_key)
            
            if not chat:
                chat = await self.initialize_agent_chat(agent, conversation.session_id)
            
            # Build context from conversation history
            context_messages = []
            if conversation.messages:
                # Get last few messages for context
                recent_messages = conversation.messages[-10:]  # Last 10 messages
                for msg in recent_messages:
                    if msg.sender_type == MessageType.user:
                        context_messages.append(f"Customer: {msg.content}")
                    elif msg.sender_type == MessageType.agent:
                        context_messages.append(f"Agent: {msg.content}")
            
            # Add customer context if available
            context_str = ""
            if customer_context:
                context_str = f"Customer Context: {json.dumps(customer_context, indent=2)}\n\n"
            
            if context_messages:
                context_str += "Conversation History:\n" + "\n".join(context_messages) + "\n\n"
            
            # Create user message with context
            full_message = f"{context_str}Customer Message: {message_content}"
            user_message = UserMessage(text=full_message)
            
            # Generate response
            response = await chat.send_message(user_message)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Analyze response for escalation needs
            requires_escalation = await self._analyze_for_escalation(message_content, response)
            escalation_reason = "Complex issue requiring human expertise" if requires_escalation else None
            
            # Generate suggestions (placeholder - would use AI to generate)
            suggestions = await self._generate_suggestions(message_content, response)
            
            return AgentResponse(
                message=response,
                confidence=0.85,  # Placeholder - would calculate based on model confidence
                processing_time_ms=processing_time_ms,
                agent_id=agent.id,
                suggestions=suggestions,
                requires_human_escalation=requires_escalation,
                escalation_reason=escalation_reason
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Fallback response
            return AgentResponse(
                message="I apologize, but I'm experiencing technical difficulties. Please hold on while I connect you with a human agent.",
                confidence=0.1,
                processing_time_ms=processing_time_ms,
                agent_id="system",
                requires_human_escalation=True,
                escalation_reason="Technical error in AI system"
            )

    async def _analyze_for_escalation(self, user_message: str, ai_response: str) -> bool:
        """Analyze if conversation needs human escalation"""
        # Simple keyword-based escalation detection
        escalation_keywords = [
            "refund", "cancel", "billing error", "complaint", "legal",
            "supervisor", "manager", "escalate", "frustrated", "angry"
        ]
        
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in escalation_keywords)

    async def _generate_suggestions(self, user_message: str, ai_response: str) -> List[str]:
        """Generate follow-up suggestions"""
        # Placeholder suggestions - would use AI to generate contextual suggestions
        suggestions = [
            "Is there anything else I can help you with?",
            "Would you like me to provide additional information?",
            "Do you need help with anything related to this topic?"
        ]
        return suggestions[:2]  # Return top 2 suggestions

    async def analyze_sentiment(self, message_content: str) -> Tuple[SentimentScore, float]:
        """Analyze sentiment of a message"""
        try:
            # Simple sentiment analysis - in production, would use dedicated sentiment analysis
            positive_words = ["happy", "great", "excellent", "thank", "good", "satisfied", "pleased"]
            negative_words = ["angry", "frustrated", "terrible", "awful", "bad", "disappointed", "upset"]
            
            message_lower = message_content.lower()
            positive_count = sum(1 for word in positive_words if word in message_lower)
            negative_count = sum(1 for word in negative_words if word in message_lower)
            
            if positive_count > negative_count:
                return SentimentScore.positive, 0.7
            elif negative_count > positive_count:
                return SentimentScore.negative, 0.7
            else:
                return SentimentScore.neutral, 0.6
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return SentimentScore.neutral, 0.5

    async def detect_intent(self, message_content: str) -> Tuple[str, float]:
        """Detect intent of a message"""
        try:
            # Simple intent detection - in production, would use NLU models
            intents = {
                "technical_support": ["error", "bug", "not working", "broken", "issue", "problem"],
                "billing_inquiry": ["bill", "charge", "payment", "invoice", "subscription", "refund"],
                "general_inquiry": ["how", "what", "when", "where", "info", "information"],
                "complaint": ["complain", "disappointed", "terrible", "awful", "bad experience"],
                "praise": ["great", "excellent", "amazing", "love", "fantastic", "wonderful"]
            }
            
            message_lower = message_content.lower()
            intent_scores = {}
            
            for intent, keywords in intents.items():
                score = sum(1 for keyword in keywords if keyword in message_lower)
                if score > 0:
                    intent_scores[intent] = score
            
            if intent_scores:
                best_intent = max(intent_scores, key=intent_scores.get)
                confidence = min(intent_scores[best_intent] * 0.3, 1.0)
                return best_intent, confidence
            else:
                return "general_inquiry", 0.5
                
        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            return "general_inquiry", 0.3

    async def cleanup_chat_session(self, agent_id: str, session_id: str):
        """Cleanup chat session when conversation ends"""
        chat_key = f"{agent_id}_{session_id}"
        if chat_key in self.active_chats:
            del self.active_chats[chat_key]

    async def get_agent_performance_summary(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """Get performance summary for an agent"""
        # Placeholder - would calculate real metrics from database
        return {
            "conversations_handled": 45,
            "average_response_time_ms": 180,
            "customer_satisfaction_avg": 4.3,
            "resolution_rate": 87.5,
            "escalation_rate": 12.5
        }

class KnowledgeBaseService:
    """Service for managing and querying knowledge base"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def search_relevant_articles(self, query: str, conversation_context: Optional[str] = None) -> List[KnowledgeArticle]:
        """Search for relevant knowledge base articles"""
        return await self.db_manager.search_knowledge_base(query, limit=5)
    
    async def create_article_from_conversation(self, conversation: Conversation) -> Optional[str]:
        """Auto-generate knowledge base article from resolved conversation"""
        if conversation.status != ConversationStatus.resolved or not conversation.summary:
            return None
        
        # Create article from conversation summary
        article = KnowledgeArticle(
            title=f"Solution: {conversation.subject or 'Customer Inquiry'}",
            content=conversation.summary.resolution or "",
            category="auto_generated",
            tags=conversation.tags,
            confidence_threshold=0.7
        )
        
        return await self.db_manager.create_knowledge_article(article)

# Global AI service instance
ai_coordinator = None

async def get_ai_coordinator(db_manager: DatabaseManager) -> MultiAgentCoordinator:
    """Get AI coordinator instance"""
    global ai_coordinator
    if not ai_coordinator:
        ai_coordinator = MultiAgentCoordinator(db_manager)
    return ai_coordinator

async def get_knowledge_service(db_manager: DatabaseManager) -> KnowledgeBaseService:
    """Get knowledge base service instance"""
    return KnowledgeBaseService(db_manager)