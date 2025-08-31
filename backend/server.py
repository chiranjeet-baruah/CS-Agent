from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
import uvicorn

app = FastAPI(
    title="Multi-Agent Customer Service AI Platform",
    description="Enterprise-grade customer service automation platform with AI agents",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Multi-Agent Customer Service AI Platform API", "status": "active", "timestamp": datetime.now()}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "cs-agent-api"
    }

@app.get("/api/agents")
async def get_agents():
    """Get list of available AI agents"""
    return {
        "agents": [
            {
                "id": "general-support",
                "name": "General Support Agent",
                "description": "Handles general customer inquiries and support requests",
                "status": "active",
                "capabilities": ["FAQ", "Basic Troubleshooting", "Information Retrieval"]
            },
            {
                "id": "technical-support",
                "name": "Technical Support Agent", 
                "description": "Specialized in technical issues and advanced troubleshooting",
                "status": "active",
                "capabilities": ["Technical Diagnostics", "Advanced Troubleshooting", "System Integration"]
            },
            {
                "id": "billing-support",
                "name": "Billing Support Agent",
                "description": "Handles billing inquiries, payments, and subscription management",
                "status": "active", 
                "capabilities": ["Payment Processing", "Subscription Management", "Invoice Queries"]
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)