"""
ADK-based configurable agent implementation.
Migrated from LangChain/LangGraph-based configurable_agent.py to Google ADK.
"""
import os
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

# ADK imports (with fallback for development)
try:
    from google_adk import Agent
    from google_adk.models import Model
    from google_adk.tools import Tool
    from google_adk.memory import SessionMemory
    from google_adk.core import Message
    ADK_AVAILABLE = True
except ImportError:
    # Fallback for development/testing
    print("Warning: Google ADK not available. Using mock implementations.")

    class Agent:
        def __init__(self, name: str, instructions: str, model=None, tools=None, **kwargs):
            self.name = name
            self.instructions = instructions
            self.model = model
            self.tools = tools or []

        def run(self, input_text: str, **kwargs):
            return {
                "response": f"Mock ADK response to: {input_text}",
                "messages": [{"role": "user", "content": input_text}],
                "status": "success"
            }

    class Model:
        def __init__(self, name: str = "gemini-1.5-flash", **kwargs):
            self.name = name

    class Message:
        def __init__(self, content: str, role: str = "user"):
            self.content = content
            self.role = role

    ADK_AVAILABLE = False

# Try Google AI imports
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

from .config_loader_adk import ADKConfigLoader, ADKAgentConfiguration
from .tool_registry_adk import ADKToolRegistry
from .memory_manager_adk import ADKMemoryManager

# Load environment variables from .env file
load_dotenv()


