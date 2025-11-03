"""
Pydantic models for agent library API requests and responses
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class AgentSearchRequest(BaseModel):
    """Request model for searching agents"""
    query: Optional[str] = Field(None, description="Search query for agent name or description")
    capabilities: Optional[List[str]] = Field(None, description="Filter by capabilities")
    role: Optional[Literal["coordinator", "supervisor", "worker", "specialist"]] = Field(None, description="Filter by role")
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class AgentCapability(BaseModel):
    """Agent capability information"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None

class AgentInfo(BaseModel):
    """Information about an agent"""
    id: str
    name: str
    description: str
    primary_role: Literal["coordinator", "supervisor", "worker", "specialist"]
    secondary_roles: List[str] = []
    capabilities: List[AgentCapability]
    tools: List[str]
    specializations: List[str] = []
    file_path: str
    compatibility_score: float = Field(ge=0.0, le=1.0)
    can_coordinate: bool = False
    can_supervise: bool = False
    team_size_limit: Optional[int] = None

class AgentListResponse(BaseModel):
    """Response model for agent listing"""
    agents: List[AgentInfo]
    total: int
    limit: int
    offset: int

class AgentResponse(BaseModel):
    """Response model for individual agent details"""
    agent: AgentInfo
    config_data: Optional[Dict[str, Any]] = None
    usage_stats: Optional[Dict[str, Any]] = None

class AgentCompatibilityRequest(BaseModel):
    """Request model for agent compatibility check"""
    agent_ids: List[str] = Field(..., min_items=2, description="List of agent IDs to check compatibility")

class AgentCompatibilityResponse(BaseModel):
    """Response model for agent compatibility"""
    compatibility_matrix: Dict[str, Dict[str, float]]
    average_compatibility: float
    recommendations: List[str] = []

class AgentStatsResponse(BaseModel):
    """Response model for agent library statistics"""
    total_agents: int
    by_role: Dict[str, int]
    by_capability: Dict[str, int]
    coordination_capable: int
    supervision_capable: int
    average_compatibility: float
    most_popular_capabilities: List[str]

class TeamSuggestionRequest(BaseModel):
    """Request model for team composition suggestions"""
    task_description: str = Field(..., description="Description of the task")
    preferred_team_size: Optional[int] = Field(None, ge=2, le=20, description="Preferred team size")
    required_capabilities: Optional[List[str]] = Field(None, description="Required capabilities")
    team_type: Literal["hierarchical", "flat", "pipeline"] = Field("hierarchical", description="Type of team structure")

class TeamSuggestion(BaseModel):
    """A suggested team composition"""
    coordinator: AgentInfo
    teams: List[Dict[str, Any]]  # Team structure with supervisors and workers
    reasoning: str
    compatibility_score: float
    estimated_performance: float

class TeamSuggestionResponse(BaseModel):
    """Response model for team suggestions"""
    suggestions: List[TeamSuggestion]
    task_analysis: Optional[Dict[str, Any]] = None