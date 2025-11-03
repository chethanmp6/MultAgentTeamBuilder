"""
ADK-based supervisor agent for hierarchical teams.
Migrated from LangChain-based supervisor.py to Google ADK.
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
            return {"response": f"Mock supervisor response to: {input_text}"}

    class Model:
        def __init__(self, name: str = "gemini-1.5-flash"):
            self.name = name

    class Message:
        def __init__(self, content: str, role: str = "user"):
            self.content = content
            self.role = role

    ADK_AVAILABLE = False

from ..configurable_agent_adk import ADKConfigurableAgent
from .worker_agent_adk import ADKWorkerAgent
from .enhanced_routing_adk import ADKEnhancedRoutingEngine, ADKRoutingStrategy, ADKAgentCapability


class ADKSupervisorAgent:
    """ADK-based supervisor agent for managing worker agents in a team."""

    def __init__(self,
                 name: str = "adk_supervisor",
                 config_file: str = None,
                 coordinator_model: Model = None,
                 adk_agent: Agent = None):
        """
        Initialize ADK supervisor agent.

        Args:
            name: Supervisor name
            config_file: Path to configuration file (optional)
            coordinator_model: Model from coordinator (optional)
            adk_agent: Pre-configured ADK agent (optional)
        """
        self.name = name
        self.workers: List[ADKWorkerAgent] = []
        self.routing_engine = None
        self.agent = None
        self.model = coordinator_model

        # Initialize supervisor agent
        if config_file:
            # Create from configuration file
            self.configurable_agent = ADKConfigurableAgent(config_file=config_file)
            self.agent = self.configurable_agent.agent
            self.model = self.configurable_agent.model
        elif adk_agent:
            # Use pre-configured agent
            self.agent = adk_agent
        elif coordinator_model:
            # Create agent with coordinator's model
            self._create_agent_with_model(coordinator_model)
        else:
            # Create default agent
            self._create_default_agent()

        # Initialize routing engine
        self._setup_routing_engine()

    def _create_agent_with_model(self, model: Model):
        """Create supervisor agent with specified model."""
        instructions = f"""You are a Team Supervisor named {self.name} managing a team of specialized worker agents. Your responsibilities include:

1. Analyzing incoming tasks and determining which worker is best suited to handle them
2. Delegating tasks to the appropriate worker based on their capabilities and current workload
3. Coordinating between workers when tasks require collaboration
4. Aggregating and summarizing results from multiple workers
5. Escalating complex issues that require coordinator intervention

When delegating tasks, consider:
- Worker specializations and capabilities
- Current worker availability and workload
- Task complexity and requirements
- Worker performance history

