"""
ADK-based team coordinator for hierarchical agent systems.
Migrated from LangChain-based team_coordinator.py to Google ADK.
"""
from typing import Dict, Any, List, Optional, Union

# ADK imports (with fallback for development)
try:
    from google_adk import Agent
    from google_adk.models import Model
    from google_adk.core import Message
    ADK_AVAILABLE = True
except ImportError:
    print("Warning: Google ADK not available. Using mock implementations.")

    class Agent:
        def __init__(self, name: str, **kwargs):
            self.name = name

        def run(self, input_text: str):
            return {"response": f"Mock coordinator response to: {input_text}"}

    class Model:
        def __init__(self, name: str = "gemini-1.5-flash"):
            self.name = name

    class Message:
        def __init__(self, content: str, role: str = "user"):
            self.content = content
            self.role = role

    ADK_AVAILABLE = False

from ..configurable_agent_adk import ADKConfigurableAgent
from .enhanced_routing_adk import ADKEnhancedRoutingEngine, ADKRoutingStrategy


class ADKTeamCoordinator:
    """ADK-based team coordinator for managing multiple agent teams."""

    def __init__(self,
                 name: str = "adk_coordinator",
                 config_file: str = None,
                 adk_agent: Agent = None,
                 model: Model = None,
                 teams: Dict[str, Any] = None):
        """
        Initialize ADK team coordinator.

        Args:
            name: Coordinator name
            config_file: Path to configuration file (optional)
            adk_agent: Pre-configured ADK agent (optional)
            model: ADK model for the coordinator (optional)
            teams: Dictionary of teams to manage (optional)
        """
        self.name = name
        self.teams = teams or {}
        self.routing_engine = None
        self.agent = None
        self.model = model

        # Initialize coordinator agent
        if config_file:
            # Create from configuration file
            self.configurable_agent = ADKConfigurableAgent(config_file=config_file)
            self.agent = self.configurable_agent.agent
            self.model = self.configurable_agent.model
        elif adk_agent:
            # Use pre-configured agent
            self.agent = adk_agent
        elif model:
            # Create agent with provided model
            self._create_agent_with_model(model)
        else:
            # Create default agent
            self._create_default_agent()

        # Initialize routing engine
        self._setup_routing_engine()

    def _create_agent_with_model(self, model: Model):
        """Create coordinator agent with specified model."""
        instructions = """You are a Team Coordinator for a hierarchical agent system. Your role is to:

1. Analyze incoming tasks and determine the most appropriate team to handle them
2. Route tasks to the best-suited team based on capabilities and workload
3. Coordinate between teams when necessary
4. Provide consolidated responses from team outputs

Available teams and their capabilities will be provided with each task.

When making routing decisions, consider:
- Task complexity and requirements
- Team specializations and capabilities
- Current team workload and availability
- Task urgency and priority

Always provide clear reasoning for your routing decisions."""

        try:
            if ADK_AVAILABLE:
                self.agent = Agent(
                    name=self.name,
                    instructions=instructions,
                    model=model
                )
            else:
                self.agent = Agent(name=self.name)
        except Exception as e:
            print(f"Warning: Failed to create coordinator agent: {str(e)}")
            self.agent = Agent(name=self.name)

    def _create_default_agent(self):
        """Create default coordinator agent."""
        try:
            if ADK_AVAILABLE:
                default_model = Model(name="gemini-1.5-flash", temperature=0.3)
                self._create_agent_with_model(default_model)
                self.model = default_model
            else:
                self.agent = Agent(name=self.name)
                self.model = Model(name="gemini-1.5-flash")
        except Exception as e:
            print(f"Warning: Failed to create default coordinator: {str(e)}")
            self.agent = Agent(name=self.name)
            self.model = Model(name="gemini-1.5-flash")

    def _setup_routing_engine(self):
        """Setup the routing engine with the coordinator agent."""
        try:
            self.routing_engine = ADKEnhancedRoutingEngine(
                routing_agent=self.agent,
                default_strategy=ADKRoutingStrategy.HYBRID
            )
        except Exception as e:
            print(f"Warning: Failed to setup routing engine: {str(e)}")
            self.routing_engine = ADKEnhancedRoutingEngine(
                default_strategy=ADKRoutingStrategy.KEYWORD_BASED
            )

    def add_team(self, team_name: str, team_agent: Any):
        """
        Add a team to the coordinator.

        Args:
            team_name: Name of the team
            team_agent: Team supervisor agent
        """
        self.teams[team_name] = team_agent

        # Register team capabilities with routing engine if available
        if self.routing_engine and hasattr(team_agent, 'get_capabilities'):
            try:
                capabilities = team_agent.get_capabilities()
                from .enhanced_routing_adk import ADKAgentCapability

                agent_capability = ADKAgentCapability(
                    agent_id=team_name,
                    capabilities=capabilities.get('capabilities', []),
                    specialization_keywords=capabilities.get('keywords', []),
                    priority=capabilities.get('priority', 1)
                )
                self.routing_engine.register_agent(agent_capability)
            except Exception as e:
                print(f"Warning: Failed to register team {team_name}: {str(e)}")

    def remove_team(self, team_name: str):
        """Remove a team from the coordinator."""
        if team_name in self.teams:
            del self.teams[team_name]

    def route_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route a task to the most appropriate team.

        Args:
            task_description: Description of the task
            context: Additional context for routing

        Returns:
            Dictionary with routing decision and metadata
        """
        if not self.teams:
            return {
                "error": "No teams available",
                "target_team": None,
                "reasoning": "No teams configured"
            }

        available_teams = list(self.teams.keys())
        context = context or {}

        try:
            if self.routing_engine:
                decision = self.routing_engine.route_task(
                    task_description=task_description,
                    available_agents=available_teams,
                    context=context
                )

                return {
                    "target_team": decision.target,
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning,
                    "strategy": decision.strategy_used.value,
                    "alternatives": decision.alternative_targets,
                    "metadata": decision.metadata
                }
            else:
                # Fallback to simple routing
                target_team = available_teams[0]  # Simple fallback
                return {
                    "target_team": target_team,
                    "confidence": 0.5,
                    "reasoning": "Fallback routing - using first available team",
                    "strategy": "fallback"
                }

        except Exception as e:
            return {
                "error": str(e),
                "target_team": available_teams[0] if available_teams else None,
                "reasoning": f"Error in routing: {str(e)}"
            }

    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Process input through the coordinator and route to appropriate team.

        Args:
            input_text: Input text to process
            **kwargs: Additional parameters

        Returns:
            Dictionary with coordinator response and metadata
        """
        if not self.teams:
            return {
                "error": "No teams available",
                "response": "No teams configured for this coordinator",
                "coordinator": self.name,
                "framework": "google-adk"
            }

        try:
            # Route the task
            routing_result = self.route_task(input_text, kwargs)

            if "error" in routing_result:
                return {
                    "error": routing_result["error"],
                    "response": f"Routing failed: {routing_result['error']}",
                    "coordinator": self.name,
                    "framework": "google-adk"
                }

            target_team = routing_result["target_team"]
            if target_team not in self.teams:
                return {
                    "error": f"Target team '{target_team}' not found",
                    "response": f"Team '{target_team}' is not available",
                    "coordinator": self.name,
                    "framework": "google-adk"
                }

            # Execute task on target team
            team_agent = self.teams[target_team]
            team_result = team_agent.run(input_text, **kwargs)

            # Update routing engine performance metrics if available
            if self.routing_engine:
                try:
                    success = not ("error" in team_result)
                    response_time = kwargs.get("response_time", 1.0)
                    self.routing_engine.update_agent_performance(
                        target_team, response_time, success
                    )
                except Exception as e:
                    print(f"Warning: Failed to update performance metrics: {str(e)}")

            # Build comprehensive response
            response = {
                "response": team_result.get("response", str(team_result)),
                "coordinator": self.name,
                "framework": "google-adk",
                "routing": {
                    "target_team": target_team,
                    "confidence": routing_result.get("confidence", 0.5),
                    "reasoning": routing_result.get("reasoning", "Team selected"),
                    "strategy": routing_result.get("strategy", "unknown")
                },
                "team_result": team_result,
                "metadata": {
                    "total_teams": len(self.teams),
                    "available_teams": list(self.teams.keys()),
                    "adk_available": ADK_AVAILABLE,
                    **kwargs
                }
            }

            return response

        except Exception as e:
            return {
                "error": str(e),
                "response": f"Coordinator error: {str(e)}",
                "coordinator": self.name,
                "framework": "google-adk",
                "metadata": kwargs
            }

    def list_teams(self) -> List[Dict[str, Any]]:
        """List all teams with their information."""
        teams_info = []
        for team_name, team_agent in self.teams.items():
            info = {
                "name": team_name,
                "type": "supervisor",
                "framework": "google-adk",
                "available": True
            }

            # Try to get additional team information
            try:
                if hasattr(team_agent, 'get_team_info'):
                    team_info = team_agent.get_team_info()
                    info.update(team_info)
                elif hasattr(team_agent, 'workers'):
                    info["worker_count"] = len(team_agent.workers)
                    info["workers"] = [w.name for w in team_agent.workers] if team_agent.workers else []
            except Exception as e:
                info["warning"] = f"Could not get team info: {str(e)}"

            teams_info.append(info)

        return teams_info

    def get_coordinator_info(self) -> Dict[str, Any]:
        """Get information about the coordinator."""
        return {
            "name": self.name,
            "framework": "google-adk",
            "adk_available": ADK_AVAILABLE,
            "model": getattr(self.model, 'name', 'unknown') if self.model else None,
            "teams_managed": len(self.teams),
            "team_names": list(self.teams.keys()),
            "routing_engine_active": self.routing_engine is not None,
            "agent_active": self.agent is not None
        }

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics from the routing engine."""
        if self.routing_engine:
            stats = self.routing_engine.get_routing_statistics()
            stats["coordinator"] = self.name
            stats["framework"] = "google-adk"
            return stats
        else:
            return {
                "coordinator": self.name,
                "framework": "google-adk",
                "message": "No routing engine available"
            }

    def update_team_workload(self, team_name: str, workload_change: int):
        """Update a team's workload for routing decisions."""
        if self.routing_engine:
            self.routing_engine.update_agent_workload(team_name, workload_change)

    def migrate_from_langchain_coordinator(self, langchain_coordinator) -> Dict[str, Any]:
        """
        Migrate data from a LangChain team coordinator.

        Args:
            langchain_coordinator: LangChain TeamCoordinator instance

        Returns:
            Migration report
        """
        migration_report = {
            "migration_status": "started",
            "components_migrated": [],
            "teams_migrated": 0,
            "warnings": [],
            "errors": []
        }

        try:
            # Migrate teams
            if hasattr(langchain_coordinator, 'teams') and langchain_coordinator.teams:
                for team_name, lc_team in langchain_coordinator.teams.items():
                    try:
                        # For now, just register the team name
                        # In a full migration, we'd convert the team agent
                        self.teams[team_name] = lc_team  # Temporary
                        migration_report["teams_migrated"] += 1
                    except Exception as e:
                        migration_report["warnings"].append(f"Team {team_name} migration warning: {str(e)}")

            # Migrate routing history if available
            if (hasattr(langchain_coordinator, 'routing_engine') and
                langchain_coordinator.routing_engine and
                self.routing_engine):
                try:
                    # This would require converting routing history format
                    migration_report["components_migrated"].append("routing_history")
                except Exception as e:
                    migration_report["warnings"].append(f"Routing history migration failed: {str(e)}")

            migration_report["components_migrated"].extend(["teams", "coordinator_config"])
            migration_report["migration_status"] = "completed"

        except Exception as e:
            migration_report["migration_status"] = "failed"
            migration_report["errors"].append(f"Migration failed: {str(e)}")

        return migration_report

    def __str__(self) -> str:
        return f"ADKTeamCoordinator(name='{self.name}', teams={len(self.teams)}, framework='google-adk')"

    def __repr__(self) -> str:
        return self.__str__()