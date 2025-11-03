"""
Execution management API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from ..models.execution_models import (
    ExecutionRequest, ExecutionResponse, ExecutionListRequest,
    ExecutionListResponse, ExecutionCancelRequest, ExecutionCancelResponse
)
from ..services.execution_service import ExecutionService

router = APIRouter()

def get_execution_service(request: Request) -> ExecutionService:
    """Dependency to get execution service"""
    return ExecutionService(request.app.app_state)

@router.post("/{team_id}/execute", response_model=ExecutionResponse)
async def execute_task(
    team_id: str,
    request: ExecutionRequest,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """Execute a task on a hierarchical team"""
    try:
        return await execution_service.execute_task(team_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute task: {str(e)}")

@router.post("/{team_id}/workers/{worker_id}/execute", response_model=ExecutionResponse)
async def execute_worker_task(
    team_id: str,
    worker_id: str,
    request: ExecutionRequest,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """Execute a task on a specific worker"""
    try:
        return await execution_service.execute_worker_task(team_id, worker_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute worker task: {str(e)}")

@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """Get execution status and results"""
    try:
        execution = await execution_service.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution: {str(e)}")

@router.post("/", response_model=ExecutionListResponse)
async def list_executions(
    request: ExecutionListRequest,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """List executions with filtering and pagination"""
    try:
        return await execution_service.list_executions(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")

@router.get("/", response_model=ExecutionListResponse)
async def list_executions_query(
    team_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    order_by: str = "created_at",
    order_direction: str = "desc",
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """List executions using query parameters"""
    try:
        # Convert query parameters to request model
        list_request = ExecutionListRequest(
            team_id=team_id,
            status=status,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_direction=order_direction
        )
        return await execution_service.list_executions(list_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")

@router.post("/{execution_id}/cancel", response_model=ExecutionCancelResponse)
async def cancel_execution(
    execution_id: str,
    request: ExecutionCancelRequest,
    execution_service: ExecutionService = Depends(get_execution_service)
):
    """Cancel a running execution"""
    try:
        result = await execution_service.cancel_execution(execution_id, request)
        if not result:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")