Always provide clear instructions to workers and explain your delegation decisions."""

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
            print(f"Warning: Failed to create supervisor agent: {str(e)}")
            self.agent = Agent(name=self.name)

    def _create_default_agent(self):
        """Create default supervisor agent."""
        try:
            if ADK_AVAILABLE:
                default_model = Model(name="gemini-1.5-flash", temperature=0.2)
                self._create_agent_with_model(default_model)
                self.model = default_model
            else:
                self.agent = Agent(name=self.name)
                self.model = Model(name="gemini-1.5-flash")
        except Exception as e:
            print(f"Warning: Failed to create default supervisor: {str(e)}")
            self.agent = Agent(name=self.name)
            self.model = Model(name="gemini-1.5-flash")

    def _setup_routing_engine(self):
        """Setup the routing engine for worker selection."""
        try:
            self.routing_engine = ADKEnhancedRoutingEngine(
                routing_agent=self.agent,
                default_strategy=ADKRoutingStrategy.CAPABILITY_BASED
            )
        except Exception as e:
            print(f"Warning: Failed to setup routing engine: {str(e)}")
            self.routing_engine = ADKEnhancedRoutingEngine(
                default_strategy=ADKRoutingStrategy.KEYWORD_BASED
            )

    def add_worker(self, worker: ADKWorkerAgent):
        """
        Add a worker to this supervisor's team.

        Args:
            worker: ADKWorkerAgent to add to the team
        """
        self.workers.append(worker)

        # Register worker capabilities with routing engine
        if self.routing_engine:
            try:
                capabilities = worker.get_capabilities()
                agent_capability = ADKAgentCapability(
                    agent_id=worker.name,
                    capabilities=capabilities.get('capabilities', []),
                    specialization_keywords=capabilities.get('keywords', []),
                    priority=capabilities.get('priority', 1),
                    adk_agent=worker.agent if hasattr(worker, 'agent') else None
                )
                self.routing_engine.register_agent(agent_capability)
            except Exception as e:
                print(f"Warning: Failed to register worker {worker.name}: {str(e)}")

    def remove_worker(self, worker_name: str) -> bool:
        """
        Remove a worker from this supervisor's team.

        Args:
            worker_name: Name of the worker to remove

        Returns:
            True if worker was removed, False if not found
        """
        for i, worker in enumerate(self.workers):
            if worker.name == worker_name:
                self.workers.pop(i)
                return True
        return False

    def get_worker(self, worker_name: str) -> Optional[ADKWorkerAgent]:
        """Get a worker by name."""
        for worker in self.workers:
            if worker.name == worker_name:
                return worker
        return None

    def delegate_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Delegate a task to the most appropriate worker.

        Args:
            task_description: Description of the task
            context: Additional context for delegation

        Returns:
            Dictionary with delegation decision and metadata
        """
        if not self.workers:
            return {
                "error": "No workers available",
                "target_worker": None,
                "reasoning": "No workers in this team"
            }

        available_workers = [w.name for w in self.workers]
        context = context or {}

        try:
            if self.routing_engine:
                decision = self.routing_engine.route_task(
                    task_description=task_description,
                    available_agents=available_workers,
                    context=context
                )

                return {
                    "target_worker": decision.target,
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning,
                    "strategy": decision.strategy_used.value,
                    "alternatives": decision.alternative_targets,
                    "metadata": decision.metadata
                }
            else:
                # Fallback to simple delegation
                target_worker = available_workers[0]
                return {
                    "target_worker": target_worker,
                    "confidence": 0.5,
                    "reasoning": "Fallback delegation - using first available worker",
                    "strategy": "fallback"
                }

        except Exception as e:
            return {
                "error": str(e),
                "target_worker": available_workers[0] if available_workers else None,
                "reasoning": f"Error in delegation: {str(e)}"
            }

    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Process input through the supervisor and delegate to appropriate worker.

        Args:
            input_text: Input text to process
            **kwargs: Additional parameters

        Returns:
            Dictionary with supervisor response and metadata
        """
        if not self.workers:
            return {
                "error": "No workers available",
                "response": "No workers assigned to this supervisor",
                "supervisor": self.name,
                "framework": "google-adk"
            }

        try:
            # Delegate the task
            delegation_result = self.delegate_task(input_text, kwargs)

            if "error" in delegation_result:
                return {
                    "error": delegation_result["error"],
                    "response": f"Delegation failed: {delegation_result['error']}",
                    "supervisor": self.name,
                    "framework": "google-adk"
                }

            target_worker_name = delegation_result["target_worker"]
            target_worker = self.get_worker(target_worker_name)

            if not target_worker:
                return {
                    "error": f"Target worker '{target_worker_name}' not found",
                    "response": f"Worker '{target_worker_name}' is not available",
                    "supervisor": self.name,
                    "framework": "google-adk"
                }

            # Execute task on target worker
            worker_result = target_worker.run(input_text, **kwargs)

            # Update routing engine performance metrics if available
            if self.routing_engine:
                try:
                    success = not ("error" in worker_result)
                    response_time = kwargs.get("response_time", 1.0)
                    self.routing_engine.update_agent_performance(
                        target_worker_name, response_time, success
                    )
                except Exception as e:
                    print(f"Warning: Failed to update performance metrics: {str(e)}")

            # Build comprehensive response
            response = {
                "response": worker_result.get("response", str(worker_result)),
                "supervisor": self.name,
                "framework": "google-adk",
                "delegation": {
                    "target_worker": target_worker_name,
                    "confidence": delegation_result.get("confidence", 0.5),
                    "reasoning": delegation_result.get("reasoning", "Worker selected"),
                    "strategy": delegation_result.get("strategy", "unknown")
                },
                "worker_result": worker_result,
                "metadata": {
                    "total_workers": len(self.workers),
                    "available_workers": [w.name for w in self.workers],
                    "adk_available": ADK_AVAILABLE,
                    **kwargs
                }
            }

            return response

        except Exception as e:
            return {
                "error": str(e),
                "response": f"Supervisor error: {str(e)}",
                "supervisor": self.name,
                "framework": "google-adk",
                "metadata": kwargs
            }

    def get_team_info(self) -> Dict[str, Any]:
        """Get information about this supervisor's team."""
        return {
            "supervisor": self.name,
            "framework": "google-adk",
            "worker_count": len(self.workers),
            "workers": [
                {
                    "name": w.name,
                    "description": w.description,
                    "capabilities": w.get_capabilities() if hasattr(w, 'get_capabilities') else []
                }
                for w in self.workers
            ],
            "routing_engine_active": self.routing_engine is not None,
            "adk_available": ADK_AVAILABLE
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get combined capabilities of all workers in this team."""
        all_capabilities = set()
        all_keywords = set()
        max_priority = 1

        for worker in self.workers:
            try:
                worker_caps = worker.get_capabilities()
                all_capabilities.update(worker_caps.get('capabilities', []))
                all_keywords.update(worker_caps.get('keywords', []))
                max_priority = max(max_priority, worker_caps.get('priority', 1))
            except Exception as e:
                print(f"Warning: Could not get capabilities for worker {worker.name}: {str(e)}")

        return {
            "capabilities": list(all_capabilities),
            "keywords": list(all_keywords),
            "priority": max_priority,
            "worker_count": len(self.workers)
        }

    def list_workers(self) -> List[Dict[str, Any]]:
        """List all workers with their information."""
        return [
            {
                "name": worker.name,
                "description": worker.description,
                "framework": "google-adk",
                "capabilities": worker.get_capabilities() if hasattr(worker, 'get_capabilities') else {},
                "available": True
            }
            for worker in self.workers
        ]

    def get_delegation_statistics(self) -> Dict[str, Any]:
        """Get delegation statistics from the routing engine."""
        if self.routing_engine:
            stats = self.routing_engine.get_routing_statistics()
            stats["supervisor"] = self.name
            stats["framework"] = "google-adk"
            return stats
        else:
            return {
                "supervisor": self.name,
                "framework": "google-adk",
                "message": "No routing engine available"
            }

    def update_worker_workload(self, worker_name: str, workload_change: int):
        """Update a worker's workload for delegation decisions."""
        if self.routing_engine:
            self.routing_engine.update_agent_workload(worker_name, workload_change)

    def migrate_from_langchain_supervisor(self, langchain_supervisor) -> Dict[str, Any]:
        """
        Migrate data from a LangChain supervisor agent.

        Args:
            langchain_supervisor: LangChain SupervisorAgent instance

        Returns:
            Migration report
        """
        migration_report = {
            "migration_status": "started",
            "components_migrated": [],
            "workers_migrated": 0,
            "warnings": [],
            "errors": []
        }

        try:
            # Migrate workers
            if hasattr(langchain_supervisor, 'workers') and langchain_supervisor.workers:
                for lc_worker in langchain_supervisor.workers:
                    try:
                        # Create ADK worker from LangChain worker
                        adk_worker = ADKWorkerAgent(name=lc_worker.name)

                        # Try to migrate worker configuration
                        if hasattr(lc_worker, 'get_config'):
                            # This would require config conversion
                            pass

                        self.add_worker(adk_worker)
                        migration_report["workers_migrated"] += 1

                    except Exception as e:
                        migration_report["warnings"].append(f"Worker {lc_worker.name} migration failed: {str(e)}")

            migration_report["components_migrated"].extend(["workers", "supervisor_config"])
            migration_report["migration_status"] = "completed"

        except Exception as e:
            migration_report["migration_status"] = "failed"
            migration_report["errors"].append(f"Migration failed: {str(e)}")

        return migration_report

    def __str__(self) -> str:
        return f"ADKSupervisorAgent(name='{self.name}', workers={len(self.workers)}, framework='google-adk')"

    def __repr__(self) -> str:
        return self.__str__()