"""
Google ADK (Agent Development Kit) implementation for multi-agent systems.
This module provides ADK-based alternatives to LangChain/LangGraph components.
"""

# Version information
__version__ = "1.0.0"
__adk_version__ = "0.3.0"

# Core ADK imports
try:
    import google_adk
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("Warning: Google ADK not installed. Please install with: pip install google-adk")

# Module exports
from .config_loader_adk import ADKConfigLoader, ADKAgentConfiguration
from .configurable_agent_adk import ADKConfigurableAgent
from .tool_registry_adk import ADKToolRegistry
from .memory_manager_adk import ADKMemoryManager

__all__ = [
    "ADKConfigLoader",
    "ADKAgentConfiguration",
    "ADKConfigurableAgent",
    "ADKToolRegistry",
    "ADKMemoryManager",
    "ADK_AVAILABLE"
]