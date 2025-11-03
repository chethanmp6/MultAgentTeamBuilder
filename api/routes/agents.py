"""
Agent library API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from ..models.agent_models import (
    AgentSearchRequest, AgentListResponse, AgentResponse,
    AgentCompatibilityRequest, AgentCompatibilityResponse,
    AgentStatsResponse, TeamSuggestionRequest, TeamSuggestionResponse
)
from ..services.agent_service import AgentService

router = APIRouter()

def get_agent_service(request: Request) -> AgentService:
    """Dependency to get agent service"""
    return AgentService(request.app.app_state, request.app.app_state["config"])

@router.post("/search", response_model=AgentListResponse)
async def search_agents(
    request: AgentSearchRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Search agents based on criteria"""
    try:
        return await agent_service.search_agents(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search agents: {str(e)}")

@router.get("/", response_model=AgentListResponse)
async def list_agents(
    query: Optional[str] = None,
    role: Optional[str] = None,
    capabilities: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    agent_service: AgentService = Depends(get_agent_service)
):
    """List agents with optional filtering"""
    try:
        # Convert query parameters to search request
        search_request = AgentSearchRequest(
            query=query,
            capabilities=capabilities.split(",") if capabilities else None,
            role=role,
            limit=limit,
            offset=offset
        )
        return await agent_service.search_agents(search_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@router.get("/stats", response_model=AgentStatsResponse)
async def get_agent_stats(
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get statistics about the agent library"""
    try:
        return await agent_service.get_agent_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/debug", response_model=dict)
async def debug_agent_loading(
    agent_service: AgentService = Depends(get_agent_service)
):
    """Debug endpoint to check agent loading status"""
    try:
        debug_info = {
            "enhanced_library_initialized": agent_service.enhanced_library is not None,
            "template_generator_initialized": agent_service.template_generator is not None,
            "total_agents": 0,
            "agents_by_role": {},
            "sample_agents": [],
            "configs_directory": "configs/examples"
        }
        
        if agent_service.enhanced_library:
            all_agents = agent_service.enhanced_library.get_all_agents()
            debug_info["total_agents"] = len(all_agents)
            
            # Count agents by role
            role_counts = {}
            for agent_id, metadata in all_agents.items():
                role = metadata.primary_role.value
                role_counts[role] = role_counts.get(role, 0) + 1
                
                # Add to sample (first 5 agents)
                if len(debug_info["sample_agents"]) < 5:
                    debug_info["sample_agents"].append({
                        "id": agent_id,
                        "name": metadata.name,
                        "primary_role": role,
                        "can_supervise": metadata.can_supervise,
                        "can_coordinate": metadata.can_coordinate,
                        "file_path": metadata.file_path
                    })
            
            debug_info["agents_by_role"] = role_counts
            
            # Add specific role counts
            supervisors = agent_service.enhanced_library.get_supervisors()
            workers = agent_service.enhanced_library.get_workers()
            debug_info["supervisors_count"] = len(supervisors)
            debug_info["workers_count"] = len(workers)
            
        return debug_info
        
    except Exception as e:
        return {
            "error": str(e),
            "enhanced_library_initialized": False,
            "total_agents": 0
        }

@router.post("/compatibility", response_model=AgentCompatibilityResponse)
async def check_agent_compatibility(
    request: AgentCompatibilityRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Check compatibility between agents"""
    try:
        return await agent_service.get_agent_compatibility(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check compatibility: {str(e)}")

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get detailed information about a specific agent"""
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")

@router.post("/team-suggestions", response_model=TeamSuggestionResponse)
async def get_team_suggestions(
    request: TeamSuggestionRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get team composition suggestions for a task"""
    try:
        return await agent_service.get_team_suggestions(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team suggestions: {str(e)}")