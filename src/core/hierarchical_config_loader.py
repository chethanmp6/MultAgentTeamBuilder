"""
Configuration loader and validator for hierarchical agent teams.
Extends the base configuration loader with hierarchical team support.
"""
import yaml
import os
from typing import Dict, Any, Optional, List, Union, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path

from .config_loader import (
    LLMConfig, PromptTemplate, ToolsConfig, MemoryConfig,
    RuntimeConfig, AgentConfiguration
)

# Load environment variables from .env file
load_dotenv()


class RoutingConfig(BaseModel):
    """Configuration for decision-making and routing in hierarchical systems."""
    strategy: Literal["keyword_based", "llm_based", "rule_based", "hybrid"] = "hybrid"
    fallback_team: Optional[str] = None
    fallback_worker: Optional[str] = None
    confidence_threshold: float = 0.7
    max_decision_time: int = 30


class CoordinatorPromptsConfig(BaseModel):
    """Prompts configuration specific to coordinators."""
    system_prompt: PromptTemplate
    decision_prompt: PromptTemplate
    coordination_prompt: Optional[PromptTemplate] = None


class CoordinatorConfig(BaseModel):
    """Configuration for the team coordinator."""
    name: str
    description: str
    llm: LLMConfig
    prompts: CoordinatorPromptsConfig
    routing: RoutingConfig = RoutingConfig()


class WorkerLLMOverrideConfig(BaseModel):
    """Partial LLM configuration for worker overrides."""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None


class WorkerOverrideConfig(BaseModel):
    """Optional overrides for worker configuration."""
    llm: Optional[WorkerLLMOverrideConfig] = None
    tools: Optional[ToolsConfig] = None
    memory: Optional[MemoryConfig] = None


class WorkerConfig(BaseModel):
    """Configuration for individual worker agents."""
    name: str
    role: str
    config_file: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    description: str
    capabilities: List[str] = []
    priority: int = 1
    overrides: Optional[WorkerOverrideConfig] = None
    
    @field_validator('config_file')
    @classmethod
    def validate_config_file_exists(cls, v):
        """Validate that the worker config file exists."""
        if v is None:
            return v
        if not Path(v).exists():
            # Try relative to configs/examples
            alt_path = Path(f"configs/examples/{v}")
            if not alt_path.exists():
                raise ValueError(f"Worker configuration file not found: {v}")
        return v
    
    @model_validator(mode='after')
    def validate_config_or_data(self):
        """Validate that either config_file or config_data is provided."""
        if not self.config_file and not self.config_data:
            raise ValueError("Either config_file or config_data must be provided for worker")
        return self


class SupervisorConfig(BaseModel):
    """Configuration for team supervisors."""
    name: str
    config_file: Optional[str] = None
    llm: Optional[LLMConfig] = None
    routing: RoutingConfig = RoutingConfig()


class TeamConfig(BaseModel):
    """Configuration for individual teams within the hierarchy."""
    name: str
    description: str
    supervisor: SupervisorConfig
    workers: List[WorkerConfig] = []


class HierarchicalMemoryLevelConfig(BaseModel):
    """Memory configuration for different hierarchy levels."""
    enabled: bool = True
    types: Dict[str, bool] = {
        "semantic": True,
        "episodic": True,
        "procedural": True
    }
    storage: Optional[Dict[str, Any]] = None


class HierarchicalMemoryConfig(BaseModel):
    """Memory configuration for hierarchical teams."""
    enabled: bool = True
    provider: str = "langmem"
    
    levels: Dict[str, HierarchicalMemoryLevelConfig] = {
        "coordinator": HierarchicalMemoryLevelConfig(),
        "team": HierarchicalMemoryLevelConfig(),
        "worker": HierarchicalMemoryLevelConfig()
    }
    
    settings: Dict[str, Any] = {
        "max_memory_size": 20000,
        "retention_days": 60,
        "background_processing": True,
        "memory_consolidation": True
    }


class TaskFlowConfig(BaseModel):
    """Configuration for task flow and execution."""
    type: Literal["sequential", "parallel", "conditional", "pipeline"] = "sequential"
    max_parallel_tasks: int = 3
    timeout_per_task: int = 300
    retry_strategy: Literal["none", "linear", "exponential"] = "linear"


class ResultsConfig(BaseModel):
    """Configuration for results aggregation."""
    aggregation_strategy: Literal["merge", "prioritize", "vote", "consensus"] = "merge"
    final_response_format: Literal["detailed", "summary", "raw"] = "detailed"
    include_reasoning: bool = True
    include_metadata: bool = True


class CoordinationConfig(BaseModel):
    """Configuration for team coordination and communication."""
    cross_team_communication: bool = False
    team_dependencies: List[str] = []
    task_flow: TaskFlowConfig = TaskFlowConfig()
    results: ResultsConfig = ResultsConfig()


class PerformanceMonitoringConfig(BaseModel):
    """Configuration for performance monitoring."""
    enabled: bool = True
    metrics: List[str] = [
        "response_time",
        "task_success_rate", 
        "worker_utilization",
        "decision_accuracy",
        "communication_efficiency"
    ]


