"""
Hierarchical Agent Team - Main class for managing hierarchical agent teams
"""
from typing import Dict, Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.chat_models import init_chat_model
import os

from ..core.configurable_agent import ConfigurableAgent
from .supervisor import SupervisorAgent
from .worker_agent import WorkerAgent
from .team_coordinator import TeamCoordinator


class HierarchicalAgentTeam:
    """Main class for managing hierarchical agent teams."""
    
    def __init__(self, 
                 name: str = "hierarchical_team",
                 coordinator_config: str = None,
                 llm: BaseChatModel = None,
                 hierarchical_config: Dict[str, Any] = None):
        """
        Initialize a hierarchical agent team.
        
        Args:
            name: Name of the hierarchical team
            coordinator_config: Path to coordinator configuration file (optional)
            llm: Language model to use for coordinator (optional)
            hierarchical_config: Hierarchical configuration data (optional)
        """
        self.name = name
        self.coordinator = None
        self.teams: Dict[str, SupervisorAgent] = {}
        self.workers: Dict[str, WorkerAgent] = {}
        self.hierarchical_config = hierarchical_config
        
        # Initialize coordinator
        if coordinator_config:
            self.coordinator = TeamCoordinator(
                name="coordinator",
                config_file=coordinator_config,
                teams={}
            )
        elif hierarchical_config and 'coordinator' in hierarchical_config:
            # Initialize from hierarchical config
            self._setup_coordinator_from_config(hierarchical_config['coordinator'])
        elif llm:
            self.coordinator = TeamCoordinator(
                name="coordinator",
                llm=llm,
                teams={}
            )
        else:
            # Use default OpenAI model
            default_llm = init_chat_model("openai:gpt-4o-mini", temperature=0.7)
            self.coordinator = TeamCoordinator(
                name="coordinator",
                llm=default_llm,
                teams={}
            )
    
    def add_worker(self, worker: WorkerAgent, team_name: str = "default"):
        """Add a worker to a specific team."""
        # Create team if it doesn't exist
        if team_name not in self.teams:
            self.teams[team_name] = SupervisorAgent(
                name=f"{team_name}_supervisor",
                llm=self.coordinator.llm
            )
            # Add team to coordinator
            self.coordinator.add_team(team_name, self.teams[team_name])
        
        # Add worker to team
        self.teams[team_name].add_worker(worker)
        self.workers[worker.name] = worker
    
    def _setup_coordinator_from_config(self, coordinator_config: Dict[str, Any]):
        """Setup coordinator from hierarchical configuration."""
        # Extract LLM configuration
        llm_config = coordinator_config.get('llm', {})
        api_key = os.getenv(llm_config.get('api_key_env', 'OPENAI_API_KEY'))
        
        # Map provider names to init_chat_model format
        provider_mapping = {
            "openai": "openai",
            "anthropic": "anthropic", 
            "gemini": "google_vertexai",
            "groq": "groq"
        }
        
        provider = llm_config.get('provider', 'openai').lower()
        mapped_provider = provider_mapping.get(provider, 'openai')
        
        # Prepare model name with provider prefix
        model_name = f"{mapped_provider}:{llm_config.get('model', 'gpt-4o-mini')}"
        
        # Prepare additional kwargs
        llm_kwargs = {
            "temperature": llm_config.get('temperature', 0.7),
            "max_tokens": llm_config.get('max_tokens', 2000),
            "api_key": api_key
        }
        
        # Add base_url if specified
        if llm_config.get('base_url'):
            llm_kwargs["base_url"] = llm_config.get('base_url')
        
        # Create LLM instance using init_chat_model
        try:
            llm = init_chat_model(
                model=model_name,
                **llm_kwargs
            )
        except Exception as e:
            # Fallback to default OpenAI model
            llm = init_chat_model("openai:gpt-4o-mini", temperature=0.7)
        
        # Create coordinator
        self.coordinator = TeamCoordinator(
            name="coordinator",
            llm=llm,
            teams={}
        )
    
    def add_team(self, team_name: str, supervisor: SupervisorAgent):
        """Add a complete team with supervisor."""
        self.teams[team_name] = supervisor
        self.coordinator.add_team(team_name, supervisor)
        
        # Add all workers from the team to our workers dict
        for worker in supervisor.workers:
            self.workers[worker.name] = worker
    
    def create_worker_from_config(self, name: str, config_file: str = None, config_data: Dict[str, Any] = None, team_name: str = "default"):
        """Create a worker from a configuration file or embedded config data."""
        if config_file:
            worker = WorkerAgent(name=name, config_file=config_file)
        elif config_data:
            # Create worker with embedded configuration data
            worker = WorkerAgent(name=name, config_data=config_data)
        else:
            raise ValueError("Either config_file or config_data must be provided")
        
        self.add_worker(worker, team_name)
        return worker
    
    def create_supervisor_from_config(self, team_name: str, config_file: str):
        """Create a supervisor from a configuration file."""
        supervisor = SupervisorAgent(name=f"{team_name}_supervisor", config_file=config_file)
        self.add_team(team_name, supervisor)
        return supervisor
    
    def remove_worker(self, worker_name: str):
        """Remove a worker from its team."""
        for team_name, supervisor in self.teams.items():
            supervisor.remove_worker(worker_name)
            if worker_name in self.workers:
                del self.workers[worker_name]
            break
    
    def remove_team(self, team_name: str):
        """Remove a team and all its workers."""
        if team_name in self.teams:
            # Remove workers from our dict
            team_workers = self.teams[team_name].workers
            for worker in team_workers:
                if worker.name in self.workers:
                    del self.workers[worker.name]
            
            # Remove team
            del self.teams[team_name]
            self.coordinator.remove_team(team_name)
    
    def get_worker(self, worker_name: str) -> Optional[WorkerAgent]:
        """Get a worker by name."""
        return self.workers.get(worker_name)
    
    def get_team(self, team_name: str) -> Optional[SupervisorAgent]:
        """Get a team by name."""
        return self.teams.get(team_name)
    
    def list_workers(self) -> List[Dict[str, Any]]:
        """List all workers with their information."""
        worker_info = []
        for worker_name, worker in self.workers.items():
            info = {
                "name": worker_name,
                "description": worker.description,
                "tools": worker.get_available_tools(),
                "config": worker.get_config() is not None
            }
            worker_info.append(info)
        return worker_info
    
    def list_teams(self) -> List[Dict[str, Any]]:
        """List all teams with their information."""
        return self.coordinator.list_teams()
    
    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run the hierarchical team with given input."""
        if not self.coordinator:
            raise ValueError("No coordinator configured")
        
        if not self.teams:
            raise ValueError("No teams available")
        
        # Run through coordinator
        result = self.coordinator.run(input_text, **kwargs)
        
        # Add hierarchical team metadata
        result["hierarchical_team"] = {
            "name": self.name,
            "total_teams": len(self.teams),
            "total_workers": len(self.workers),
            "teams": list(self.teams.keys()),
            "workers": list(self.workers.keys())
        }
        
        return result
    
    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Async version of run."""
        # For now, run synchronously
        return self.run(input_text, **kwargs)
    
    def run_direct_worker(self, worker_name: str, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run a specific worker directly."""
        worker = self.get_worker(worker_name)
        if not worker:
            return {
                "error": f"Worker '{worker_name}' not found",
                "response": f"Error: Worker '{worker_name}' is not available",
                "metadata": kwargs
            }
        
        return worker.run(input_text, **kwargs)
    
    def run_direct_team(self, team_name: str, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run a specific team directly."""
        team = self.get_team(team_name)
        if not team:
            return {
                "error": f"Team '{team_name}' not found",
                "response": f"Error: Team '{team_name}' is not available",
                "metadata": kwargs
            }
        
        return team.run(input_text, **kwargs)
    
    def get_hierarchy_info(self) -> Dict[str, Any]:
        """Get information about the hierarchical structure."""
        return {
            "name": self.name,
            "coordinator": {
                "name": self.coordinator.name if self.coordinator else None,
                "llm": self.coordinator.llm.model_name if self.coordinator and self.coordinator.llm else None
            },
            "teams": {
                team_name: {
                    "supervisor": supervisor.name,
                    "worker_count": len(supervisor.workers),
                    "workers": [w.name for w in supervisor.workers]
                }
                for team_name, supervisor in self.teams.items()
            },
            "total_teams": len(self.teams),
            "total_workers": len(self.workers)
        }
    
    def __str__(self) -> str:
        return f"HierarchicalAgentTeam(name='{self.name}', teams={len(self.teams)}, workers={len(self.workers)})"
    
    def __repr__(self) -> str:
        return self.__str__() 