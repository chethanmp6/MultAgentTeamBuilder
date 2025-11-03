"""
Team management API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from ..models.team_models import (
    TeamCreateRequest, TeamUpdateRequest, TeamResponse, 
    TeamListResponse, TeamDeleteResponse, TeamStatusResponse
)
from ..services.team_service import TeamService

router = APIRouter()

def get_team_service(request: Request) -> TeamService:
    """Dependency to get team service"""
    return TeamService(request.app.app_state)

@router.post("/", response_model=TeamResponse)
async def create_team(
    request: TeamCreateRequest,
    team_service: TeamService = Depends(get_team_service)
):
    """Create a new hierarchical team"""
    try:
        return await team_service.create_team(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")

@router.get("/", response_model=TeamListResponse)
async def list_teams(
    limit: int = 100,
    offset: int = 0,
    team_service: TeamService = Depends(get_team_service)
):
    """List all teams"""
    try:
        return await team_service.list_teams(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    team_service: TeamService = Depends(get_team_service)
):
    """Get a specific team"""
    try:
        team = await team_service.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        return team
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team: {str(e)}")

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    request: TeamUpdateRequest,
    team_service: TeamService = Depends(get_team_service)
):
    """Update a team"""
    try:
        team = await team_service.update_team(team_id, request)
        if not team:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        return team
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")

@router.delete("/{team_id}", response_model=TeamDeleteResponse)
async def delete_team(
    team_id: str,
    team_service: TeamService = Depends(get_team_service)
):
    """Delete a team"""
    try:
        result = await team_service.delete_team(team_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")

@router.get("/{team_id}/status", response_model=TeamStatusResponse)
async def get_team_status(
    team_id: str,
    team_service: TeamService = Depends(get_team_service)
):
    """Get team status"""
    try:
        status = await team_service.get_team_status(team_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team status: {str(e)}")