class PerformanceOptimizationConfig(BaseModel):
    """Configuration for performance optimization."""
    enabled: bool = False
    auto_scaling: bool = False
    load_balancing: bool = False
    adaptive_routing: bool = False


class PerformanceConfig(BaseModel):
    """Performance and monitoring configuration."""
    monitoring: PerformanceMonitoringConfig = PerformanceMonitoringConfig()
    optimization: PerformanceOptimizationConfig = PerformanceOptimizationConfig()


class ScalingConfig(BaseModel):
    """Configuration for scaling workers and teams."""
    min_workers_per_team: int = 1
    max_workers_per_team: int = 10
    auto_scale: bool = False


class SecurityConfig(BaseModel):
    """Security configuration for hierarchical teams."""
    api_key_management: Literal["environment", "vault", "config"] = "environment"
    access_control: List[str] = []
    audit_logging: bool = True


class DeploymentConfig(BaseModel):
    """Deployment configuration."""
    environment: Literal["development", "staging", "production"] = "development"
    scaling: ScalingConfig = ScalingConfig()
    security: SecurityConfig = SecurityConfig()


class HierarchicalRuntimeConfig(BaseModel):
    """Runtime configuration for hierarchical teams."""
    max_iterations: int = 50
    timeout_seconds: int = 600
    retry_attempts: int = 3
    debug_mode: bool = False
    
    # Hierarchical-specific settings
    max_delegation_depth: int = 5
    task_queue_size: int = 100
    concurrent_tasks: int = 5
    heartbeat_interval: int = 30


class TeamInfo(BaseModel):
    """Basic information about the hierarchical team."""
    name: str
    description: str
    version: str = "1.0.0"
    type: Literal["hierarchical", "flat", "pipeline"] = "hierarchical"


class HierarchicalAgentConfiguration(BaseModel):
    """Complete configuration for hierarchical agent teams."""
    team: TeamInfo
    coordinator: CoordinatorConfig
    teams: List[TeamConfig] = []
    memory: HierarchicalMemoryConfig = HierarchicalMemoryConfig()
    coordination: CoordinationConfig = CoordinationConfig()
    performance: PerformanceConfig = PerformanceConfig()
    deployment: DeploymentConfig = DeploymentConfig()
    runtime: HierarchicalRuntimeConfig = HierarchicalRuntimeConfig()
    
    @field_validator('teams')
    @classmethod
    def validate_teams_not_empty(cls, v):
        """Ensure at least one team is configured."""
        if not v:
            raise ValueError("At least one team must be configured")
        return v
    
    @field_validator('coordinator')
    @classmethod
    def validate_coordinator_api_key(cls, v):
        """Validate coordinator API key exists."""
        if v.llm.api_key_env and not os.getenv(v.llm.api_key_env):
            raise ValueError(f"Environment variable {v.llm.api_key_env} not found")
        return v


class HierarchicalConfigLoader:
    """Loads and validates hierarchical agent team configurations from YAML files."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: Optional[HierarchicalAgentConfiguration] = None
    
    def load_config(self, config_file: str) -> HierarchicalAgentConfiguration:
        """Load hierarchical configuration from YAML file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Validate and parse configuration
            self._config = HierarchicalAgentConfiguration(**config_data)
            return self._config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Configuration validation error: {e}")
    
    def get_config(self) -> Optional[HierarchicalAgentConfiguration]:
        """Get the loaded configuration."""
        return self._config
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration data without loading."""
        try:
            HierarchicalAgentConfiguration(**config_data)
            return True
        except Exception:
            return False
    
    def get_coordinator_config(self) -> CoordinatorConfig:
        """Get coordinator configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.coordinator
    
    def get_teams_config(self) -> List[TeamConfig]:
        """Get teams configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.teams
    
    def get_team_config(self, team_name: str) -> Optional[TeamConfig]:
        """Get configuration for a specific team."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        
        for team in self._config.teams:
            if team.name == team_name:
                return team
        return None
    
    def get_worker_configs(self, team_name: Optional[str] = None) -> List[WorkerConfig]:
        """Get worker configurations for a specific team or all teams."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        
        if team_name:
            team_config = self.get_team_config(team_name)
            return team_config.workers if team_config else []
        
        # Return all workers from all teams
        all_workers = []
        for team in self._config.teams:
            all_workers.extend(team.workers)
        return all_workers
    
    def get_memory_config(self) -> HierarchicalMemoryConfig:
        """Get hierarchical memory configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.memory
    
    def get_coordination_config(self) -> CoordinationConfig:
        """Get coordination configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.coordination
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.performance
    
    def get_runtime_config(self) -> HierarchicalRuntimeConfig:
        """Get runtime configuration."""
        if not self._config:
            raise ValueError("Configuration not loaded")
        return self._config.runtime
    
    def export_config(self, output_file: str) -> None:
        """Export the loaded configuration to a YAML file."""
        if not self._config:
            raise ValueError("No configuration loaded to export")
        
        config_dict = self._config.model_dump()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False, indent=2)