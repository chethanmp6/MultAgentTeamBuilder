"""
ADK-based configuration loader and validator for configurable agents.
Migrated from LangChain-based config_loader.py to Google ADK.
"""
import yaml
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pathlib import Path

# Load environment variables from .env file
load_dotenv()


class ADKLLMConfig(BaseModel):
    """ADK-compatible LLM configuration."""
    provider: str = "google"  # Default to Google models for ADK
    model: str = "gemini-1.5-flash"  # Default Gemini model
    temperature: float = 0.7
    max_tokens: int = 4000
    api_key_env: str = "GOOGLE_API_KEY"  # Default to Google API key
    project_id: Optional[str] = None  # For Vertex AI
    location: Optional[str] = None  # For Vertex AI
    base_url: Optional[str] = None


class ADKPromptTemplate(BaseModel):
    """ADK-compatible prompt template."""
    template: str
    variables: List[str] = []


class ADKPromptsConfig(BaseModel):
    """ADK-compatible prompts configuration."""
    system_prompt: ADKPromptTemplate
    user_prompt: ADKPromptTemplate
    tool_prompt: Optional[ADKPromptTemplate] = None


class ADKCustomTool(BaseModel):
    """ADK-compatible custom tool definition."""
    name: str
    function_name: str  # ADK uses function names
    description: str
    parameters: Dict[str, Any] = {}
    module_path: Optional[str] = None  # For custom implementations


class ADKToolsConfig(BaseModel):
    """ADK-compatible tools configuration."""
    built_in: List[str] = []
    custom: List[ADKCustomTool] = []


class ADKMemoryStorageConfig(BaseModel):
    """ADK-compatible memory storage configuration."""
    backend: str = "memory"
    connection_string: Optional[str] = None


class ADKMemoryTypesConfig(BaseModel):
    """ADK-compatible memory types configuration."""
    conversation: bool = True  # ADK's conversation memory
    semantic: bool = True
    episodic: bool = True
    procedural: bool = True


class ADKMemorySettingsConfig(BaseModel):
    """ADK-compatible memory settings configuration."""
    max_memory_size: int = 10000
    retention_days: int = 30
    session_management: bool = True  # ADK session management


class ADKMemoryConfig(BaseModel):
    """ADK-compatible memory configuration."""
    enabled: bool = False
    provider: str = "adk"  # Use ADK's built-in memory
    types: ADKMemoryTypesConfig = ADKMemoryTypesConfig()
    storage: ADKMemoryStorageConfig = ADKMemoryStorageConfig()
    settings: ADKMemorySettingsConfig = ADKMemorySettingsConfig()


class ADKWorkflowConfig(BaseModel):
    """ADK workflow configuration (replaces ReAct config)."""
    max_iterations: int = 10
    timeout_seconds: int = 300
    workflow_type: str = "sequential"  # sequential, parallel, conditional


class ADKPromptOptimizationConfig(BaseModel):
    """ADK-compatible prompt optimization configuration."""
    enabled: bool = False
    feedback_collection: bool = False
    ab_testing: bool = False
    optimization_frequency: str = "weekly"


class ADKPerformanceTrackingConfig(BaseModel):
    """ADK-compatible performance tracking configuration."""
    enabled: bool = False
    metrics: List[str] = ["response_time", "accuracy", "user_satisfaction"]
    adk_monitoring: bool = True  # Use ADK's built-in monitoring


class ADKOptimizationConfig(BaseModel):
    """ADK-compatible optimization configuration."""
    enabled: bool = False
    prompt_optimization: ADKPromptOptimizationConfig = ADKPromptOptimizationConfig()
    performance_tracking: ADKPerformanceTrackingConfig = ADKPerformanceTrackingConfig()


class ADKRuntimeConfig(BaseModel):
    """ADK-compatible runtime configuration."""
    max_iterations: int = 50
    timeout_seconds: int = 300
    retry_attempts: int = 3
    debug_mode: bool = False
    use_adk_dev_ui: bool = False  # Enable ADK's development UI


class ADKAgentInfo(BaseModel):
    """ADK-compatible agent information."""
    name: str
    description: str
    version: str = "1.0.0"
    framework: str = "google-adk"  # Specify ADK framework


