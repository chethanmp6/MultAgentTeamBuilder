"""
Worker Agent for Hierarchical Agent Teams
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from ..core.configurable_agent import ConfigurableAgent
from ..core.config_loader import AgentConfiguration


class WorkerAgent:
    """A worker agent that can be part of a hierarchical team."""
    
    def __init__(self, 
                 name: str,
                 config_file: str = None,
                 config_data: Dict[str, Any] = None,
                 llm: BaseChatModel = None,
                 tools: List[BaseTool] = None,
                 system_prompt: str = None,
                 description: str = None):
        """
        Initialize a worker agent.
        
        Args:
            name: Name of the worker agent
            config_file: Path to configuration file (optional)
            config_data: Configuration data dictionary (optional)
            llm: Language model to use (optional)
            tools: List of tools available to the agent (optional)
            system_prompt: System prompt for the agent (optional)
            description: Description of the agent's role (optional)
        """
        self.name = name
        self.description = description or f"Worker agent: {name}"
        
        # Initialize from config file if provided
        if config_file:
            self.agent = ConfigurableAgent(config_file)
            self.llm = self.agent.llm
            self.tools = self.agent.available_tools
            self.system_prompt = self.agent.system_prompt
        elif config_data:
            # Initialize from embedded config data
            # For now, create a temporary config file and use ConfigurableAgent
            # In a future version, we could modify ConfigurableAgent to accept dict directly
            import tempfile
            import yaml
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                yaml.dump(config_data, f)
                temp_config_file = f.name
            
            try:
                self.agent = ConfigurableAgent(temp_config_file)
                self.llm = self.agent.llm
                self.tools = self.agent.available_tools
                self.system_prompt = self.agent.system_prompt
            finally:
                # Clean up temporary file
                import os
                os.unlink(temp_config_file)
        else:
            # Initialize with provided components
            self.agent = None
            self.llm = llm
            self.tools = tools or []
            self.system_prompt = system_prompt or f"You are {name}, a specialized worker agent."
    
    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run the worker agent with given input."""
        if self.agent:
            # Use the configurable agent if available
            return self.agent.run(input_text, **kwargs)
        else:
            # Use direct LLM call with tools
            return self._run_direct(input_text, **kwargs)
    
    def _run_direct(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run agent directly with LLM and tools."""
        if not self.llm:
            raise ValueError("No LLM configured for worker agent")
        
        # Prepare messages
        messages = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        messages.append(HumanMessage(content=input_text))
        
        try:
            # Run with tools if available
            if self.tools:
                # Simple tool calling (for basic implementation)
                response = self.llm.invoke(messages)
            else:
                response = self.llm.invoke(messages)
            
            return {
                "response": response.content if hasattr(response, 'content') else str(response),
                "messages": [str(m) for m in messages],
                "tool_results": {},
                "iteration_count": 0,
                "metadata": kwargs
            }
        except Exception as e:
            return {
                "error": str(e),
                "response": f"Error running worker agent: {str(e)}",
                "messages": [],
                "tool_results": {},
                "iteration_count": 0,
                "metadata": {}
            }
    
    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Async version of run."""
        if self.agent:
            return await self.agent.arun(input_text, **kwargs)
        else:
            # For now, run synchronously
            return self.run(input_text, **kwargs)
    
    def get_config(self) -> Optional[AgentConfiguration]:
        """Get configuration if available."""
        if self.agent:
            return self.agent.get_config()
        return None
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        if self.agent:
            return list(self.agent.get_available_tools().keys())
        return [tool.name for tool in self.tools] if self.tools else []
    
    def __str__(self) -> str:
        return f"WorkerAgent(name='{self.name}', description='{self.description}')"
    
    def __repr__(self) -> str:
        return self.__str__() 