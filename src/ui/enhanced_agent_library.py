"""
Enhanced Agent Library with role-based filtering and metadata
"""
from typing import Dict, Any, List, Set, Optional, Tuple
from pathlib import Path
import yaml
from dataclasses import asdict

from .agent_role_classifier import AgentRoleClassifier, AgentMetadata, AgentRole, AgentCapability


class EnhancedAgentLibrary:
    """Enhanced agent library with role classification and filtering capabilities."""
    
    def __init__(self, configs_directory: str = "configs/examples"):
        self.configs_directory = Path(configs_directory)
        self.classifier = AgentRoleClassifier()
        self.agents: Dict[str, AgentMetadata] = {}
        self.load_agents()
    
    def load_agents(self):
        """Load and classify all agents from the configurations directory."""
        self.agents = self.classifier.classify_agents_from_directory(str(self.configs_directory))
    
    def reload_agents(self):
        """Reload agents from the configurations directory."""
        self.load_agents()
    
    def get_all_agents(self) -> Dict[str, AgentMetadata]:
        """Get all available agents."""
        return self.agents
    
    def get_agents_by_role(self, role: AgentRole, include_secondary: bool = True) -> Dict[str, AgentMetadata]:
        """Get agents filtered by role."""
        return self.classifier.filter_agents_by_role(self.agents, role, include_secondary)
    
    def get_coordinators(self) -> Dict[str, AgentMetadata]:
        """Get agents capable of coordination."""
        return {
            agent_id: metadata for agent_id, metadata in self.agents.items()
            if metadata.can_coordinate or metadata.primary_role == AgentRole.COORDINATOR
        }
    
    def get_supervisors(self) -> Dict[str, AgentMetadata]:
        """Get agents capable of supervision."""
        return {
            agent_id: metadata for agent_id, metadata in self.agents.items()
            if metadata.can_supervise or metadata.primary_role == AgentRole.SUPERVISOR
        }
    
    def get_workers(self) -> Dict[str, AgentMetadata]:
        """Get worker agents."""
        return self.get_agents_by_role(AgentRole.WORKER)
    
    def get_specialists(self) -> Dict[str, AgentMetadata]:
        """Get specialist agents."""
        return self.get_agents_by_role(AgentRole.SPECIALIST)
    
    def get_agents_by_capability(self, capability: AgentCapability) -> Dict[str, AgentMetadata]:
        """Get agents with a specific capability."""
        return {
            agent_id: metadata for agent_id, metadata in self.agents.items()
            if capability in metadata.capabilities
        }
    
    def get_agents_by_capabilities(self, capabilities: Set[AgentCapability]) -> Dict[str, AgentMetadata]:
        """Get agents that have any of the specified capabilities."""
        return self.classifier.get_compatible_agents(self.agents, capabilities)
    
    def search_agents(self, query: str) -> Dict[str, AgentMetadata]:
        """Search agents by name, description, or capabilities."""
        query_lower = query.lower()
        results = {}
        
        for agent_id, metadata in self.agents.items():
            # Search in name and description
            if (query_lower in metadata.name.lower() or 
                query_lower in metadata.description.lower()):
                results[agent_id] = metadata
                continue
            
            # Search in capabilities
            capability_names = [cap.value for cap in metadata.capabilities]
            if any(query_lower in cap_name.lower() for cap_name in capability_names):
                results[agent_id] = metadata
                continue
            
            # Search in tools
            if any(query_lower in tool.lower() for tool in metadata.tools):
                results[agent_id] = metadata
                continue
            
            # Search in specializations
            if any(query_lower in spec.lower() for spec in metadata.specializations):
                results[agent_id] = metadata
        
        return results
    
    def get_team_suggestions(self, task_description: str) -> Dict[str, List[AgentMetadata]]:
        """Get suggested team composition for a task."""
        return self.classifier.suggest_team_composition(self.agents, task_description)
    
    def get_agent_compatibility_matrix(self) -> Dict[str, Dict[str, float]]:
        """Get compatibility matrix between agents."""
        matrix = {}
        agent_ids = list(self.agents.keys())
        
        for agent_id1 in agent_ids:
            matrix[agent_id1] = {}
            for agent_id2 in agent_ids:
                if agent_id1 == agent_id2:
                    matrix[agent_id1][agent_id2] = 1.0
                else:
                    compatibility = self._calculate_agent_compatibility(
                        self.agents[agent_id1], self.agents[agent_id2]
                    )
                    matrix[agent_id1][agent_id2] = compatibility
        
        return matrix
    
    def _calculate_agent_compatibility(self, agent1: AgentMetadata, agent2: AgentMetadata) -> float:
        """Calculate compatibility score between two agents."""
        score = 0.0
        
        # Capability overlap (complementary is better than identical)
        common_capabilities = agent1.capabilities.intersection(agent2.capabilities)
        total_capabilities = agent1.capabilities.union(agent2.capabilities)
        
        if len(total_capabilities) > 0:
            # Prefer some overlap but not complete overlap
            overlap_ratio = len(common_capabilities) / len(total_capabilities)
            score += 0.3 * (1 - abs(overlap_ratio - 0.3))  # Optimal around 30% overlap
        
        # Role compatibility
        if self._roles_are_compatible(agent1.primary_role, agent2.primary_role):
            score += 0.4
        
        # Tool compatibility
        common_tools = set(agent1.tools).intersection(set(agent2.tools))
        if len(common_tools) > 0:
            score += 0.1
        
        # Specialization diversity
        if len(set(agent1.specializations).intersection(set(agent2.specializations))) == 0:
            score += 0.2  # Different specializations are good for diversity
        
        return min(score, 1.0)
    
    def _roles_are_compatible(self, role1: AgentRole, role2: AgentRole) -> bool:
        """Check if two roles are compatible in a team."""
        # Define compatible role pairs
        compatible_pairs = [
            (AgentRole.COORDINATOR, AgentRole.SUPERVISOR),
            (AgentRole.COORDINATOR, AgentRole.WORKER),
            (AgentRole.COORDINATOR, AgentRole.SPECIALIST),
            (AgentRole.SUPERVISOR, AgentRole.WORKER),
            (AgentRole.SUPERVISOR, AgentRole.SPECIALIST),
        ]
        
        return ((role1, role2) in compatible_pairs or 
                (role2, role1) in compatible_pairs or
                role1 == role2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics."""
        stats = {
            "total_agents": len(self.agents),
            "roles": {},
            "capabilities": {},
            "average_compatibility": 0.0,
            "supervision_capable": 0,
            "coordination_capable": 0
        }
        
        # Role statistics
        for role in AgentRole:
            agents_with_role = self.get_agents_by_role(role, include_secondary=False)
            stats["roles"][role.value] = len(agents_with_role)
        
        # Capability statistics
        all_capabilities = set()
        for metadata in self.agents.values():
            all_capabilities.update(metadata.capabilities)
        
        for capability in all_capabilities:
            agents_with_capability = self.get_agents_by_capability(capability)
            stats["capabilities"][capability.value] = len(agents_with_capability)
        
        # Special capabilities
        stats["supervision_capable"] = sum(1 for metadata in self.agents.values() if metadata.can_supervise)
        stats["coordination_capable"] = sum(1 for metadata in self.agents.values() if metadata.can_coordinate)
        
        # Average compatibility score
        if self.agents:
            total_compatibility = sum(metadata.compatibility_score for metadata in self.agents.values())
            stats["average_compatibility"] = total_compatibility / len(self.agents)
        
        return stats
    
    def export_agent_metadata(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Export agent metadata as dictionary."""
        if agent_id in self.agents:
            metadata = self.agents[agent_id]
            # Convert to dictionary and handle special types
            data = asdict(metadata)
            # Convert sets to lists for JSON serialization
            data["capabilities"] = [cap.value for cap in metadata.capabilities]
            data["primary_role"] = metadata.primary_role.value
            data["secondary_roles"] = [role.value for role in metadata.secondary_roles]
            return data
        return None
    
    def export_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Export all agent metadata."""
        return {
            agent_id: self.export_agent_metadata(agent_id)
            for agent_id in self.agents.keys()
        }
    
    def validate_team_composition(self, coordinator_id: Optional[str], 
                                 supervisor_ids: List[str], 
                                 worker_ids: List[str]) -> Dict[str, Any]:
        """Validate a proposed team composition."""
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        # Check coordinator
        if coordinator_id:
            if coordinator_id not in self.agents:
                validation["errors"].append(f"Coordinator '{coordinator_id}' not found")
                validation["valid"] = False
            else:
                coordinator = self.agents[coordinator_id]
                if not coordinator.can_coordinate:
                    validation["warnings"].append(f"'{coordinator.name}' may not be suitable as coordinator")
        
        # Check supervisors
        for supervisor_id in supervisor_ids:
            if supervisor_id not in self.agents:
                validation["errors"].append(f"Supervisor '{supervisor_id}' not found")
                validation["valid"] = False
            else:
                supervisor = self.agents[supervisor_id]
                if not supervisor.can_supervise:
                    validation["warnings"].append(f"'{supervisor.name}' may not be suitable as supervisor")
        
        # Check workers
        for worker_id in worker_ids:
            if worker_id not in self.agents:
                validation["errors"].append(f"Worker '{worker_id}' not found")
                validation["valid"] = False
        
        # Check team size limits
        if coordinator_id and coordinator_id in self.agents:
            coordinator = self.agents[coordinator_id]
            if coordinator.team_size_limit and len(supervisor_ids) > coordinator.team_size_limit:
                validation["warnings"].append(
                    f"Team size ({len(supervisor_ids)}) exceeds coordinator's recommended limit ({coordinator.team_size_limit})"
                )
        
        # Check capability coverage
        all_capabilities = set()
        for worker_id in worker_ids:
            if worker_id in self.agents:
                all_capabilities.update(self.agents[worker_id].capabilities)
        
        essential_capabilities = {AgentCapability.WEB_SEARCH, AgentCapability.WRITING, AgentCapability.RESEARCH}
        missing_capabilities = essential_capabilities - all_capabilities
        
        if missing_capabilities:
            validation["suggestions"].append(
                f"Consider adding agents with: {', '.join([cap.value for cap in missing_capabilities])}"
            )
        
        return validation
    
    def get_recommended_workers_for_supervisor(self, supervisor_id: str, max_workers: int = 5) -> List[str]:
        """Get recommended workers for a specific supervisor."""
        if supervisor_id not in self.agents:
            return []
        
        supervisor = self.agents[supervisor_id]
        workers = self.get_workers()
        
        # Calculate compatibility scores
        compatibility_scores = []
        for worker_id, worker_metadata in workers.items():
            if worker_id != supervisor_id:  # Don't recommend the supervisor as a worker for itself
                compatibility = self._calculate_agent_compatibility(supervisor, worker_metadata)
                compatibility_scores.append((worker_id, compatibility))
        
        # Sort by compatibility and return top recommendations
        compatibility_scores.sort(key=lambda x: x[1], reverse=True)
        return [worker_id for worker_id, _ in compatibility_scores[:max_workers]]
    
    def get_agent_info_summary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of agent information for UI display."""
        if agent_id not in self.agents:
            return None
        
        metadata = self.agents[agent_id]
        return {
            "id": agent_id,
            "name": metadata.name,
            "description": metadata.description,
            "primary_role": metadata.primary_role.value,
            "secondary_roles": [role.value for role in metadata.secondary_roles],
            "capabilities": [cap.value for cap in metadata.capabilities],
            "tools": metadata.tools,
            "specializations": metadata.specializations,
            "can_supervise": metadata.can_supervise,
            "can_coordinate": metadata.can_coordinate,
            "compatibility_score": metadata.compatibility_score,
            "team_size_limit": metadata.team_size_limit
        }