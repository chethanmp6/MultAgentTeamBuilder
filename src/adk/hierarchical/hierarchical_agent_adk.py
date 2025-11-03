"""
ADK-based hierarchical agent team implementation.
Migrated from LangChain-based hierarchical_agent.py to Google ADK.
"""
from typing import Dict, Any, List, Optional
import os

# ADK imports (with fallback for development)
try:
    from google_adk import Agent
    from google_adk.models import Model
    ADK_AVAILABLE = True
except ImportError:
    print("Warning: Google ADK not available. Using mock implementations.")

    class Agent:
        def __init__(self, name: str, **kwargs):
            self.name = name

        def run(self, input_text: str):
            return {"response": f"Mock response from {self.name} to: {input_text}"}

    class Model:
        def __init__(self, name: str = "gemini-1.5-flash"):
            self.name = name

    ADK_AVAILABLE = False

from ..configurable_agent_adk import ADKConfigurableAgent
from .team_coordinator_adk import ADKTeamCoordinator
from .supervisor_adk import ADKSupervisorAgent
from .worker_agent_adk import ADKWorkerAgent


class ADKHierarchicalAgentTeam:
    """ADK-based hierarchical agent team management."""

    def __init__(self,
                 name: str = "adk_hierarchical_team",
                 coordinator_config: str = None,
                 coordinator_agent: Agent = None,
                 hierarchical_config: Dict[str, Any] = None):
        """
        Initialize an ADK hierarchical agent team.

        Args:
            name: Name of the hierarchical team
            coordinator_config: Path to coordinator configuration file (optional)
            coordinator_agent: Pre-configured ADK coordinator agent (optional)
            hierarchical_config: Hierarchical configuration data (optional)
        """
        self.name = name
        self.coordinator = None
        self.teams: Dict[str, ADKSupervisorAgent] = {}
        self.workers: Dict[str, ADKWorkerAgent] = {}
        self.hierarchical_config = hierarchical_config

        # Initialize coordinator
        if coordinator_config:
            self.coordinator = ADKTeamCoordinator(
                name="adk_coordinator",
                config_file=coordinator_config,
                teams={}
            )
        elif hierarchical_config and 'coordinator' in hierarchical_config:
            # Initialize from hierarchical config
            self._setup_coordinator_from_config(hierarchical_config['coordinator'])
        elif coordinator_agent:
            self.coordinator = ADKTeamCoordinator(
                name="adk_coordinator",
                adk_agent=coordinator_agent,
                teams={}
            )
        else:
            # Use default configuration
            self._setup_default_coordinator()

    def _setup_coordinator_from_config(self, coordinator_config: Dict[str, Any]):
        """Setup coordinator from hierarchical configuration."""
        # Extract model configuration
        llm_config = coordinator_config.get('llm', {})
        api_key = os.getenv(llm_config.get('api_key_env', 'GOOGLE_API_KEY'))

        # Map provider to Google models for ADK
        provider = llm_config.get('provider', 'google').lower()
        model_name = llm_config.get('model', 'gemini-1.5-flash')

        # Map common models to Gemini equivalents
        model_mapping = {
            "gpt-4o-mini": "gemini-1.5-flash",
            "gpt-4": "gemini-1.5-pro",
            "claude-3-5-sonnet-20241022": "gemini-1.5-pro",
            "claude-3-haiku": "gemini-1.5-flash"
        }
        mapped_model = model_mapping.get(model_name, model_name)

        # Prepare model parameters
        model_params = {
            "temperature": llm_config.get('temperature', 0.7),
            "max_tokens": llm_config.get('max_tokens', 2000)
        }

        # Create ADK model
        try:
            if ADK_AVAILABLE:
                model = Model(name=mapped_model, **model_params)
            else:
                model = Model(name=mapped_model)
        except Exception as e:
            print(f"Warning: Failed to create model {mapped_model}: {str(e)}")
            model = Model(name="gemini-1.5-flash")

        # Create coordinator
        self.coordinator = ADKTeamCoordinator(
            name="adk_coordinator",
            model=model,
            teams={}
        )

    def _setup_default_coordinator(self):
        """Setup default coordinator with Google ADK."""
        try:
            if ADK_AVAILABLE:
                default_model = Model(name="gemini-1.5-flash", temperature=0.7)
            else:
                default_model = Model(name="gemini-1.5-flash")

            self.coordinator = ADKTeamCoordinator(
                name="adk_coordinator",
                model=default_model,
                teams={}
            )
        except Exception as e:
            print(f"Warning: Failed to setup default coordinator: {str(e)}")
            self.coordinator = ADKTeamCoordinator(
                name="adk_coordinator",
                teams={}
            )

    def add_worker(self, worker: ADKWorkerAgent, team_name: str = "default"):
        """Add a worker to a specific team."""
        # Create team if it doesn't exist
        if team_name not in self.teams:
            self.teams[team_name] = ADKSupervisorAgent(
                name=f"{team_name}_supervisor",
                coordinator_model=self.coordinator.model if self.coordinator else None
            )
            # Add team to coordinator
            if self.coordinator:
                self.coordinator.add_team(team_name, self.teams[team_name])

        # Add worker to team
        self.teams[team_name].add_worker(worker)
        self.workers[worker.name] = worker

    def add_team(self, team_name: str, supervisor: ADKSupervisorAgent):
        """Add a complete team with supervisor."""
        self.teams[team_name] = supervisor
        if self.coordinator:
            self.coordinator.add_team(team_name, supervisor)

        # Add all workers from the team to our workers dict
        for worker in supervisor.workers:
            self.workers[worker.name] = worker

    def create_worker_from_config(self,
                                name: str,
                                config_file: str = None,
                                config_data: Dict[str, Any] = None,
                                team_name: str = "default") -> ADKWorkerAgent:
        """Create a worker from a configuration file or embedded config data."""
        if config_file:
            worker = ADKWorkerAgent(name=name, config_file=config_file)
        elif config_data:
            # Convert LangChain config to ADK format if needed
            adk_config = self._convert_config_to_adk(config_data)
            worker = ADKWorkerAgent(name=name, config_data=adk_config)
        else:
            raise ValueError("Either config_file or config_data must be provided")

        self.add_worker(worker, team_name)
        return worker

    def create_supervisor_from_config(self, team_name: str, config_file: str) -> ADKSupervisorAgent:
        """Create a supervisor from a configuration file."""
        supervisor = ADKSupervisorAgent(name=f"{team_name}_supervisor", config_file=config_file)
        self.add_team(team_name, supervisor)
        return supervisor

    def _convert_config_to_adk(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LangChain configuration to ADK format."""
        adk_config = config_data.copy()

        # Convert LLM configuration
        if 'llm' in adk_config:
            llm_config = adk_config['llm']

            # Map to Google providers
            provider_mapping = {
                "openai": "google",
                "anthropic": "google",
                "gemini": "google",
                "groq": "google"
            }

            original_provider = llm_config.get('provider', 'openai')
            llm_config['provider'] = provider_mapping.get(original_provider, 'google')

            # Map model names
            model_mapping = {
                "gpt-4o-mini": "gemini-1.5-flash",
                "gpt-4": "gemini-1.5-pro",
                "claude-3-5-sonnet-20241022": "gemini-1.5-pro",
                "claude-3-haiku": "gemini-1.5-flash"
            }

            original_model = llm_config.get('model', 'gpt-4o-mini')
            llm_config['model'] = model_mapping.get(original_model, 'gemini-1.5-flash')

            # Update API key if needed
            if original_provider != 'google':
                llm_config['api_key_env'] = 'GOOGLE_API_KEY'

        # Convert ReAct to workflow
        if 'react' in adk_config:
            react_config = adk_config.pop('react')
            adk_config['workflow'] = {
                'max_iterations': react_config.get('max_iterations', 10),
                'timeout_seconds': react_config.get('timeout_seconds', 300),
                'workflow_type': 'sequential'
            }

        # Add framework specification
        if 'agent' in adk_config:
            adk_config['agent']['framework'] = 'google-adk'

        return adk_config

    def remove_worker(self, worker_name: str):
        """Remove a worker from its team."""
        for team_name, supervisor in self.teams.items():
            if supervisor.remove_worker(worker_name):
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
            if self.coordinator:
                self.coordinator.remove_team(team_name)

    def get_worker(self, worker_name: str) -> Optional[ADKWorkerAgent]:
        """Get a worker by name."""
        return self.workers.get(worker_name)

    def get_team(self, team_name: str) -> Optional[ADKSupervisorAgent]:
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
                "config": worker.get_config() is not None,
                "framework": "google-adk",
                "agent_type": "worker"
            }
            worker_info.append(info)
        return worker_info

    def list_teams(self) -> List[Dict[str, Any]]:
        """List all teams with their information."""
        if self.coordinator:
            return self.coordinator.list_teams()
        return []

    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run the ADK hierarchical team with given input."""
        if not self.coordinator:
            raise ValueError("No coordinator configured")

        if not self.teams:
            raise ValueError("No teams available")

        # Run through coordinator
        result = self.coordinator.run(input_text, **kwargs)

        # Add hierarchical team metadata
        if isinstance(result, dict):
            result["hierarchical_team"] = {
                "name": self.name,
                "framework": "google-adk",
                "total_teams": len(self.teams),
                "total_workers": len(self.workers),
                "teams": list(self.teams.keys()),
                "workers": list(self.workers.keys()),
                "adk_available": ADK_AVAILABLE
            }
        else:
            result = {
                "response": str(result),
                "hierarchical_team": {
                    "name": self.name,
                    "framework": "google-adk",
                    "total_teams": len(self.teams),
                    "total_workers": len(self.workers)
                }
            }

        return result

    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Async version of run."""
        # For now, run synchronously
        # In production, this would use ADK's async capabilities
        return self.run(input_text, **kwargs)

    def run_direct_worker(self, worker_name: str, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run a specific worker directly."""
        worker = self.get_worker(worker_name)
        if not worker:
            return {
                "error": f"Worker '{worker_name}' not found",
                "response": f"Error: Worker '{worker_name}' is not available",
                "framework": "google-adk",
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
                "framework": "google-adk",
                "metadata": kwargs
            }

        return team.run(input_text, **kwargs)

    def get_hierarchy_info(self) -> Dict[str, Any]:
        """Get information about the hierarchical structure."""
        coordinator_info = None
        if self.coordinator:
            coordinator_info = {
                "name": self.coordinator.name,
                "model": getattr(self.coordinator.model, 'name', 'unknown') if self.coordinator.model else None,
                "framework": "google-adk"
            }

        return {
            "name": self.name,
            "framework": "google-adk",
            "adk_available": ADK_AVAILABLE,
            "coordinator": coordinator_info,
            "teams": {
                team_name: {
                    "supervisor": supervisor.name,
                    "worker_count": len(supervisor.workers),
                    "workers": [w.name for w in supervisor.workers],
                    "framework": "google-adk"
                }
                for team_name, supervisor in self.teams.items()
            },
            "total_teams": len(self.teams),
            "total_workers": len(self.workers)
        }

    def migrate_from_langchain_team(self, langchain_team) -> Dict[str, Any]:
        """
        Migrate data from a LangChain hierarchical team to this ADK team.

        Args:
            langchain_team: The LangChain HierarchicalAgentTeam instance

        Returns:
            Migration report
        """
        migration_report = {
            "migration_status": "started",
            "components_migrated": [],
            "workers_migrated": 0,
            "teams_migrated": 0,
            "warnings": [],
            "errors": []
        }

        try:
            # Migrate workers
            if hasattr(langchain_team, 'workers') and langchain_team.workers:
                for worker_name, lc_worker in langchain_team.workers.items():
                    try:
                        # Create ADK worker from LangChain worker
                        adk_worker = ADKWorkerAgent(name=worker_name)

                        # Try to migrate memory if available
                        if hasattr(lc_worker, 'memory_manager') and lc_worker.memory_manager:
                            # This would require memory migration logic
                            pass

                        self.workers[worker_name] = adk_worker
                        migration_report["workers_migrated"] += 1

                    except Exception as e:
                        migration_report["warnings"].append(f"Worker {worker_name} migration failed: {str(e)}")

            # Migrate teams
            if hasattr(langchain_team, 'teams') and langchain_team.teams:
                for team_name, lc_supervisor in langchain_team.teams.items():
                    try:
                        # Create ADK supervisor
                        adk_supervisor = ADKSupervisorAgent(name=f"{team_name}_supervisor")
                        self.teams[team_name] = adk_supervisor
                        migration_report["teams_migrated"] += 1

                    except Exception as e:
                        migration_report["warnings"].append(f"Team {team_name} migration failed: {str(e)}")

            migration_report["components_migrated"] = ["workers", "teams", "coordinator"]
            migration_report["migration_status"] = "completed"

        except Exception as e:
            migration_report["migration_status"] = "failed"
            migration_report["errors"].append(f"Migration failed: {str(e)}")

        return migration_report

    def export_adk_config(self) -> Dict[str, Any]:
        """Export the current team configuration in ADK format."""
        return {
            "team": {
                "name": self.name,
                "framework": "google-adk",
                "type": "hierarchical"
            },
            "coordinator": {
                "name": self.coordinator.name if self.coordinator else None,
                "model": getattr(self.coordinator.model, 'name', None) if self.coordinator and self.coordinator.model else None
            },
            "teams": {
                team_name: {
                    "supervisor": supervisor.name,
                    "workers": [w.name for w in supervisor.workers]
                }
                for team_name, supervisor in self.teams.items()
            },
            "workers": list(self.workers.keys()),
            "metadata": {
                "adk_available": ADK_AVAILABLE,
                "total_teams": len(self.teams),
                "total_workers": len(self.workers)
            }
        }

    def __str__(self) -> str:
        return f"ADKHierarchicalAgentTeam(name='{self.name}', teams={len(self.teams)}, workers={len(self.workers)}, framework='google-adk')"

    def __repr__(self) -> str:
        return self.__str__()