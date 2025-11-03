"""
Agent service for managing agent library and compatibility
"""
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import os

from src.ui.enhanced_agent_library import EnhancedAgentLibrary
from src.ui.agent_role_classifier import AgentRole, AgentCapability
from src.config.dynamic_template_generator import DynamicTemplateGenerator
from ..models.agent_models import (
    AgentSearchRequest, AgentInfo, AgentListResponse, AgentResponse,
    AgentCapability as APIAgentCapability, AgentCompatibilityRequest,
    AgentCompatibilityResponse, AgentStatsResponse, TeamSuggestionRequest,
    TeamSuggestion, TeamSuggestionResponse
)

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing agent library and suggestions"""
    
    def __init__(self, storage: Dict[str, Any], config: Any):
        """Initialize agent service"""
        self.storage = storage
        self.config = config
        
        # Initialize enhanced library with proper configs path
        configs_path = "configs/examples"
        if not os.path.exists(configs_path):
            # Try relative path from project root
            configs_path = os.path.join(os.getcwd(), "configs", "examples")
            
        logger.info(f"Initializing AgentService with configs path: {configs_path}")
        
        try:
            self.enhanced_library = EnhancedAgentLibrary(configs_directory=configs_path)
            agents = self.enhanced_library.get_all_agents()
            logger.info(f"Successfully loaded {len(agents)} agents from {configs_path}")
            
            # Log agent details for debugging
            for agent_id, metadata in agents.items():
                logger.debug(f"Loaded agent: {agent_id} - {metadata.name} (role: {metadata.primary_role.value})")
                
        except Exception as e:
            logger.error(f"Failed to initialize EnhancedAgentLibrary: {e}")
            # Create empty library as fallback
            self.enhanced_library = None
            
        if self.enhanced_library:
            try:
                self.template_generator = DynamicTemplateGenerator(self.enhanced_library)
            except Exception as e:
                logger.error(f"Failed to initialize DynamicTemplateGenerator: {e}")
                self.template_generator = None
        else:
            self.template_generator = None
    
    async def search_agents(self, request: AgentSearchRequest) -> AgentListResponse:
        """Search agents based on criteria"""
        try:
            # Check if library is properly initialized
            if not self.enhanced_library:
                logger.error("EnhancedAgentLibrary not initialized")
                return AgentListResponse(
                    agents=[], 
                    total=0, 
                    limit=request.limit, 
                    offset=request.offset
                )
            
            # Get all agents
            if request.query:
                agents = self.enhanced_library.search_agents(request.query)
            else:
                agents = self.enhanced_library.get_all_agents()
                
            logger.debug(f"Found {len(agents)} agents before filtering")
            
            # Apply role filter
            if request.role:
                role_enum = AgentRole(request.role)
                agents = {
                    agent_id: metadata for agent_id, metadata in agents.items()
                    if metadata.primary_role == role_enum or role_enum in metadata.secondary_roles
                }
            
            # Apply capability filter
            if request.capabilities:
                capability_enums = [AgentCapability(cap) for cap in request.capabilities]
                agents = {
                    agent_id: metadata for agent_id, metadata in agents.items()
                    if any(cap in metadata.capabilities for cap in capability_enums)
                }
            
            # Convert to API format with pagination
            agent_list = []
            agent_items = list(agents.items())[request.offset:request.offset + request.limit]
            
            for agent_id, metadata in agent_items:
                agent_info = self._convert_to_agent_info(agent_id, metadata)
                agent_list.append(agent_info)
            
            return AgentListResponse(
                agents=agent_list,
                total=len(agents),
                limit=request.limit,
                offset=request.offset
            )
            
        except Exception as e:
            logger.error(f"Failed to search agents: {e}")
            return AgentListResponse(agents=[], total=0, limit=request.limit, offset=request.offset)
    
    async def get_agent(self, agent_id: str) -> Optional[AgentResponse]:
        """Get detailed information about a specific agent"""
        try:
            all_agents = self.enhanced_library.get_all_agents()
            
            if agent_id not in all_agents:
                return None
            
            metadata = all_agents[agent_id]
            agent_info = self._convert_to_agent_info(agent_id, metadata)
            
            # Load config data if available
            config_data = None
            if Path(metadata.file_path).exists():
                with open(metadata.file_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            
            # Mock usage stats (in a real implementation, this would come from actual usage data)
            usage_stats = {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_response_time": 0.0,
                "last_used": None
            }
            
            return AgentResponse(
                agent=agent_info,
                config_data=config_data,
                usage_stats=usage_stats
            )
            
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    async def get_agent_compatibility(self, request: AgentCompatibilityRequest) -> AgentCompatibilityResponse:
        """Get compatibility matrix for specified agents"""
        try:
            full_matrix = self.enhanced_library.get_agent_compatibility_matrix()
            
            # Filter matrix for requested agents
            filtered_matrix = {}
            for agent_id in request.agent_ids:
                if agent_id in full_matrix:
                    filtered_matrix[agent_id] = {
                        other_id: score for other_id, score in full_matrix[agent_id].items()
                        if other_id in request.agent_ids
                    }
            
            # Calculate average compatibility
            all_scores = []
            for agent_scores in filtered_matrix.values():
                all_scores.extend([score for score in agent_scores.values()])
            
            avg_compatibility = sum(all_scores) / len(all_scores) if all_scores else 0.0
            
            # Generate recommendations
            recommendations = []
            if avg_compatibility < 0.7:
                recommendations.append("Consider agents with more complementary capabilities")
            if len(request.agent_ids) > 5:
                recommendations.append("Large teams may benefit from hierarchical organization")
            
            return AgentCompatibilityResponse(
                compatibility_matrix=filtered_matrix,
                average_compatibility=avg_compatibility,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to get compatibility: {e}")
            return AgentCompatibilityResponse(
                compatibility_matrix={},
                average_compatibility=0.0,
                recommendations=["Error calculating compatibility"]
            )
    
    async def get_agent_stats(self) -> AgentStatsResponse:
        """Get statistics about the agent library"""
        try:
            stats = self.enhanced_library.get_statistics()
            
            # Calculate role statistics
            all_agents = self.enhanced_library.get_all_agents()
            by_role = {}
            for agent_id, metadata in all_agents.items():
                role = metadata.primary_role.value
                by_role[role] = by_role.get(role, 0) + 1
            
            return AgentStatsResponse(
                total_agents=stats['total_agents'],
                by_role=by_role,
                by_capability=stats['capabilities'],
                coordination_capable=stats['coordination_capable'],
                supervision_capable=stats['supervision_capable'],
                average_compatibility=stats['average_compatibility'],
                most_popular_capabilities=list(stats['capabilities'].keys())[:5]
            )
            
        except Exception as e:
            logger.error(f"Failed to get agent stats: {e}")
            return AgentStatsResponse(
                total_agents=0,
                by_role={},
                by_capability={},
                coordination_capable=0,
                supervision_capable=0,
                average_compatibility=0.0,
                most_popular_capabilities=[]
            )
    
    async def get_team_suggestions(self, request: TeamSuggestionRequest) -> TeamSuggestionResponse:
        """Get team composition suggestions for a task"""
        try:
            # Use the enhanced library to get suggestions
            suggestions = self.enhanced_library.get_team_suggestions(request.task_description)
            
            # Generate team configurations using template generator
            team_configs = []
            for suggestion in suggestions[:3]:  # Limit to top 3 suggestions
                try:
                    team_config = self.template_generator.generate_template_from_task(
                        request.task_description
                    )
                    
                    # Convert to API format
                    # This is a simplified conversion - in a real implementation,
                    # you'd properly map the team configuration to the response format
                    team_suggestion = TeamSuggestion(
                        coordinator=self._mock_agent_info("coordinator"),
                        teams=[{"name": "main_team", "agents": suggestion[:3]}],
                        reasoning=f"Team designed for: {request.task_description[:100]}...",
                        compatibility_score=0.85,
                        estimated_performance=0.80
                    )
                    team_configs.append(team_suggestion)
                    
                except Exception as e:
                    logger.warning(f"Failed to generate team config: {e}")
            
            return TeamSuggestionResponse(
                suggestions=team_configs,
                task_analysis={
                    "task_type": "general",
                    "complexity": "medium",
                    "required_capabilities": request.required_capabilities or [],
                    "estimated_duration": "unknown"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to get team suggestions: {e}")
            return TeamSuggestionResponse(
                suggestions=[],
                task_analysis={"error": str(e)}
            )
    
    def _convert_to_agent_info(self, agent_id: str, metadata) -> AgentInfo:
        """Convert library metadata to API AgentInfo format"""
        # Convert capabilities
        api_capabilities = []
        for capability in metadata.capabilities:
            api_capabilities.append(APIAgentCapability(
                name=capability.value,
                description=f"Capability: {capability.value}",
                category="general"
            ))
        
        return AgentInfo(
            id=agent_id,
            name=metadata.name,
            description=metadata.description,
            primary_role=metadata.primary_role.value,
            secondary_roles=[role.value for role in metadata.secondary_roles],
            capabilities=api_capabilities,
            tools=metadata.tools,
            specializations=metadata.specializations,
            file_path=metadata.file_path,
            compatibility_score=metadata.compatibility_score,
            can_coordinate=metadata.can_coordinate,
            can_supervise=metadata.can_supervise,
            team_size_limit=metadata.team_size_limit
        )
    
    def _mock_agent_info(self, role: str) -> AgentInfo:
        """Create a mock agent info for testing"""
        return AgentInfo(
            id=f"mock_{role}",
            name=f"Mock {role.title()}",
            description=f"Mock {role} agent",
            primary_role=role,
            secondary_roles=[],
            capabilities=[],
            tools=[],
            specializations=[],
            file_path="",
            compatibility_score=0.8,
            can_coordinate=(role == "coordinator"),
            can_supervise=(role in ["coordinator", "supervisor"])
        )