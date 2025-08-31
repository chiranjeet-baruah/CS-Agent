import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta
from models import *

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/cs_agent_db")
            self.client = AsyncIOMotorClient(mongo_url)
            
            # Extract database name from URL or use default
            db_name = mongo_url.split("/")[-1] if "/" in mongo_url else "cs_agent_db"
            self.database = self.client[db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {mongo_url}")
            
            # Create indexes for performance
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Conversations indexes
            conversations = self.database["conversations"]
            await conversations.create_index("customer_id")
            await conversations.create_index("assigned_agent_id")
            await conversations.create_index("status")
            await conversations.create_index("created_at")
            await conversations.create_index("session_id", unique=True)
            
            # Messages indexes
            messages = self.database["messages"] 
            await messages.create_index("conversation_id")
            await messages.create_index("timestamp")
            
            # Agents indexes
            agents = self.database["agents"]
            await agents.create_index("status")
            await agents.create_index("specialization")
            
            # Customers indexes
            customers = self.database["customers"]
            await customers.create_index("email", unique=True, sparse=True)
            await customers.create_index("phone", unique=True, sparse=True)
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get a collection from the database"""
        return self.database[collection_name]

    # Agent Operations
    async def create_agent(self, agent: Agent) -> str:
        """Create a new agent"""
        collection = self.get_collection("agents")
        agent_dict = agent.model_dump(by_alias=True)
        result = await collection.insert_one(agent_dict)
        return str(result.inserted_id)

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        collection = self.get_collection("agents")
        agent_data = await collection.find_one({"_id": agent_id})
        return Agent(**agent_data) if agent_data else None

    async def get_agents(self, status: Optional[AgentStatus] = None) -> List[Agent]:
        """Get all agents, optionally filtered by status"""
        collection = self.get_collection("agents")
        query = {"status": status} if status else {}
        cursor = collection.find(query)
        agents = []
        async for agent_data in cursor:
            agents.append(Agent(**agent_data))
        return agents

    async def update_agent_load(self, agent_id: str, load_change: int):
        """Update agent's current load"""
        collection = self.get_collection("agents")
        await collection.update_one(
            {"_id": agent_id},
            {"$inc": {"current_load": load_change}}
        )

    # Customer Operations
    async def create_customer(self, customer: CustomerProfile) -> str:
        """Create a new customer"""
        collection = self.get_collection("customers")
        customer_dict = customer.model_dump(by_alias=True)
        result = await collection.insert_one(customer_dict)
        return str(result.inserted_id)

    async def get_customer_by_email(self, email: str) -> Optional[CustomerProfile]:
        """Get customer by email"""
        collection = self.get_collection("customers")
        customer_data = await collection.find_one({"email": email})
        return CustomerProfile(**customer_data) if customer_data else None

    async def get_or_create_customer(self, email: Optional[str] = None, name: Optional[str] = None) -> CustomerProfile:
        """Get existing customer or create new one"""
        if email:
            customer = await self.get_customer_by_email(email)
            if customer:
                return customer
        
        # Create new customer
        new_customer = CustomerProfile(email=email, name=name)
        customer_id = await self.create_customer(new_customer)
        new_customer.id = customer_id
        return new_customer

    # Conversation Operations
    async def create_conversation(self, conversation: Conversation) -> str:
        """Create a new conversation"""
        collection = self.get_collection("conversations")
        conversation_dict = conversation.model_dump(by_alias=True)
        result = await collection.insert_one(conversation_dict)
        return str(result.inserted_id)

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        collection = self.get_collection("conversations")
        conv_data = await collection.find_one({"_id": conversation_id})
        return Conversation(**conv_data) if conv_data else None

    async def add_message_to_conversation(self, conversation_id: str, message: Message):
        """Add message to conversation"""
        collection = self.get_collection("conversations")
        await collection.update_one(
            {"_id": conversation_id},
            {
                "$push": {"messages": message.model_dump()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    async def update_conversation_status(self, conversation_id: str, status: ConversationStatus):
        """Update conversation status"""
        collection = self.get_collection("conversations")
        await collection.update_one(
            {"_id": conversation_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )

    async def assign_agent_to_conversation(self, conversation_id: str, agent_id: str):
        """Assign agent to conversation"""
        collection = self.get_collection("conversations")
        await collection.update_one(
            {"_id": conversation_id},
            {
                "$set": {
                    "assigned_agent_id": agent_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

    async def get_active_conversations(self, agent_id: Optional[str] = None) -> List[Conversation]:
        """Get active conversations, optionally for specific agent"""
        collection = self.get_collection("conversations")
        query = {"status": {"$in": ["active", "pending"]}}
        if agent_id:
            query["assigned_agent_id"] = agent_id
            
        cursor = collection.find(query).sort("created_at", -1)
        conversations = []
        async for conv_data in cursor:
            conversations.append(Conversation(**conv_data))
        return conversations

    async def get_conversations_by_customer(self, customer_id: str) -> List[Conversation]:
        """Get all conversations for a customer"""
        collection = self.get_collection("conversations")
        cursor = collection.find({"customer_id": customer_id}).sort("created_at", -1)
        conversations = []
        async for conv_data in cursor:
            conversations.append(Conversation(**conv_data))
        return conversations

    # Analytics Operations
    async def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics"""
        conversations_col = self.get_collection("conversations")
        agents_col = self.get_collection("agents")
        
        # Get today's date
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Active conversations
        active_conversations = await conversations_col.count_documents({
            "status": {"$in": ["active", "pending"]}
        })
        
        # Active agents
        active_agents = await agents_col.count_documents({"status": "active"})
        
        # Conversations today
        conversations_today = await conversations_col.count_documents({
            "created_at": {"$gte": today}
        })
        
        # Calculate average response time and other metrics
        # This is a simplified version - in production, you'd want more sophisticated aggregation
        avg_response_time = 150.0  # placeholder
        customer_satisfaction = 4.2  # placeholder
        escalation_rate = 5.5  # placeholder
        resolution_rate = 89.3  # placeholder
        
        return DashboardStats(
            active_conversations=active_conversations,
            active_agents=active_agents,
            avg_response_time_ms=avg_response_time,
            customer_satisfaction=customer_satisfaction,
            conversations_today=conversations_today,
            messages_today=conversations_today * 3,  # estimate
            escalation_rate=escalation_rate,
            resolution_rate=resolution_rate
        )

    async def save_agent_metrics(self, metrics: AgentMetrics):
        """Save agent performance metrics"""
        collection = self.get_collection("agent_metrics")
        metrics_dict = metrics.model_dump()
        await collection.replace_one(
            {"agent_id": metrics.agent_id, "date": metrics.date},
            metrics_dict,
            upsert=True
        )

    async def save_system_metrics(self, metrics: SystemMetrics):
        """Save system performance metrics"""
        collection = self.get_collection("system_metrics")
        metrics_dict = metrics.model_dump()
        await collection.replace_one(
            {"date": metrics.date},
            metrics_dict,
            upsert=True
        )

    # Knowledge Base Operations
    async def create_knowledge_article(self, article: KnowledgeArticle) -> str:
        """Create a knowledge base article"""
        collection = self.get_collection("knowledge_base")
        article_dict = article.model_dump(by_alias=True)
        result = await collection.insert_one(article_dict)
        return str(result.inserted_id)

    async def search_knowledge_base(self, query: str, limit: int = 5) -> List[KnowledgeArticle]:
        """Search knowledge base articles"""
        collection = self.get_collection("knowledge_base")
        # Simple text search - in production, you'd use MongoDB text search or vector search
        cursor = collection.find({
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query]}}
            ],
            "is_active": True
        }).limit(limit)
        
        articles = []
        async for article_data in cursor:
            articles.append(KnowledgeArticle(**article_data))
        return articles

# Global database instance
db_manager = DatabaseManager()

async def get_database() -> DatabaseManager:
    """Dependency to get database instance"""
    return db_manager