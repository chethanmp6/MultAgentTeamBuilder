"""
Dynamic Template Generator for Hierarchical Agent Configurations
"""
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path
import yaml
from dataclasses import dataclass

from ..ui.agent_role_classifier import AgentRole, AgentCapability
from ..ui.enhanced_agent_library import EnhancedAgentLibrary


@dataclass
class TeamMember:
    """Represents a team member in the hierarchy."""
    agent_id: str
    name: str
    role: str
    config_file: str
    capabilities: List[str]
    priority: int = 1
    description: str = ""


@dataclass
class Team:
    """Represents a team with supervisor and workers."""
    name: str
    description: str
    supervisor: TeamMember
    workers: List[TeamMember]
    specialization: str = ""
    max_workers: int = 5


@dataclass
class HierarchicalTeamConfig:
    """Represents the complete hierarchical team configuration."""
    name: str
    description: str
    version: str
    coordinator: TeamMember
    teams: List[Team]
    routing_strategy: str = "hybrid"
    communication_strategy: str = "direct"


class DynamicTemplateGenerator:
    """Generates hierarchical team configurations dynamically."""
    
    def __init__(self, agent_library: Optional[EnhancedAgentLibrary] = None):
        self.agent_library = agent_library or EnhancedAgentLibrary()
        self.routing_strategies = [
            "keyword_based",
            "llm_based", 
            "rule_based",
            "capability_based",
            "workload_based",
            "performance_based",
            "hybrid"
        ]
        self.communication_strategies = [
            "direct",
            "broadcast",
            "hierarchical",
            "peer_to_peer"
        ]
    
    def create_team_config(self, 
                          team_name: str,
                          team_description: str,
                          coordinator_id: str,
                          teams_data: List[Dict[str, Any]],
                          routing_strategy: str = "hybrid",
                          communication_strategy: str = "direct") -> HierarchicalTeamConfig:
        """Create a hierarchical team configuration."""
        
        # Get coordinator information
        coordinator_metadata = self.agent_library.get_agent_info_summary(coordinator_id)
        if not coordinator_metadata:
            raise ValueError(f"Coordinator '{coordinator_id}' not found")
        
        coordinator = TeamMember(
            agent_id=coordinator_id,
            name=coordinator_metadata["name"],
            role="coordinator",
            config_file=self.agent_library.agents[coordinator_id].file_path,
            capabilities=coordinator_metadata["capabilities"],
            description=coordinator_metadata["description"]
        )
        
        # Create teams
        teams = []
        for team_data in teams_data:
            team = self._create_team_from_data(team_data)
            teams.append(team)
        
        return HierarchicalTeamConfig(
            name=team_name,
            description=team_description,
            version="1.0.0",
            coordinator=coordinator,
            teams=teams,
            routing_strategy=routing_strategy,
            communication_strategy=communication_strategy
        )
    
    def _create_team_from_data(self, team_data: Dict[str, Any]) -> Team:
        """Create a team from team data."""
        team_name = team_data.get("name", "Unnamed Team")
        team_description = team_data.get("description", "")
        supervisor_id = team_data.get("supervisor_id")
        worker_ids = team_data.get("worker_ids", [])
        specialization = team_data.get("specialization", "")
        max_workers = team_data.get("max_workers", 5)
        
        # Get supervisor information
        supervisor_metadata = self.agent_library.get_agent_info_summary(supervisor_id)
        if not supervisor_metadata:
            raise ValueError(f"Supervisor '{supervisor_id}' not found")
        
        supervisor = TeamMember(
            agent_id=supervisor_id,
            name=supervisor_metadata["name"],
            role="supervisor",
            config_file=self.agent_library.agents[supervisor_id].file_path,
            capabilities=supervisor_metadata["capabilities"],
            description=supervisor_metadata["description"]
        )
        
        # Create workers
        workers = []
        for worker_id in worker_ids:
            worker_metadata = self.agent_library.get_agent_info_summary(worker_id)
            if worker_metadata:
                worker = TeamMember(
                    agent_id=worker_id,
                    name=worker_metadata["name"],
                    role="worker",
                    config_file=self.agent_library.agents[worker_id].file_path,
                    capabilities=worker_metadata["capabilities"],
                    description=worker_metadata["description"]
                )
                workers.append(worker)
        
        return Team(
            name=team_name,
            description=team_description,
            supervisor=supervisor,
            workers=workers,
            specialization=specialization,
            max_workers=max_workers
        )
    
    def generate_yaml_config(self, team_config: HierarchicalTeamConfig) -> str:
        """Generate YAML configuration from team config."""
        
        # Build the configuration structure
        config = {
            "# Dynamically Generated Hierarchical Team Configuration": None,
            "team": {
                "name": team_config.name,
                "description": team_config.description,
                "version": team_config.version,
                "type": "hierarchical",
                "created": datetime.now().isoformat(),
                "generator": "dynamic_template_generator"
            },
            
            "coordinator": {
                "name": team_config.coordinator.name,
                "description": team_config.coordinator.description,
                "agent_id": team_config.coordinator.agent_id,
                "config_file": team_config.coordinator.config_file,
                "capabilities": team_config.coordinator.capabilities,
                "llm": self._get_llm_config_from_agent(team_config.coordinator.agent_id),
                "routing": {
                    "strategy": team_config.routing_strategy,
                    "fallback_strategy": "hybrid",
                    "timeout_seconds": 30
                },
                "communication": {
                    "strategy": team_config.communication_strategy,
                    "broadcast_enabled": True,
                    "logging_enabled": True
                }
            },
            
            "teams": []
        }
        
        # Add teams
        for team in team_config.teams:
            team_dict = {
                "name": team.name,
                "description": team.description,
                "specialization": team.specialization,
                "max_workers": team.max_workers,
                "supervisor": {
                    "name": team.supervisor.name,
                    "description": team.supervisor.description,
                    "agent_id": team.supervisor.agent_id,
                    "config_file": team.supervisor.config_file,
                    "capabilities": team.supervisor.capabilities,
                    "llm": self._get_llm_config_from_agent(team.supervisor.agent_id),
                    "delegation": {
                        "strategy": "capability_based",
                        "load_balancing": True,
                        "retry_attempts": 2
                    }
                },
                "workers": []
            }
            
            # Add workers to team
            for worker in team.workers:
                worker_dict = {
                    "name": worker.name,
                    "description": worker.description,
                    "role": worker.role,
                    "agent_id": worker.agent_id,
                    "config_file": worker.config_file,
                    "capabilities": worker.capabilities,
                    "priority": worker.priority,
                    "performance": {
                        "timeout_seconds": 120,
                        "retry_attempts": 2,
                        "memory_enabled": True
                    }
                }
                team_dict["workers"].append(worker_dict)
            
            config["teams"].append(team_dict)
        
        # Add performance monitoring
        config["performance"] = {
            "monitoring": {
                "enabled": True,
                "metrics": [
                    "response_time",
                    "success_rate", 
                    "task_distribution",
                    "agent_utilization"
                ],
                "retention_days": 30
            },
            "optimization": {
                "enabled": True,
                "auto_scaling": False,
                "load_balancing": True,
                "performance_alerts": True
            },
            "analytics": {
                "dashboard_enabled": True,
                "reporting_frequency": "daily",
                "export_format": "json"
            }
        }
        
        # Add runtime configuration
        config["runtime"] = {
            "max_concurrent_tasks": 10,
            "task_timeout_seconds": 300,
            "coordination_timeout_seconds": 60,
            "memory_limit_mb": 1024,
            "debug_mode": False,
            "logging": {
                "enabled": True,
                "level": "INFO",
                "format": "structured"
            }
        }
        
        # Convert to YAML string
        yaml_str = yaml.dump(config, default_flow_style=False, indent=2, sort_keys=False)
        
        # Clean up the YAML (remove None values for comments)
        lines = yaml_str.split('\n')
        cleaned_lines = [line for line in lines if not line.strip().endswith(': null')]
        
        return '\n'.join(cleaned_lines)
    
    def _get_llm_config_from_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get LLM configuration from agent config file."""
        agent_metadata = self.agent_library.agents.get(agent_id)
        if not agent_metadata:
            return self._get_default_llm_config()
        
        try:
            with open(agent_metadata.file_path, 'r') as f:
                agent_config = yaml.safe_load(f)
            
            llm_config = agent_config.get('llm', {})
            return {
                "provider": llm_config.get('provider', 'openai'),
                "model": llm_config.get('model', 'gpt-4o-mini'),
                "temperature": llm_config.get('temperature', 0.7),
                "max_tokens": llm_config.get('max_tokens', 2000),
                "api_key_env": llm_config.get('api_key_env', 'OPENAI_API_KEY')
            }
        except Exception:
            return self._get_default_llm_config()
    
    def _get_default_llm_config(self) -> Dict[str, Any]:
        """Get default LLM configuration."""
        return {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000,
            "api_key_env": "OPENAI_API_KEY"
        }
    
    def generate_template_from_task(self, task_description: str, 
                                   team_name: Optional[str] = None) -> HierarchicalTeamConfig:
        """Generate a team template based on task description."""
        
        # Get team suggestions from agent library
        suggestions = self.agent_library.get_team_suggestions(task_description)
        
        if not suggestions.get("coordinators"):
            raise ValueError("No suitable coordinators found for this task")
        
        # Use the best coordinator
        coordinator = suggestions["coordinators"][0]
        coordinator_id = None
        for agent_id, metadata in self.agent_library.agents.items():
            if metadata == coordinator:
                coordinator_id = agent_id
                break
        
        if not coordinator_id:
            raise ValueError("Could not find coordinator ID")
        
        # Create teams based on suggestions
        teams_data = []
        
        # Group workers by specialization if possible
        workers_by_spec = {}
        for worker in suggestions.get("workers", []):
            worker_id = None
            for agent_id, metadata in self.agent_library.agents.items():
                if metadata == worker:
                    worker_id = agent_id
                    break
            
            if worker_id:
                # Group by primary capability or specialization
                primary_capability = list(worker.capabilities)[0].value if worker.capabilities else "general"
                if primary_capability not in workers_by_spec:
                    workers_by_spec[primary_capability] = []
                workers_by_spec[primary_capability].append(worker_id)
        
        # Create teams from grouped workers
        for spec, worker_ids in workers_by_spec.items():
            # Find a suitable supervisor
            supervisors = suggestions.get("supervisors", [])
            supervisor_id = None
            
            if supervisors:
                # Use first available supervisor
                for supervisor in supervisors:
                    for agent_id, metadata in self.agent_library.agents.items():
                        if metadata == supervisor:
                            supervisor_id = agent_id
                            break
                    if supervisor_id:
                        break
            
            # If no supervisor found, use coordinator as supervisor
            if not supervisor_id:
                supervisor_id = coordinator_id
            
            team_data = {
                "name": f"{spec.title()} Team",
                "description": f"Team specialized in {spec} tasks",
                "supervisor_id": supervisor_id,
                "worker_ids": worker_ids[:5],  # Limit to 5 workers per team
                "specialization": spec,
                "max_workers": 5
            }
            teams_data.append(team_data)
        
        # Generate team name if not provided
        if not team_name:
            capabilities = set()
            for worker in suggestions.get("workers", []):
                capabilities.update([cap.value for cap in worker.capabilities])
            team_name = f"Dynamic {', '.join(list(capabilities)[:2]).title()} Team"
        
        return self.create_team_config(
            team_name=team_name,
            team_description=f"Dynamically generated team for: {task_description}",
            coordinator_id=coordinator_id,
            teams_data=teams_data
        )
    
    def save_template(self, team_config: HierarchicalTeamConfig, 
                     output_dir: str = "configs/custom/hierarchical") -> str:
        """Save the template to a file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        safe_name = "".join(c for c in team_config.name if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"{safe_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml"
        
        file_path = output_path / filename
        
        # Generate and save YAML
        yaml_content = self.generate_yaml_config(team_config)
        
        with open(file_path, 'w') as f:
            f.write(yaml_content)
        
        return str(file_path)
    
    def validate_template(self, team_config: HierarchicalTeamConfig) -> Dict[str, Any]:
        """Validate a team template configuration."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Validate coordinator
        if not self.agent_library.agents.get(team_config.coordinator.agent_id):
            validation["errors"].append(f"Coordinator '{team_config.coordinator.agent_id}' not found")
        
        # Validate teams
        total_workers = 0
        for team in team_config.teams:
            # Validate supervisor
            if not self.agent_library.agents.get(team.supervisor.agent_id):
                validation["errors"].append(f"Supervisor '{team.supervisor.agent_id}' not found in team '{team.name}'")
            
            # Validate workers
            for worker in team.workers:
                if not self.agent_library.agents.get(worker.agent_id):
                    validation["errors"].append(f"Worker '{worker.agent_id}' not found in team '{team.name}'")
                else:
                    total_workers += 1
        
        # Check team composition
        if len(team_config.teams) == 0:
            validation["errors"].append("No teams defined")
        
        if total_workers == 0:
            validation["warnings"].append("No workers defined")
        
        # Check for capability coverage
        all_capabilities = set()
        for team in team_config.teams:
            for worker in team.workers:
                all_capabilities.update(worker.capabilities)
        
        essential_capabilities = {"web_search", "writing", "research"}
        missing_capabilities = essential_capabilities - all_capabilities
        
        if missing_capabilities:
            validation["suggestions"].append(
                f"Consider adding workers with capabilities: {', '.join(missing_capabilities)}"
            )
        
        if validation["errors"]:
            validation["valid"] = False
        
        return validation
    
    def get_available_routing_strategies(self) -> List[Dict[str, str]]:
        """Get available routing strategies with descriptions."""
        return [
            {"value": "keyword_based", "label": "Keyword Based", "description": "Route based on keywords in the request"},
            {"value": "llm_based", "label": "LLM Based", "description": "Use LLM to determine routing"},
            {"value": "rule_based", "label": "Rule Based", "description": "Route based on predefined rules"},
            {"value": "capability_based", "label": "Capability Based", "description": "Route based on agent capabilities"},
            {"value": "workload_based", "label": "Workload Based", "description": "Route based on current workload"},
            {"value": "performance_based", "label": "Performance Based", "description": "Route based on historical performance"},
            {"value": "hybrid", "label": "Hybrid", "description": "Combine multiple routing strategies"}
        ]
    
    def get_available_communication_strategies(self) -> List[Dict[str, str]]:
        """Get available communication strategies with descriptions."""
        return [
            {"value": "direct", "label": "Direct", "description": "Direct communication between agents"},
            {"value": "broadcast", "label": "Broadcast", "description": "Broadcast messages to all relevant agents"},
            {"value": "hierarchical", "label": "Hierarchical", "description": "Follow strict hierarchical communication"},
            {"value": "peer_to_peer", "label": "Peer to Peer", "description": "Allow peer-to-peer communication"}
        ]