class ADKConfigurableAgent:
    """ADK-based configurable agent class."""

    def __init__(self, config_file: str = None, config_data: Dict[str, Any] = None):
        """
        Initialize ADK agent from configuration.

        Args:
            config_file: Path to YAML configuration file
            config_data: Direct configuration dictionary
        """
        self.config_loader = ADKConfigLoader()
        self.config = None
        self.tool_registry = ADKToolRegistry()
        self.memory_manager = None
        self.model = None
        self.agent = None

        # Load configuration
        if config_file:
            self.config = self.config_loader.load_config(config_file)
        elif config_data:
            # Convert and validate config data
            self.config = ADKAgentConfiguration(**config_data)
        else:
            raise ValueError("Either config_file or config_data must be provided")

        self._initialize_components()

    def _initialize_components(self):
        """Initialize all ADK agent components."""
        self._setup_model()
        self._setup_tools()
        self._setup_memory()
        self._setup_agent()

    def _setup_model(self):
        """Initialize the ADK model based on configuration."""
        llm_config = self.config.llm

        # Get API key from environment
        api_key = os.getenv(llm_config.api_key_env)
        if not api_key:
            print(f"Warning: API key not found in environment variable: {llm_config.api_key_env}")

        # Configure Google AI if available
        if GOOGLE_AI_AVAILABLE and api_key:
            genai.configure(api_key=api_key)

        # Create ADK model
        model_params = {
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens
        }

        if llm_config.project_id:
            model_params["project_id"] = llm_config.project_id

        if llm_config.location:
            model_params["location"] = llm_config.location

        try:
            if ADK_AVAILABLE:
                self.model = Model(name=llm_config.model, **model_params)
            else:
                # Fallback model
                self.model = Model(name=llm_config.model, **model_params)
        except Exception as e:
            print(f"Warning: Failed to initialize model {llm_config.model}: {str(e)}")
            # Fallback to default model
            self.model = Model(name="gemini-1.5-flash")

    def _setup_tools(self):
        """Setup tools from configuration."""
        tools_config = self.config.tools

        # Register custom tools
        for custom_tool in tools_config.custom:
            self.tool_registry.register_custom_tool(
                name=custom_tool.name,
                function_name=custom_tool.function_name,
                description=custom_tool.description,
                module_path=custom_tool.module_path,
                parameters=custom_tool.parameters
            )

        # Validate all required tools exist
        all_tool_names = tools_config.built_in + [t.name for t in tools_config.custom]
        missing_tools = self.tool_registry.validate_tools(all_tool_names)
        if missing_tools:
            print(f"Warning: Missing tools: {missing_tools}")

    def _setup_memory(self):
        """Setup memory management if enabled."""
        if self.config.memory.enabled:
            self.memory_manager = ADKMemoryManager(self.config.memory)

    def _setup_agent(self):
        """Setup the ADK agent with model, tools, and instructions."""
        # Get all configured tools in ADK format
        all_tool_names = self.config.tools.built_in + [t.name for t in self.config.tools.custom]
        tools = self.tool_registry.get_adk_tools_for_agent(all_tool_names)

        # Create system instructions from configuration
        system_instructions = self.config_loader.get_prompt_template(
            "system_prompt",
            query="",
            memory_context="",
            programming_language="",
            project_context="",
            customer_info="",
            knowledge_base=""
        )

        try:
            if ADK_AVAILABLE:
                # Create ADK agent
                self.agent = Agent(
                    name=self.config.agent.name,
                    instructions=system_instructions,
                    model=self.model,
                    tools=tools,
                    memory=self.memory_manager.session_memory if self.memory_manager else None
                )
            else:
                # Fallback agent
                self.agent = Agent(
                    name=self.config.agent.name,
                    instructions=system_instructions,
                    model=self.model,
                    tools=tools
                )

        except Exception as e:
            print(f"Warning: Failed to create ADK agent: {str(e)}")
            # Create fallback agent
            self.agent = Agent(
                name=self.config.agent.name,
                instructions=system_instructions,
                model=self.model,
                tools=[]
            )

    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Run the ADK agent with given input.

        Args:
            input_text: Input text for the agent
            **kwargs: Additional parameters

        Returns:
            Dictionary with agent response and metadata
        """
        if not self.agent:
            raise ValueError("Agent not initialized")

        # Add memory context if available
        enhanced_input = input_text
        if self.memory_manager:
            memory_context = self.memory_manager.get_relevant_context(input_text)
            if memory_context:
                enhanced_input = f"{input_text}\n\nRelevant context: {memory_context}"

        try:
            # Create ADK message
            if ADK_AVAILABLE:
                input_message = Message(content=enhanced_input, role="user")
            else:
                input_message = {"content": enhanced_input, "role": "user"}

            # Run the ADK agent
            if ADK_AVAILABLE:
                result = self.agent.run(enhanced_input, **kwargs)
            else:
                # Fallback execution
                result = {
                    "response": f"ADK Agent ({self.config.agent.name}) response to: {enhanced_input}",
                    "status": "success",
                    "model_used": self.config.llm.model,
                    "tools_available": len(self.tool_registry.get_built_in_tools())
                }

            # Extract response
            if isinstance(result, dict):
                response_text = result.get("response", "No response")
                messages = result.get("messages", [])
            else:
                response_text = str(result)
                messages = [{"role": "assistant", "content": response_text}]

            # Store interaction in memory if available
            if self.memory_manager:
                input_msg = input_message if ADK_AVAILABLE else {"content": input_text, "role": "user"}
                response_msg = {"content": response_text, "role": "assistant"}
                self.memory_manager.store_interaction([input_msg], response_msg)

            # Build response
            response = {
                "response": response_text,
                "messages": messages,
                "agent_name": self.config.agent.name,
                "model_used": self.config.llm.model,
                "framework": "google-adk",
                "tools_used": self._extract_tools_used(result),
                "memory_enabled": self.config.memory.enabled,
                "metadata": {
                    **kwargs,
                    "adk_available": ADK_AVAILABLE,
                    "workflow_type": self.config.workflow.workflow_type
                }
            }

            return response

        except Exception as e:
            return {
                "error": str(e),
                "response": f"Error running ADK agent: {str(e)}",
                "agent_name": self.config.agent.name,
                "framework": "google-adk",
                "messages": [],
                "tools_used": [],
                "metadata": {
                    "error_type": type(e).__name__,
                    **kwargs
                }
            }

    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Async version of run (currently delegates to sync version).

        Args:
            input_text: Input text for the agent
            **kwargs: Additional parameters

        Returns:
            Dictionary with agent response and metadata
        """
        # For now, delegate to sync version
        # In production, this would use ADK's async capabilities
        return self.run(input_text, **kwargs)

    def _extract_tools_used(self, result: Any) -> List[str]:
        """Extract list of tools used from agent result."""
        if isinstance(result, dict):
            return result.get("tools_used", [])
        return []

    def get_prompt_template(self, prompt_type: str, **variables) -> str:
        """Get a formatted prompt template."""
        return self.config_loader.get_prompt_template(prompt_type, **variables)

    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools."""
        return self.tool_registry.list_all_tools()

    def get_config(self) -> ADKAgentConfiguration:
        """Get the loaded configuration."""
        return self.config

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        if self.memory_manager:
            return self.memory_manager.get_stats()
        return {"memory_enabled": False}

    def update_prompts(self, prompt_updates: Dict[str, str]):
        """Update prompt templates dynamically."""
        for prompt_type, new_template in prompt_updates.items():
            if hasattr(self.config.prompts, prompt_type):
                getattr(self.config.prompts, prompt_type).template = new_template

        # Reinitialize agent with new prompts
        self._setup_agent()

    def reload_config(self, config_file: str = None, config_data: Dict[str, Any] = None):
        """Reload configuration and reinitialize components."""
        if config_file:
            self.config = self.config_loader.load_config(config_file)
        elif config_data:
            self.config = ADKAgentConfiguration(**config_data)

        self._initialize_components()

    def export_conversation(self, format_type: str = "json") -> str:
        """Export conversation history."""
        if not self.memory_manager:
            return json.dumps({"error": "Memory not enabled"})

        return self.memory_manager.export_history(format_type)

    def clear_memory(self):
        """Clear agent memory."""
        if self.memory_manager:
            self.memory_manager.clear_memory()

    def get_adk_agent_info(self) -> Dict[str, Any]:
        """Get information about the ADK agent."""
        return {
            "agent_name": self.config.agent.name,
            "agent_description": self.config.agent.description,
            "framework": "google-adk",
            "adk_available": ADK_AVAILABLE,
            "google_ai_available": GOOGLE_AI_AVAILABLE,
            "model": self.config.llm.model,
            "provider": self.config.llm.provider,
            "tools_count": len(self.get_available_tools()),
            "memory_enabled": self.config.memory.enabled,
            "workflow_type": self.config.workflow.workflow_type,
            "max_iterations": self.config.workflow.max_iterations,
            "timeout_seconds": self.config.workflow.timeout_seconds
        }

    def migrate_from_langchain_agent(self, langchain_agent) -> Dict[str, Any]:
        """
        Migrate data from a LangChain agent to this ADK agent.

        Args:
            langchain_agent: The LangChain ConfigurableAgent instance

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
            # Migrate memory if both have memory enabled
            if (hasattr(langchain_agent, 'memory_manager') and
                langchain_agent.memory_manager and
                self.memory_manager):

                # Export memory from LangChain agent
                lc_memory = langchain_agent.export_conversation("json")

                # Import into ADK agent (with format conversion)
                try:
                    self.memory_manager.import_history(lc_memory, "json")
                    migration_report["components_migrated"].append("memory")
                except Exception as e:
                    migration_report["warnings"].append(f"Memory migration failed: {str(e)}")

            # Migrate tool configurations
            try:
                lc_tools = langchain_agent.get_available_tools()
                adk_tools = self.get_available_tools()

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
        return f"ADKConfigurableAgent(name='{self.config.agent.name}', model='{self.config.llm.model}', framework='google-adk')"

    def __repr__(self) -> str:
        return self.__str__()