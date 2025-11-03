"""
ADK-based worker agent for hierarchical teams.
Migrated from LangChain-based worker_agent.py to Google ADK.
"""
from typing import Dict, Any, List, Optional

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
            return {"response": f"Mock worker response to: {input_text}"}

    class Model:
        def __init__(self, name: str = "gemini-1.5-flash"):
            self.name = name

    class Message:
        def __init__(self, content: str, role: str = "user"):
            self.content = content
            self.role = role

    ADK_AVAILABLE = False

from ..configurable_agent_adk import ADKConfigurableAgent


class ADKWorkerAgent:
    """ADK-based worker agent for specialized tasks in hierarchical teams."""

    def __init__(self,
                 name: str = "adk_worker",
                 config_file: str = None,
                 config_data: Dict[str, Any] = None,
                 adk_agent: Agent = None,
                 specialization: str = None):
        """
        Initialize ADK worker agent.

        Args:
            name: Worker name
            config_file: Path to configuration file (optional)
            config_data: Configuration dictionary (optional)
            adk_agent: Pre-configured ADK agent (optional)
            specialization: Worker specialization (optional)
        """
        self.name = name
        self.specialization = specialization or "general"
        self.description = f"ADK worker agent specialized in {self.specialization}"
        self.agent = None
        self.configurable_agent = None

        # Initialize worker agent
        if config_file:
            # Create from configuration file
            self.configurable_agent = ADKConfigurableAgent(config_file=config_file)
            self.agent = self.configurable_agent.agent
            self.description = self.configurable_agent.config.agent.description
        elif config_data:
            # Create from configuration data
            self.configurable_agent = ADKConfigurableAgent(config_data=config_data)
            self.agent = self.configurable_agent.agent
            self.description = self.configurable_agent.config.agent.description
        elif adk_agent:
            # Use pre-configured agent
            self.agent = adk_agent
        else:
            # Create default agent
            self._create_default_agent()

    def _create_default_agent(self):
        """Create default worker agent."""
        instructions = f"""You are a Worker Agent named {self.name} specialized in {self.specialization}.

Your role is to:
1. Execute specific tasks assigned by your supervisor
2. Use your specialized capabilities to complete tasks efficiently
3. Provide detailed results and status updates
4. Request clarification if task requirements are unclear
5. Escalate issues that are beyond your capabilities

Specialization: {self.specialization}
Focus on providing accurate, detailed responses within your area of expertise."""

        try:
            if ADK_AVAILABLE:
                default_model = Model(name="gemini-1.5-flash", temperature=0.1)
                self.agent = Agent(
                    name=self.name,
                    instructions=instructions,
                    model=default_model
                )
            else:
                self.agent = Agent(name=self.name)
        except Exception as e:
            print(f"Warning: Failed to create default worker agent: {str(e)}")
            self.agent = Agent(name=self.name)

    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task using the ADK worker agent.

        Args:
            input_text: Task description or input
            **kwargs: Additional parameters

        Returns:
            Dictionary with worker response and metadata
        """
        if not self.agent:
            return {
                "error": "Worker agent not initialized",
                "response": "Worker agent is not available",
                "worker": self.name,
                "framework": "google-adk"
            }

        try:
            # Execute task using ADK agent
            if ADK_AVAILABLE:
                result = self.agent.run(input_text, **kwargs)
            else:
                # Fallback execution
                result = {
                    "response": f"ADK Worker ({self.name}) specialized in {self.specialization} response to: {input_text}",
                    "status": "success"
                }

            # Extract response
            if isinstance(result, dict):
                response_text = result.get("response", str(result))
                messages = result.get("messages", [])
            else:
                response_text = str(result)
                messages = []

            # Build comprehensive response
            worker_response = {
                "response": response_text,
                "worker": self.name,
                "specialization": self.specialization,
                "framework": "google-adk",
                "messages": messages,
                "status": "completed",
                "metadata": {
                    "adk_available": ADK_AVAILABLE,
                    "task_input": input_text,
                    **kwargs
                }
            }

            # Add configurable agent info if available
            if self.configurable_agent:
                worker_response["metadata"].update({
                    "tools_available": len(self.configurable_agent.get_available_tools()),
                    "memory_enabled": self.configurable_agent.config.memory.enabled,
                    "model_used": self.configurable_agent.config.llm.model
                })

            return worker_response

        except Exception as e:
            return {
                "error": str(e),
                "response": f"Worker error: {str(e)}",
                "worker": self.name,
                "specialization": self.specialization,
                "framework": "google-adk",
                "status": "failed",
                "metadata": {
                    "error_type": type(e).__name__,
                    **kwargs
                }
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get worker capabilities and specialization information."""
        capabilities = {
            "specialization": self.specialization,
            "capabilities": [self.specialization],  # Default capability
            "keywords": [self.specialization],
            "priority": 1,
            "framework": "google-adk"
        }

        # Get additional capabilities from configurable agent if available
        if self.configurable_agent:
            try:
                agent_config = self.configurable_agent.config

                # Extract capabilities from agent configuration
                if hasattr(agent_config, 'tools'):
                    tools = agent_config.tools
                    capabilities["tools"] = tools.built_in + [t.name for t in tools.custom]

                # Extract capabilities from specialization config if available
                if hasattr(agent_config, 'specialization'):
                    spec_config = agent_config.specialization
                    if hasattr(spec_config, 'capabilities'):
                        capabilities["capabilities"] = spec_config.capabilities
                    if hasattr(spec_config, 'keywords'):
                        capabilities["keywords"] = spec_config.keywords
                    if hasattr(spec_config, 'priority'):
                        capabilities["priority"] = spec_config.priority

            except Exception as e:
                print(f"Warning: Could not extract capabilities for worker {self.name}: {str(e)}")

        return capabilities

    def get_available_tools(self) -> Dict[str, str]:
        """Get available tools for this worker."""
        if self.configurable_agent:
            return self.configurable_agent.get_available_tools()
        return {}

    def get_config(self) -> Optional[Any]:
        """Get the worker's configuration."""
        if self.configurable_agent:
            return self.configurable_agent.get_config()
        return None

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        if self.configurable_agent:
            return self.configurable_agent.get_memory_stats()
        return {"memory_enabled": False}

    def clear_memory(self):
        """Clear worker memory."""
        if self.configurable_agent:
            self.configurable_agent.clear_memory()

    def update_specialization(self, new_specialization: str):
        """Update worker specialization."""
        self.specialization = new_specialization
        self.description = f"ADK worker agent specialized in {self.specialization}"

        # Update agent instructions if using default agent
        if self.agent and not self.configurable_agent:
            self._create_default_agent()

    def get_worker_info(self) -> Dict[str, Any]:
        """Get comprehensive information about this worker."""
        info = {
            "name": self.name,
            "description": self.description,
            "specialization": self.specialization,
            "framework": "google-adk",
            "adk_available": ADK_AVAILABLE,
            "agent_active": self.agent is not None,
            "configurable_agent_active": self.configurable_agent is not None
        }

        # Add configuration info if available
        if self.configurable_agent:
            agent_info = self.configurable_agent.get_adk_agent_info()
            info.update({
                "model": agent_info.get("model"),
                "tools_count": agent_info.get("tools_count"),
                "memory_enabled": agent_info.get("memory_enabled"),
                "workflow_type": agent_info.get("workflow_type")
            })

        return info

    def migrate_from_langchain_worker(self, langchain_worker) -> Dict[str, Any]:
        """
        Migrate data from a LangChain worker agent.

        Args:
            langchain_worker: LangChain WorkerAgent instance

        Returns:
            Migration report
        """
        migration_report = {
            "migration_status": "started",
            "components_migrated": [],
            "warnings": [],
            "errors": []
        }

        try:
            # Migrate basic properties
            if hasattr(langchain_worker, 'name'):
                self.name = langchain_worker.name
                migration_report["components_migrated"].append("name")

            if hasattr(langchain_worker, 'description'):
                self.description = langchain_worker.description
                migration_report["components_migrated"].append("description")

            # Migrate memory if both have memory
            if (hasattr(langchain_worker, 'memory_manager') and
                langchain_worker.memory_manager and
                self.configurable_agent and
                self.configurable_agent.memory_manager):

                try:
                    # Export memory from LangChain worker
                    lc_memory = langchain_worker.export_conversation("json")
                    # Import into ADK worker
                    self.configurable_agent.memory_manager.import_history(lc_memory, "json")
                    migration_report["components_migrated"].append("memory")
                except Exception as e:
                    migration_report["warnings"].append(f"Memory migration failed: {str(e)}")

            # Migrate tool configurations
            try:
                if hasattr(langchain_worker, 'get_available_tools'):
                    lc_tools = langchain_worker.get_available_tools()
                    if self.configurable_agent:
                        adk_tools = self.configurable_agent.get_available_tools()
                        migrated_tools = set(lc_tools.keys()).intersection(set(adk_tools.keys()))
                        migration_report["components_migrated"].append(f"tools ({len(migrated_tools)} common)")

                        if len(migrated_tools) < len(lc_tools):
                            missing_tools = set(lc_tools.keys()) - set(adk_tools.keys())
                            migration_report["warnings"].append(f"Tools not migrated: {list(missing_tools)}")

            except Exception as e:
                migration_report["errors"].append(f"Tool migration failed: {str(e)}")

            migration_report["migration_status"] = "completed"

        except Exception as e:
            migration_report["migration_status"] = "failed"
            migration_report["errors"].append(f"Migration failed: {str(e)}")

        return migration_report

    def __str__(self) -> str:
        return f"ADKWorkerAgent(name='{self.name}', specialization='{self.specialization}', framework='google-adk')"

    def __repr__(self) -> str:
        return self.__str__()