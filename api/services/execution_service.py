"""
Execution service for managing task executions on hierarchical teams
"""
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import logging

from src.hierarchical.hierarchical_agent import HierarchicalAgentTeam
from ..models.execution_models import (
    ExecutionRequest, ExecutionResponse, ExecutionStatus, 
    ExecutionMetadata, ExecutionResult, ExecutionListRequest,
    ExecutionListResponse, ExecutionCancelRequest, ExecutionCancelResponse
)

logger = logging.getLogger(__name__)

class ExecutionService:
    """Service for managing task executions"""
    
    def __init__(self, storage: Dict[str, Any]):
        """Initialize execution service"""
        self.storage = storage
        self.teams: Dict[str, HierarchicalAgentTeam] = storage.get("teams", {})
        self.executions: Dict[str, Dict[str, Any]] = storage.get("executions", {})
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_task(self, team_id: str, request: ExecutionRequest) -> ExecutionResponse:
        """Execute a task on a hierarchical team"""
        if team_id not in self.teams:
            raise ValueError(f"Team {team_id} not found")
        
        execution_id = str(uuid4())
        team = self.teams[team_id]
        
        # Create execution metadata
        metadata = ExecutionMetadata(
            execution_id=execution_id,
            team_id=team_id,
            worker_id=request.worker_id,
            input_text=request.input_text,
            parameters=request.parameters
        )
        
        # Create initial status
        status = ExecutionStatus(
            status="pending",
            progress=0
        )
        
        # Store execution info
        execution_info = {
            "id": execution_id,
            "metadata": metadata,
            "status": status,
            "result": None,
            "created_at": datetime.utcnow()
        }
        self.executions[execution_id] = execution_info
        
        # Start execution task
        task = asyncio.create_task(
            self._execute_task_async(execution_id, team, request)
        )
        self.running_tasks[execution_id] = task
        
        return ExecutionResponse(
            execution_id=execution_id,
            status=status,
            metadata=metadata
        )
    
    async def execute_worker_task(self, team_id: str, worker_id: str, request: ExecutionRequest) -> ExecutionResponse:
        """Execute a task on a specific worker"""
        if team_id not in self.teams:
            raise ValueError(f"Team {team_id} not found")
        
        team = self.teams[team_id]
        worker = team.get_worker(worker_id)
        
        if not worker:
            raise ValueError(f"Worker {worker_id} not found in team {team_id}")
        
        execution_id = str(uuid4())
        
        # Create execution metadata
        metadata = ExecutionMetadata(
            execution_id=execution_id,
            team_id=team_id,
            worker_id=worker_id,
            input_text=request.input_text,
            parameters=request.parameters
        )
        
        # Create initial status
        status = ExecutionStatus(
            status="pending",
            progress=0
        )
        
        # Store execution info
        execution_info = {
            "id": execution_id,
            "metadata": metadata,
            "status": status,
            "result": None,
            "created_at": datetime.utcnow()
        }
        self.executions[execution_id] = execution_info
        
        # Start execution task
        task = asyncio.create_task(
            self._execute_worker_task_async(execution_id, team, worker_id, request)
        )
        self.running_tasks[execution_id] = task
        
        return ExecutionResponse(
            execution_id=execution_id,
            status=status,
            metadata=metadata
        )
    
    async def get_execution(self, execution_id: str) -> Optional[ExecutionResponse]:
        """Get execution status and results"""
        if execution_id not in self.executions:
            return None
        
        execution_info = self.executions[execution_id]
        
        return ExecutionResponse(
            execution_id=execution_id,
            status=execution_info["status"],
            metadata=execution_info["metadata"],
            result=execution_info["result"]
        )
    
    async def list_executions(self, request: ExecutionListRequest) -> ExecutionListResponse:
        """List executions with filtering and pagination"""
        filtered_executions = []
        
        for execution_info in self.executions.values():
            # Apply filters
            if request.team_id and execution_info["metadata"].team_id != request.team_id:
                continue
            
            if request.status and execution_info["status"].status != request.status:
                continue
            
            filtered_executions.append(execution_info)
        
        # Sort executions
        if request.order_by == "created_at":
            filtered_executions.sort(
                key=lambda x: x["created_at"],
                reverse=(request.order_direction == "desc")
            )
        elif request.order_by == "completed_at":
            filtered_executions.sort(
                key=lambda x: x["status"].completed_at or datetime.min,
                reverse=(request.order_direction == "desc")
            )
        elif request.order_by == "status":
            filtered_executions.sort(
                key=lambda x: x["status"].status,
                reverse=(request.order_direction == "desc")
            )
        
        # Apply pagination
        total = len(filtered_executions)
        paginated = filtered_executions[request.offset:request.offset + request.limit]
        
        # Convert to response format
        execution_responses = []
        for execution_info in paginated:
            execution_responses.append(ExecutionResponse(
                execution_id=execution_info["id"],
                status=execution_info["status"],
                metadata=execution_info["metadata"],
                result=execution_info["result"]
            ))
        
        return ExecutionListResponse(
            executions=execution_responses,
            total=total,
            limit=request.limit,
            offset=request.offset
        )
    
    async def cancel_execution(self, execution_id: str, request: ExecutionCancelRequest) -> Optional[ExecutionCancelResponse]:
        """Cancel a running execution"""
        if execution_id not in self.executions:
            return None
        
        execution_info = self.executions[execution_id]
        
        # Cancel the running task if it exists
        if execution_id in self.running_tasks:
            task = self.running_tasks[execution_id]
            if not task.done():
                task.cancel()
            del self.running_tasks[execution_id]
        
        # Update status
        execution_info["status"].status = "failed"
        execution_info["status"].completed_at = datetime.utcnow()
        execution_info["status"].error_message = f"Cancelled: {request.reason or 'User requested cancellation'}"
        
        return ExecutionCancelResponse(
            execution_id=execution_id,
            message="Execution cancelled successfully"
        )
    
    async def _execute_task_async(self, execution_id: str, team: HierarchicalAgentTeam, request: ExecutionRequest):
        """Execute task asynchronously"""
        execution_info = self.executions[execution_id]
        
        try:
            # Update status to running
            execution_info["status"].status = "running"
            execution_info["status"].started_at = datetime.utcnow()
            execution_info["status"].progress = 10
            
            start_time = time.time()
            
            # Execute the task
            kwargs = request.parameters or {}
            if request.timeout_seconds:
                kwargs["timeout"] = request.timeout_seconds
            
            result = team.run(request.input_text, **kwargs)
            
            execution_time = time.time() - start_time
            
            # Create execution result
            execution_result = ExecutionResult(
                response=result.get("response", ""),
                metadata=result.get("metadata"),
                reasoning=result.get("reasoning"),
                intermediate_steps=result.get("intermediate_steps"),
                used_tools=result.get("used_tools"),
                execution_time_seconds=execution_time
            )
            
            # Update status to completed
            execution_info["status"].status = "completed"
            execution_info["status"].completed_at = datetime.utcnow()
            execution_info["status"].progress = 100
            execution_info["result"] = execution_result
            
        except asyncio.CancelledError:
            execution_info["status"].status = "failed"
            execution_info["status"].completed_at = datetime.utcnow()
            execution_info["status"].error_message = "Execution was cancelled"
            
        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}")
            execution_info["status"].status = "failed"
            execution_info["status"].completed_at = datetime.utcnow()
            execution_info["status"].error_message = str(e)
        
        finally:
            # Remove from running tasks
            if execution_id in self.running_tasks:
                del self.running_tasks[execution_id]
    
    async def _execute_worker_task_async(self, execution_id: str, team: HierarchicalAgentTeam, worker_id: str, request: ExecutionRequest):
        """Execute task on specific worker asynchronously"""
        execution_info = self.executions[execution_id]
        
        try:
            # Update status to running
            execution_info["status"].status = "running"
            execution_info["status"].started_at = datetime.utcnow()
            execution_info["status"].progress = 10
            
            start_time = time.time()
            
            # Execute on specific worker
            kwargs = request.parameters or {}
            if request.timeout_seconds:
                kwargs["timeout"] = request.timeout_seconds
            
            result = team.run_direct_worker(worker_id, request.input_text, **kwargs)
            
            execution_time = time.time() - start_time
            
            # Create execution result
            execution_result = ExecutionResult(
                response=result.get("response", ""),
                metadata=result.get("metadata"),
                reasoning=result.get("reasoning"),
                intermediate_steps=result.get("intermediate_steps"),
                used_tools=result.get("used_tools"),
                execution_time_seconds=execution_time
            )
            
            # Update status to completed
            execution_info["status"].status = "completed"
            execution_info["status"].completed_at = datetime.utcnow()
            execution_info["status"].progress = 100
            execution_info["result"] = execution_result
            
        except asyncio.CancelledError:
            execution_info["status"].status = "failed"
            execution_info["status"].completed_at = datetime.utcnow()
            execution_info["status"].error_message = "Execution was cancelled"
            
        except Exception as e:
            logger.error(f"Worker execution {execution_id} failed: {e}")
            execution_info["status"].status = "failed"
            execution_info["status"].completed_at = datetime.utcnow()
            execution_info["status"].error_message = str(e)
        
        finally:
            # Remove from running tasks
            if execution_id in self.running_tasks:
                del self.running_tasks[execution_id]