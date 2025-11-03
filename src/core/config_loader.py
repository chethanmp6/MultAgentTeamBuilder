"""
Configuration loader and validator for configurable agents.
"""
import yaml
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pathlib import Path

# Load environment variables from .env file
load_dotenv()


class LLMConfig(BaseModel):
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    api_key_env: str
    base_url: Optional[str] = None


class PromptTemplate(BaseModel):
    template: str
    variables: List[str] = []


class PromptsConfig(BaseModel):
    system_prompt: PromptTemplate
    user_prompt: PromptTemplate
    tool_prompt: Optional[PromptTemplate] = None


class CustomTool(BaseModel):
    name: str
    module_path: str
    class_name: str
    description: str
    parameters: Dict[str, Any] = {}


class ToolsConfig(BaseModel):
    built_in: List[str] = []
    custom: List[CustomTool] = []


class MemoryStorageConfig(BaseModel):
    backend: str = "memory"
    connection_string: Optional[str] = None


class MemoryTypesConfig(BaseModel):
    semantic: bool = True
    episodic: bool = True
    procedural: bool = True


class MemorySettingsConfig(BaseModel):
    max_memory_size: int = 10000
    retention_days: int = 30
    background_processing: bool = True


class MemoryConfig(BaseModel):
    enabled: bool = False
    provider: str = "langmem"
    types: MemoryTypesConfig = MemoryTypesConfig()
    storage: MemoryStorageConfig = MemoryStorageConfig()
    settings: MemorySettingsConfig = MemorySettingsConfig()


# ReAct pattern uses a simpler configuration - no complex graph needed
class ReactConfig(BaseModel):
    max_iterations: int = 10
    recursion_limit: int = 50


class PromptOptimizationConfig(BaseModel):
    enabled: bool = False
    feedback_collection: bool = False
    ab_testing: bool = False
    optimization_frequency: str = "weekly"


class PerformanceTrackingConfig(BaseModel):
    enabled: bool = False
    metrics: List[str] = ["response_time", "accuracy", "user_satisfaction"]


class OptimizationConfig(BaseModel):
    enabled: bool = False
    prompt_optimization: PromptOptimizationConfig = PromptOptimizationConfig()
    performance_tracking: PerformanceTrackingConfig = PerformanceTrackingConfig()


class RuntimeConfig(BaseModel):
    max_iterations: int = 50
    timeout_seconds: int = 300
    retry_attempts: int = 3
    debug_mode: bool = False


class AgentInfo(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"


class AgentConfiguration(BaseModel):
    agent: AgentInfo
    llm: LLMConfig
    prompts: PromptsConfig
    tools: ToolsConfig = ToolsConfig()
    memory: MemoryConfig = MemoryConfig()
    react: ReactConfig = ReactConfig()
    optimization: OptimizationConfig = OptimizationConfig()
    runtime: RuntimeConfig = RuntimeConfig()

    @field_validator('llm')
    @classmethod
    def validate_api_key_exists(cls, v):
        if v.api_key_env and not os.getenv(v.api_key_env):
            raise ValueError(f"Environment variable {v.api_key_env} not found")
        return v


class ConfigLoader:
    """Loads and validates agent configurations from YAML files."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: Optional[AgentConfiguration] = None
    
    def load_config(self, config_file: str) -> AgentConfiguration:
        """Load configuration from YAML file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Validate and parse configuration
            self._config = AgentConfiguration(**config_data)
            return self._config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Configuration validation error: {e}")
    
    def get_config(self) -> Optional[AgentConfiguration]:
        """Get the loaded configuration."""
        return self._config
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration data without loading."""
        try:
            AgentConfiguration(**config_data)
            return True
        except Exception:
            return False
    
    def get_prompt_template(self, prompt_type: str, **variables) -> str:
        """Get a formatted prompt template with variables substituted."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        
        prompt_config = getattr(self._config.prompts, prompt_type, None)
        if not prompt_config:
            raise ValueError(f"Prompt type '{prompt_type}' not found")
        
        template = prompt_config.template
        
        # Substitute variables
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            template = template.replace(placeholder, str(var_value))
        
        return template
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.llm
    
    def get_tools_config(self) -> ToolsConfig:
        """Get tools configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.tools
    
    def get_memory_config(self) -> MemoryConfig:
        """Get memory configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.memory
    
    def get_react_config(self) -> ReactConfig:
        """Get ReAct configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.react