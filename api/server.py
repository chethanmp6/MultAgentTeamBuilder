"""
FastAPI server for Hierarchical Agent System APIs
Provides REST endpoints for hierarchical agent team management
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging
import os
from typing import Dict, Any

from .routes import teams, configs, agents, executions
from .middleware.error_handler import add_error_handlers
from .config import APIConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for team instances (in production, use a proper database)
app_state: Dict[str, Any] = {
    "teams": {},
    "executions": {},
    "config": APIConfig()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Hierarchical Agent API server...")
    
    # Initialize app state
    app.app_state = app_state
    
    yield
    
    logger.info("Shutting down Hierarchical Agent API server...")

# Create FastAPI app
app = FastAPI(
    title="Hierarchical Agent System API",
    description="REST API for managing hierarchical agent teams",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handlers
add_error_handlers(app)

# Include routers
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(configs.router, prefix="/api/v1/configs", tags=["configs"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(executions.router, prefix="/api/v1/executions", tags=["executions"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Hierarchical Agent System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "teams_count": len(app.app_state["teams"]),
        "active_executions": len(app.app_state["executions"])
    }

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    uvicorn.run(
        "api.server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )