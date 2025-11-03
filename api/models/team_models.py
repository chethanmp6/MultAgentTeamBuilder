"""
Pydantic models for team-related API requests and responses
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class TeamCreateRequest(BaseModel):
    """Request model for creating a new hierarchical team"""
    name: str = Field(..., description="Name of the team")
    description: Optional[str] = Field(None, description="Description of the team")
    config_data: Optional[Dict[str, Any]] = Field(None, description="Team configuration data")
    config_file_path: Optional[str] = Field(None, description="Path to configuration file")
    template_id: Optional[str] = Field(None, description="ID of template to use")

class TeamUpdateRequest(BaseModel):
    """Request model for updating a team"""
    name: Optional[str] = Field(None, description="Updated name")
    description: Optional[str] = Field(None, description="Updated description")
    config_data: Optional[Dict[str, Any]] = Field(None, description="Updated configuration")

class WorkerInfo(BaseModel):
    """Information about a worker agent"""
    name: str
    role: str
    description: str
    capabilities: List[str]
    config_file: str
    priority: int = 1

class TeamMemberInfo(BaseModel):
    """Information about a team (supervisor + workers)"""
    name: str
    description: str
    supervisor_name: str
    workers: List[WorkerInfo]
    worker_count: int

class HierarchyInfo(BaseModel):
    """Information about team hierarchy"""
    coordinator: Dict[str, Any]
    teams: Dict[str, TeamMemberInfo]
    total_teams: int
    total_workers: int

class TeamResponse(BaseModel):
    """Response model for team information"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    status: Literal["active", "inactive", "error"] = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    hierarchy_info: Optional[HierarchyInfo] = None
    config_data: Optional[Dict[str, Any]] = None

class TeamListResponse(BaseModel):
    """Response model for listing teams"""
    teams: List[TeamResponse]
    total: int
    page: int = 1
    limit: int = 100

class TeamDeleteResponse(BaseModel):
    """Response model for team deletion"""
    message: str
    team_id: str
    deleted_at: datetime = Field(default_factory=datetime.utcnow)

class TeamStatusResponse(BaseModel):
    """Response model for team status"""
    id: str
    name: str
    status: Literal["active", "inactive", "busy", "error"]
    active_executions: int
    total_executions: int
    last_activity: Optional[datetime] = None
    hierarchy_info: Optional[HierarchyInfo] = None