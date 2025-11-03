"""
Team service for managing hierarchical agent teams
"""
import asyncio
import tempfile
import yaml
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

from src.hierarchical.hierarchical_agent import HierarchicalAgentTeam
from src.core.hierarchical_config_loader import HierarchicalConfigLoader
from ..models.team_models import (
    TeamCreateRequest, TeamUpdateRequest, TeamResponse, 
    TeamListResponse, TeamDeleteResponse, TeamStatusResponse,
    HierarchyInfo, TeamMemberInfo, WorkerInfo
)

logger = logging.getLogger(__name__)

class TeamService:
    """Service for managing hierarchical agent teams"""
    
    def __init__(self, storage: Dict[str, Any]):
        """Initialize team service with storage backend"""
        self.storage = storage
        self.teams: Dict[str, HierarchicalAgentTeam] = storage.get("teams", {})
        self.team_metadata: Dict[str, Dict[str, Any]] = storage.get("team_metadata", {})
    
    async def create_team(self, request: TeamCreateRequest) -> TeamResponse:
        """Create a new hierarchical team"""
        try:
            team_id = f"team_{len(self.teams) + 1}_{int(datetime.utcnow().timestamp())}"
            
            # Determine how to create the team
            hierarchical_team = None
            config_data = None
            
            if request.config_data:
                # Create from provided config data
                hierarchical_team, config_data = await self._create_team_from_config_data(
                    team_id, request.name, request.config_data
                )
            elif request.config_file_path:
                # Create from config file
                hierarchical_team, config_data = await self._create_team_from_file(
                    team_id, request.name, request.config_file_path
                )
            elif request.template_id:
                # Create from template
                hierarchical_team, config_data = await self._create_team_from_template(
                    team_id, request.name, request.template_id
                )
            else:
                raise ValueError("Must provide config_data, config_file_path, or template_id")
            
            # Store the team
            self.teams[team_id] = hierarchical_team
            
            # Create metadata
            metadata = {
                "id": team_id,
                "name": request.name,
                "description": request.description,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "active",
                "config_data": config_data
            }
            self.team_metadata[team_id] = metadata
            
            # Get hierarchy info
            hierarchy_info = self._get_hierarchy_info(hierarchical_team)
            
            return TeamResponse(
                id=team_id,
                name=request.name,
                description=request.description,
                status="active",
                hierarchy_info=hierarchy_info,
                config_data=config_data
            )
            
        except Exception as e:
            logger.error(f"Failed to create team: {e}")
            raise ValueError(f"Failed to create team: {str(e)}")
    
    async def get_team(self, team_id: str) -> Optional[TeamResponse]:
        """Get a team by ID"""
        if team_id not in self.teams:
            return None
        
        team = self.teams[team_id]
        metadata = self.team_metadata.get(team_id, {})
        
        hierarchy_info = self._get_hierarchy_info(team)
        
        return TeamResponse(
            id=team_id,
            name=metadata.get("name", "Unknown"),
            description=metadata.get("description"),
            status=metadata.get("status", "active"),
            created_at=metadata.get("created_at", datetime.utcnow()),
            updated_at=metadata.get("updated_at", datetime.utcnow()),
            hierarchy_info=hierarchy_info,
            config_data=metadata.get("config_data")
        )
    
    async def list_teams(self, limit: int = 100, offset: int = 0) -> TeamListResponse:
        """List all teams"""
        team_list = []
        
        # Get all teams with pagination
        team_ids = list(self.teams.keys())[offset:offset + limit]
        
        for team_id in team_ids:
            team_response = await self.get_team(team_id)
            if team_response:
                team_list.append(team_response)
        
        return TeamListResponse(
            teams=team_list,
            total=len(self.teams),
            page=(offset // limit) + 1,
            limit=limit
        )
    
    async def update_team(self, team_id: str, request: TeamUpdateRequest) -> Optional[TeamResponse]:
        """Update a team"""
        if team_id not in self.teams:
            return None
        
        metadata = self.team_metadata.get(team_id, {})
        
        # Update metadata
        if request.name:
            metadata["name"] = request.name
        if request.description:
            metadata["description"] = request.description
        if request.config_data:
            metadata["config_data"] = request.config_data
            # Note: In a full implementation, you might want to recreate the team
            # with the new configuration
        
        metadata["updated_at"] = datetime.utcnow()
        self.team_metadata[team_id] = metadata
        
        return await self.get_team(team_id)
    
    async def delete_team(self, team_id: str) -> Optional[TeamDeleteResponse]:
        """Delete a team"""
        if team_id not in self.teams:
            return None
        
        team_name = self.team_metadata.get(team_id, {}).get("name", "Unknown")
        
        # Remove from storage
        del self.teams[team_id]
        if team_id in self.team_metadata:
            del self.team_metadata[team_id]
        
        return TeamDeleteResponse(
            message=f"Team '{team_name}' deleted successfully",
            team_id=team_id
        )
    
    async def get_team_status(self, team_id: str) -> Optional[TeamStatusResponse]:
        """Get team status"""
        if team_id not in self.teams:
            return None
        
        team = self.teams[team_id]
        metadata = self.team_metadata.get(team_id, {})
        
        # Get execution info from storage
        executions = self.storage.get("executions", {})
        team_executions = [
            exec_info for exec_info in executions.values()
            if exec_info.get("team_id") == team_id
        ]
        
        active_executions = len([
            e for e in team_executions
            if e.get("status", {}).get("status") in ["pending", "running"]
        ])
        
        hierarchy_info = self._get_hierarchy_info(team)
        
        return TeamStatusResponse(
            id=team_id,
            name=metadata.get("name", "Unknown"),
            status="busy" if active_executions > 0 else "active",
            active_executions=active_executions,
            total_executions=len(team_executions),
            last_activity=metadata.get("updated_at"),
            hierarchy_info=hierarchy_info
        )
    
    async def _create_team_from_config_data(self, team_id: str, name: str, config_data: Dict[str, Any]) -> tuple[HierarchicalAgentTeam, Dict[str, Any]]:
        """Create team from configuration data"""
        # Create a temporary file with the config data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f, default_flow_style=False)
            temp_path = f.name
        
        try:
            # Load configuration
            loader = HierarchicalConfigLoader()
            config = loader.load_config(temp_path)
            
            # Create hierarchical team
            hierarchical_team = HierarchicalAgentTeam(
                name=name,
                hierarchical_config=config_data
            )
            
            # Add teams and workers based on configuration
            for team_config in config.teams:
                for worker_config in team_config.workers:
                    hierarchical_team.create_worker_from_config(
                        name=worker_config.name,
                        config_file=worker_config.config_file,
                        team_name=team_config.name
                    )
            
            return hierarchical_team, config_data
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    async def _create_team_from_file(self, team_id: str, name: str, config_file_path: str) -> tuple[HierarchicalAgentTeam, Dict[str, Any]]:
        """Create team from configuration file"""
        if not Path(config_file_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
        
        # Load configuration
        loader = HierarchicalConfigLoader()
        config = loader.load_config(config_file_path)
        
        # Load config data
        with open(config_file_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Create hierarchical team
        hierarchical_team = HierarchicalAgentTeam(
            name=name,
            hierarchical_config=config_data
        )
        
        # Add teams and workers based on configuration
        for team_config in config.teams:
            for worker_config in team_config.workers:
                hierarchical_team.create_worker_from_config(
                    name=worker_config.name,
                    config_file=worker_config.config_file,
                    config_data=worker_config.config_data,
                    team_name=team_config.name
                )
        
        return hierarchical_team, config_data
    
    async def _create_team_from_template(self, team_id: str, name: str, template_id: str) -> tuple[HierarchicalAgentTeam, Dict[str, Any]]:
        """Create team from template"""
        # Find template file
        template_paths = [
            f"configs/examples/hierarchical/{template_id}.yml",
            f"configs/templates/{template_id}.yml"
        ]
        
        template_path = None
        for path in template_paths:
            if Path(path).exists():
                template_path = path
                break
        
        if not template_path:
            raise FileNotFoundError(f"Template not found: {template_id}")
        
        return await self._create_team_from_file(team_id, name, template_path)
    
    def _get_hierarchy_info(self, team: HierarchicalAgentTeam) -> HierarchyInfo:
        """Get hierarchy information from a team"""
        try:
            team_hierarchy = team.get_hierarchy_info()
            
            # Convert to our response format
            teams_info = {}
            for team_name, team_data in team_hierarchy["teams"].items():
                workers = []
                for worker_name in team_data["workers"]:
                    worker = team.get_worker(worker_name)
                    if worker:
                        workers.append(WorkerInfo(
                            name=worker.name,
                            role=getattr(worker, 'role', 'worker'),
                            description=getattr(worker, 'description', ''),
                            capabilities=getattr(worker, 'capabilities', []),
                            config_file=getattr(worker, 'config_file', ''),
                            priority=1
                        ))
                
                teams_info[team_name] = TeamMemberInfo(
                    name=team_name,
                    description=f"Team {team_name}",
                    supervisor_name=team_data["supervisor"],
                    workers=workers,
                    worker_count=team_data["worker_count"]
                )
            
            return HierarchyInfo(
                coordinator=team_hierarchy["coordinator"],
                teams=teams_info,
                total_teams=team_hierarchy["total_teams"],
                total_workers=team_hierarchy["total_workers"]
            )
            
        except Exception as e:
            logger.error(f"Failed to get hierarchy info: {e}")
            return HierarchyInfo(
                coordinator={"name": "Unknown"},
                teams={},
                total_teams=0,
                total_workers=0
            )