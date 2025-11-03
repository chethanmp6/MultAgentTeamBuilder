"""
Pydantic models for execution-related API requests and responses
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class ExecutionRequest(BaseModel):
    """Request model for task execution"""
    input_text: str = Field(..., description="Input text for the task")
    team_id: Optional[str] = Field(None, description="Specific team to execute with")
    worker_id: Optional[str] = Field(None, description="Specific worker to execute with")
    timeout_seconds: Optional[int] = Field(None, description="Execution timeout in seconds")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional execution parameters")

class ExecutionStatus(BaseModel):
    """Execution status information"""
    status: Literal["pending", "running", "completed", "failed", "timeout"] = "pending"
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class ExecutionMetadata(BaseModel):
    """Metadata about the execution"""
    execution_id: str
    team_id: Optional[str] = None
    worker_id: Optional[str] = None
    input_text: str
    parameters: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

class ExecutionResult(BaseModel):
    """Result of a task execution"""
    response: str = Field(..., description="The main response from the execution")
    metadata: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    intermediate_steps: Optional[List[Dict[str, Any]]] = None
    used_tools: Optional[List[str]] = None
    execution_time_seconds: Optional[float] = None

class ExecutionResponse(BaseModel):
    """Complete response model for task execution"""
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    status: ExecutionStatus
    metadata: ExecutionMetadata
    result: Optional[ExecutionResult] = None

class ExecutionListRequest(BaseModel):
    """Request model for listing executions"""
    team_id: Optional[str] = None
    status: Optional[Literal["pending", "running", "completed", "failed", "timeout"]] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "completed_at", "status"] = "created_at"
    order_direction: Literal["asc", "desc"] = "desc"

class ExecutionListResponse(BaseModel):
    """Response model for listing executions"""
    executions: List[ExecutionResponse]
    total: int
    limit: int
    offset: int

class ExecutionCancelRequest(BaseModel):
    """Request model for canceling an execution"""
    reason: Optional[str] = Field(None, description="Reason for cancellation")

class ExecutionCancelResponse(BaseModel):
    """Response model for execution cancellation"""
    execution_id: str
    message: str
    cancelled_at: datetime = Field(default_factory=datetime.utcnow)