class ADKAgentConfiguration(BaseModel):
    """ADK-compatible agent configuration model."""
    agent: ADKAgentInfo
    llm: ADKLLMConfig
    prompts: ADKPromptsConfig
    tools: ADKToolsConfig = ADKToolsConfig()
    memory: ADKMemoryConfig = ADKMemoryConfig()
    workflow: ADKWorkflowConfig = ADKWorkflowConfig()
    optimization: ADKOptimizationConfig = ADKOptimizationConfig()
    runtime: ADKRuntimeConfig = ADKRuntimeConfig()

    @field_validator('llm')
    @classmethod
    def validate_api_key_exists(cls, v):
        """Validate that required API keys exist."""
        if v.api_key_env and not os.getenv(v.api_key_env):
            print(f"Warning: Environment variable {v.api_key_env} not found")
            # Don't fail validation, just warn
        return v


class ADKConfigLoader:
    """ADK-based configuration loader and validator."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: Optional[ADKAgentConfiguration] = None

    def load_config(self, config_file: str) -> ADKAgentConfiguration:
        """Load configuration from YAML file and convert to ADK format."""
        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # Convert LangChain config to ADK config if needed
            config_data = self._convert_langchain_to_adk(config_data)

            # Validate and parse configuration
            self._config = ADKAgentConfiguration(**config_data)
            return self._config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Configuration validation error: {e}")

    def _convert_langchain_to_adk(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LangChain configuration format to ADK format."""
        converted = config_data.copy()

        # Convert LLM configuration
        if 'llm' in converted:
            llm_config = converted['llm']

            # Map provider names to ADK-compatible ones
            provider_mapping = {
                "openai": "google",  # Migrate to Google models
                "anthropic": "google",
                "gemini": "google",
                "google": "google",
                "groq": "google"
            }

            original_provider = llm_config.get('provider', 'openai')
            llm_config['provider'] = provider_mapping.get(original_provider, 'google')

            # Map model names to Google models
            model_mapping = {
                "gpt-4o-mini": "gemini-1.5-flash",
                "gpt-4": "gemini-1.5-pro",
                "claude-3-5-sonnet-20241022": "gemini-1.5-pro",
                "claude-3-haiku": "gemini-1.5-flash"
            }

            original_model = llm_config.get('model', 'gpt-4o-mini')
            llm_config['model'] = model_mapping.get(original_model, 'gemini-1.5-flash')

            # Update API key environment variable
            if original_provider != 'google':
                llm_config['api_key_env'] = 'GOOGLE_API_KEY'

        # Convert ReAct config to workflow config
        if 'react' in converted:
            react_config = converted.pop('react')
            converted['workflow'] = {
                'max_iterations': react_config.get('max_iterations', 10),
                'timeout_seconds': react_config.get('timeout_seconds', 300),
                'workflow_type': 'sequential'
            }

        # Add framework specification
        if 'agent' in converted:
            converted['agent']['framework'] = 'google-adk'

        # Convert custom tools to ADK format
        if 'tools' in converted and 'custom' in converted['tools']:
            for tool in converted['tools']['custom']:
                if 'class_name' in tool:
                    tool['function_name'] = tool.pop('class_name')

        return converted

    def get_config(self) -> Optional[ADKAgentConfiguration]:
        """Get the loaded configuration."""
        return self._config

    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration data without loading."""
        try:
            # Convert if needed
            config_data = self._convert_langchain_to_adk(config_data)
            ADKAgentConfiguration(**config_data)
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

    def get_llm_config(self) -> ADKLLMConfig:
        """Get LLM configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.llm

    def get_tools_config(self) -> ADKToolsConfig:
        """Get tools configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.tools

    def get_memory_config(self) -> ADKMemoryConfig:
        """Get memory configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.memory

    def get_workflow_config(self) -> ADKWorkflowConfig:
        """Get workflow configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.workflow

    def export_adk_config(self, output_file: str):
        """Export current configuration in ADK format."""
        if not self._config:
            raise ValueError("No configuration loaded")

        config_dict = self._config.model_dump()

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

    def get_migration_report(self) -> Dict[str, Any]:
        """Generate a report on the migration from LangChain to ADK."""
        if not self._config:
            return {"error": "No configuration loaded"}

        return {
            "framework": "google-adk",
            "llm_provider": self._config.llm.provider,
            "llm_model": self._config.llm.model,
            "tools_count": len(self._config.tools.built_in) + len(self._config.tools.custom),
            "memory_enabled": self._config.memory.enabled,
            "workflow_type": self._config.workflow.workflow_type,
            "adk_features": {
                "dev_ui_available": True,
                "monitoring_enabled": self._config.optimization.performance_tracking.adk_monitoring,
                "session_management": self._config.memory.settings.session_management
            }
        }