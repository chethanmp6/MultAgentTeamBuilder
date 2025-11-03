"""
Main configurable agent class that ties everything together.
"""
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.runnables import Runnable

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from .config_loader import ConfigLoader, AgentConfiguration
from ..tools.tool_registry import ToolRegistry
from ..memory.memory_manager import MemoryManager

# Load environment variables from .env file
load_dotenv()


class ConfigurableAgent:
    """Main configurable agent class."""
    
    def __init__(self, config_file: str):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config(config_file)
        self.tool_registry = ToolRegistry()
        self.memory_manager = None
        self.llm = None
        self.graph = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all agent components."""
        self._setup_llm()
        self._setup_tools()
        self._setup_memory()
        self._setup_graph()
    
    def _setup_llm(self):
        """Initialize the LLM based on configuration using init_chat_model."""
        llm_config = self.config.llm
        
        # Get API key from environment
        api_key = os.getenv(llm_config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {llm_config.api_key_env}")
        
        # Map provider names to init_chat_model format
        provider_mapping = {
            "openai": "openai",
            "anthropic": "anthropic", 
            "gemini": "google_vertexai",  # Google Gemini models
            "groq": "groq"
        }
        
        provider = provider_mapping.get(llm_config.provider.lower())
        if not provider:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")
        
        # Prepare model name with provider prefix
        model_name = f"{provider}:{llm_config.model}"
        
        # Prepare additional kwargs
        llm_kwargs = {
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens,
            "api_key": api_key
        }
        
        # Add base_url if specified
        if llm_config.base_url:
            llm_kwargs["base_url"] = llm_config.base_url
        
        # Initialize LLM using init_chat_model
        try:
            self.llm = init_chat_model(
                model=model_name,
                **llm_kwargs
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize LLM with model {model_name}: {str(e)}")
    
    def _setup_tools(self):
        """Setup tools from configuration."""
        tools_config = self.config.tools
        
        # Register custom tools
        for custom_tool in tools_config.custom:
            self.tool_registry.register_custom_tool(
                name=custom_tool.name,
                module_path=custom_tool.module_path,
                class_name=custom_tool.class_name,
                description=custom_tool.description,
                parameters=custom_tool.parameters
            )
        
        # Validate all required tools exist
        all_tool_names = tools_config.built_in + [t.name for t in tools_config.custom]
        missing_tools = self.tool_registry.validate_tools(all_tool_names)
        if missing_tools:
            raise ValueError(f"Missing tools: {missing_tools}")
    
    def _setup_memory(self):
        """Setup memory management if enabled."""
        if self.config.memory.enabled:
            self.memory_manager = MemoryManager(self.config.memory)
    
    def _setup_graph(self):
        """Setup the LangGraph workflow using prebuilt ReAct agent."""
        # Get all configured tools
        all_tool_names = self.config.tools.built_in + [t.name for t in self.config.tools.custom]
        tools = self.tool_registry.get_tools_by_names(all_tool_names)
        
        # Create system message from configuration
        system_prompt = self.config_loader.get_prompt_template(
            "system_prompt", 
            query="", 
            memory_context="",
            programming_language="", 
            project_context="",
            customer_info="",
            knowledge_base=""
        )
        
        # For Groq models, we need to handle system prompts differently
        if self.config.llm.provider.lower() == "groq":
            # Create the ReAct agent without tools first for Groq
            self.graph = create_react_agent(
                model=self.llm,
                tools=[]  # Start without tools for Groq
            )
        else:
            # Create the ReAct agent with tools for other providers
            self.graph = create_react_agent(
                model=self.llm,
                tools=tools
            )
        
        # Store system prompt and tools for use in run method
        self.system_prompt = system_prompt
        self.available_tools = tools
    
    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run the agent with given input."""
        if not self.graph:
            raise ValueError("Graph not initialized")
        
        # Add memory context if available
        enhanced_input = input_text
        if self.memory_manager:
            memory_context = self.memory_manager.get_relevant_context(input_text)
            if memory_context:
                enhanced_input = f"{input_text}\n\nRelevant context: {memory_context}"
        
        try:
            # Prepare messages with system prompt
            messages = []
            if hasattr(self, 'system_prompt') and self.system_prompt:
                messages.append(SystemMessage(content=self.system_prompt))
            messages.append(HumanMessage(content=enhanced_input))
            
            # Handle Groq differently - use direct LLM call instead of ReAct
            if self.config.llm.provider.lower() == "groq":
                # For Groq, use direct LLM call without tools to avoid function calling issues
                response = self.llm.invoke(messages)
                result = {"messages": [response]}
            else:
                # Run the ReAct agent for other providers
                result = self.graph.invoke({"messages": messages})
            
            # Extract response from ReAct agent result
            messages = result.get("messages", [])
            last_message = messages[-1] if messages else None
            
            if last_message:
                if hasattr(last_message, 'content'):
                    response_text = last_message.content
                else:
                    response_text = last_message.get("content", "No response")
            else:
                response_text = "No response"
            
            # Extract message contents safely
            message_contents = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    message_contents.append(msg.content)
                elif isinstance(msg, dict):
                    message_contents.append(msg.get("content", ""))
                else:
                    message_contents.append(str(msg))
            
            # Store interaction in memory if available
            if self.memory_manager and messages:
                user_msg = messages[0] if messages else HumanMessage(content=input_text)
                ai_response = last_message if last_message else None
                if ai_response:
                    self.memory_manager.store_interaction([user_msg], ai_response)
            
            response = {
                "response": response_text,
                "messages": message_contents,
                "tool_results": self._get_tool_results_for_provider(messages),
                "iteration_count": self._get_iteration_count_for_provider(messages),
                "metadata": kwargs
            }
            
            return response
            
        except Exception as e:
            return {
                "error": str(e),
                "response": f"Error running agent: {str(e)}",
                "messages": [],
                "tool_results": {},
                "iteration_count": 0,
                "metadata": {}
            }
    
    def _extract_tool_results(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """Extract tool results from message history."""
        tool_results = {}
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get('name', 'unknown_tool')
                    tool_results[tool_name] = tool_call.get('args', {})
        return tool_results
    
    def _get_tool_results_for_provider(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """Get tool results based on provider."""
        if self.config.llm.provider.lower() == "groq":
            return {}
        return self._extract_tool_results(messages)
    
    def _get_iteration_count_for_provider(self, messages: List[BaseMessage]) -> int:
        """Get iteration count based on provider."""
        if self.config.llm.provider.lower() == "groq":
            return 0
        return len([m for m in messages if hasattr(m, 'tool_calls') and m.tool_calls])
    
    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Async version of run."""
        if not self.graph:
            raise ValueError("Graph not initialized")
        
        # Add memory context if available
        enhanced_input = input_text
        if self.memory_manager:
            memory_context = self.memory_manager.get_relevant_context(input_text)
            if memory_context:
                enhanced_input = f"{input_text}\n\nRelevant context: {memory_context}"
        
        try:
            # Prepare messages with system prompt
            messages = []
            if hasattr(self, 'system_prompt') and self.system_prompt:
                messages.append(SystemMessage(content=self.system_prompt))
            messages.append(HumanMessage(content=enhanced_input))
            
            # Handle Groq differently - use direct LLM call instead of ReAct
            if self.config.llm.provider.lower() == "groq":
                # For Groq, use direct LLM call without tools to avoid function calling issues
                response = await self.llm.ainvoke(messages)
                result = {"messages": [response]}
            else:
                # Run the ReAct agent asynchronously for other providers
                result = await self.graph.ainvoke({"messages": messages})
            
            # Extract response from ReAct agent result
            messages = result.get("messages", [])
            last_message = messages[-1] if messages else None
            
            if last_message:
                if hasattr(last_message, 'content'):
                    response_text = last_message.content
                else:
                    response_text = last_message.get("content", "No response")
            else:
                response_text = "No response"
            
            # Extract message contents safely
            message_contents = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    message_contents.append(msg.content)
                elif isinstance(msg, dict):
                    message_contents.append(msg.get("content", ""))
                else:
                    message_contents.append(str(msg))
            
            # Store interaction in memory if available
            if self.memory_manager and messages:
                user_msg = messages[0] if messages else HumanMessage(content=input_text)
                ai_response = last_message if last_message else None
                if ai_response:
                    self.memory_manager.store_interaction([user_msg], ai_response)
            
            response = {
                "response": response_text,
                "messages": message_contents,
                "tool_results": self._get_tool_results_for_provider(messages),
                "iteration_count": self._get_iteration_count_for_provider(messages),
                "metadata": kwargs
            }
            
            return response
            
        except Exception as e:
            return {
                "error": str(e),
                "response": f"Error running agent: {str(e)}",
                "messages": [],
                "tool_results": {},
                "iteration_count": 0,
                "metadata": {}
            }
    
    def get_prompt_template(self, prompt_type: str, **variables) -> str:
        """Get a formatted prompt template."""
        return self.config_loader.get_prompt_template(prompt_type, **variables)
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools."""
        return self.tool_registry.list_all_tools()
    
    def get_config(self) -> AgentConfiguration:
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
    
    def reload_config(self, config_file: str = None):
        """Reload configuration and reinitialize components."""
        if config_file:
            self.config = self.config_loader.load_config(config_file)
        self._initialize_components()
    
    def export_conversation(self, format_type: str = "json") -> str:
        """Export conversation history."""
        if not self.memory_manager:
            return "Memory not enabled"
        
        return self.memory_manager.export_history(format_type)
    
    def clear_memory(self):
        """Clear agent memory."""
        if self.memory_manager:
            self.memory_manager.clear_memory()