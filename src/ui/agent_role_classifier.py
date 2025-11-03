"""
Agent Role Classifier - Categorizes agents by roles and capabilities
"""
from typing import Dict, Any, List, Set, Optional
from enum import Enum
from dataclasses import dataclass
import yaml
from pathlib import Path


class AgentRole(Enum):
    """Agent role types for hierarchical teams."""
    COORDINATOR = "coordinator"
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    SPECIALIST = "specialist"


class AgentCapability(Enum):
    """Agent capability types."""
    WEB_SEARCH = "web_search"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    WRITING = "writing"
    RESEARCH = "research"
    DEBUGGING = "debugging"
    FILE_OPERATIONS = "file_operations"
    CALCULATOR = "calculator"
    COORDINATION = "coordination"
    SUPERVISION = "supervision"
    ROUTING = "routing"
    COMMUNICATION = "communication"


@dataclass
class AgentMetadata:
    """Metadata for an agent including role and capabilities."""
    name: str
    description: str
    primary_role: AgentRole
    secondary_roles: List[AgentRole]
    capabilities: Set[AgentCapability]
    tools: List[str]
    specializations: List[str]
    file_path: str
    compatibility_score: float = 0.0
    can_supervise: bool = False
    can_coordinate: bool = False
    team_size_limit: Optional[int] = None


class AgentRoleClassifier:
    """Classifies agents based on their configuration and capabilities."""
    
    def __init__(self):
        self.capability_keywords = {
            AgentCapability.WEB_SEARCH: ["web_search", "search", "browse", "internet", "web"],
            AgentCapability.CODE_GENERATION: ["code", "programming", "develop", "coding", "python", "javascript"],
            AgentCapability.DATA_ANALYSIS: ["data", "analysis", "analytics", "chart", "graph", "statistics"],
            AgentCapability.WRITING: ["write", "writing", "content", "document", "article", "text"],
            AgentCapability.RESEARCH: ["research", "investigate", "gather", "information", "study"],
            AgentCapability.DEBUGGING: ["debug", "troubleshoot", "fix", "error", "issue"],
            AgentCapability.FILE_OPERATIONS: ["file_reader", "file_writer", "file", "read", "write"],
            AgentCapability.CALCULATOR: ["calculator", "math", "calculate", "compute"],
            AgentCapability.COORDINATION: ["coordinate", "manage", "organize", "orchestrate"],
            AgentCapability.SUPERVISION: ["supervise", "oversee", "manage", "delegate"],
            AgentCapability.ROUTING: ["route", "direct", "forward", "assign"],
            AgentCapability.COMMUNICATION: ["communicate", "message", "relay", "inform"]
        }
        
        self.role_indicators = {
            AgentRole.COORDINATOR: ["coordinator", "orchestrator", "manager", "director"],
            AgentRole.SUPERVISOR: ["supervisor", "overseer", "leader", "team lead"],
            AgentRole.WORKER: ["worker", "specialist", "executor", "agent"],
            AgentRole.SPECIALIST: ["specialist", "expert", "focused", "dedicated"]
        }
    
    def classify_agent(self, config_path: str) -> AgentMetadata:
        """Classify an agent based on its configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            agent_info = config.get('agent', {})
            name = agent_info.get('name', Path(config_path).stem)
            description = agent_info.get('description', '')
            
            # Extract capabilities
            capabilities = self._extract_capabilities(config)
            
            # Extract tools
            tools = self._extract_tools(config)
            
            # Extract specializations
            specializations = self._extract_specializations(config)
            
            # Determine primary role
            primary_role = self._determine_primary_role(name, description, capabilities, specializations)
            
            # Determine secondary roles
            secondary_roles = self._determine_secondary_roles(name, description, capabilities, primary_role)
            
            # Determine supervision and coordination capabilities
            can_supervise = self._can_supervise(capabilities, specializations, description)
            can_coordinate = self._can_coordinate(capabilities, specializations, description)
            
            # Calculate compatibility score
            compatibility_score = self._calculate_compatibility_score(capabilities, tools, specializations)
            
            # Determine team size limit for supervisors
            team_size_limit = self._determine_team_size_limit(primary_role, capabilities)
            
            return AgentMetadata(
                name=name,
                description=description,
                primary_role=primary_role,
                secondary_roles=secondary_roles,
                capabilities=capabilities,
                tools=tools,
                specializations=specializations,
                file_path=config_path,
                compatibility_score=compatibility_score,
                can_supervise=can_supervise,
                can_coordinate=can_coordinate,
                team_size_limit=team_size_limit
            )
            
        except Exception as e:
            # Return basic metadata for failed classification
            return AgentMetadata(
                name=Path(config_path).stem,
                description=f"Error loading agent: {str(e)}",
                primary_role=AgentRole.WORKER,
                secondary_roles=[],
                capabilities=set(),
                tools=[],
                specializations=[],
                file_path=config_path
            )
    
    def _extract_capabilities(self, config: Dict[str, Any]) -> Set[AgentCapability]:
        """Extract capabilities from agent configuration."""
        capabilities = set()
        
        # Check tools for capability indicators
        tools = config.get('tools', {}).get('built_in', [])
        for tool in tools:
            for capability, keywords in self.capability_keywords.items():
                if any(keyword in tool.lower() for keyword in keywords):
                    capabilities.add(capability)
        
        # Check specialization section
        specialization = config.get('specialization', {})
        spec_capabilities = specialization.get('capabilities', [])
        for cap in spec_capabilities:
            for capability, keywords in self.capability_keywords.items():
                if any(keyword in cap.lower() for keyword in keywords):
                    capabilities.add(capability)
        
        # Check agent description and name
        agent_info = config.get('agent', {})
        text_to_check = f"{agent_info.get('name', '')} {agent_info.get('description', '')}"
        for capability, keywords in self.capability_keywords.items():
            if any(keyword in text_to_check.lower() for keyword in keywords):
                capabilities.add(capability)
        
        return capabilities
    
    def _extract_tools(self, config: Dict[str, Any]) -> List[str]:
        """Extract tools from agent configuration."""
        tools = []
        tool_config = config.get('tools', {})
        
        # Built-in tools
        built_in = tool_config.get('built_in', [])
        tools.extend(built_in)
        
        # Custom tools
        custom = tool_config.get('custom', [])
        if isinstance(custom, list):
            tools.extend([tool.get('name', '') if isinstance(tool, dict) else str(tool) for tool in custom])
        
        return tools
    
    def _extract_specializations(self, config: Dict[str, Any]) -> List[str]:
        """Extract specializations from agent configuration."""
        specializations = []
        
        # Check specialization section
        specialization = config.get('specialization', {})
        if 'role' in specialization:
            specializations.append(specialization['role'])
        
        if 'capabilities' in specialization:
            specializations.extend(specialization['capabilities'])
        
        # Check agent role field
        agent_info = config.get('agent', {})
        if 'role' in agent_info:
            specializations.append(agent_info['role'])
        
        return specializations
    
    def _determine_primary_role(self, name: str, description: str, 
                               capabilities: Set[AgentCapability], 
                               specializations: List[str]) -> AgentRole:
        """Determine the primary role of an agent."""
        text_to_check = f"{name} {description} {' '.join(specializations)}".lower()
        
        # Score each role based on indicators
        role_scores = {}
        for role, indicators in self.role_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_to_check)
            role_scores[role] = score
        
        # Add capability-based scoring
        if AgentCapability.COORDINATION in capabilities or AgentCapability.ROUTING in capabilities:
            role_scores[AgentRole.COORDINATOR] = role_scores.get(AgentRole.COORDINATOR, 0) + 2
        
        if AgentCapability.SUPERVISION in capabilities:
            role_scores[AgentRole.SUPERVISOR] = role_scores.get(AgentRole.SUPERVISOR, 0) + 2
        
        # Return role with highest score, default to WORKER
        if role_scores:
            best_role = max(role_scores.items(), key=lambda x: x[1])
            if best_role[1] > 0:
                return best_role[0]
        
        return AgentRole.WORKER
    
    def _determine_secondary_roles(self, name: str, description: str, 
                                  capabilities: Set[AgentCapability], 
                                  primary_role: AgentRole) -> List[AgentRole]:
        """Determine secondary roles an agent can fulfill."""
        secondary_roles = []
        text_to_check = f"{name} {description}".lower()
        
        for role, indicators in self.role_indicators.items():
            if role != primary_role:
                if any(indicator in text_to_check for indicator in indicators):
                    secondary_roles.append(role)
        
        # Add capability-based secondary roles
        if primary_role != AgentRole.SUPERVISOR and AgentCapability.SUPERVISION in capabilities:
            secondary_roles.append(AgentRole.SUPERVISOR)
        
        if primary_role != AgentRole.COORDINATOR and AgentCapability.COORDINATION in capabilities:
            secondary_roles.append(AgentRole.COORDINATOR)
        
        return secondary_roles
    
    def _can_supervise(self, capabilities: Set[AgentCapability], 
                      specializations: List[str], description: str) -> bool:
        """Determine if an agent can act as a supervisor."""
        # Check for supervision indicators
        supervision_indicators = ["supervise", "manage", "coordinate", "oversee", "lead"]
        text_to_check = f"{description} {' '.join(specializations)}".lower()
        
        has_supervision_keywords = any(indicator in text_to_check for indicator in supervision_indicators)
        has_supervision_capabilities = AgentCapability.SUPERVISION in capabilities or AgentCapability.COORDINATION in capabilities
        
        return has_supervision_keywords or has_supervision_capabilities
    
    def _can_coordinate(self, capabilities: Set[AgentCapability], 
                       specializations: List[str], description: str) -> bool:
        """Determine if an agent can act as a coordinator."""
        # Check for coordination indicators
        coordination_indicators = ["coordinate", "orchestrate", "manage", "direct", "route"]
        text_to_check = f"{description} {' '.join(specializations)}".lower()
        
        has_coordination_keywords = any(indicator in text_to_check for indicator in coordination_indicators)
        has_coordination_capabilities = (AgentCapability.COORDINATION in capabilities or 
                                       AgentCapability.ROUTING in capabilities or
                                       AgentCapability.COMMUNICATION in capabilities)
        
        return has_coordination_keywords or has_coordination_capabilities
    
    def _calculate_compatibility_score(self, capabilities: Set[AgentCapability], 
                                     tools: List[str], specializations: List[str]) -> float:
        """Calculate a compatibility score for team formation."""
        score = 0.0
        
        # Base score from number of capabilities
        score += len(capabilities) * 0.1
        
        # Bonus for diverse capabilities
        if len(capabilities) >= 3:
            score += 0.2
        
        # Bonus for coordination/supervision capabilities
        if AgentCapability.COORDINATION in capabilities:
            score += 0.3
        if AgentCapability.SUPERVISION in capabilities:
            score += 0.2
        
        # Bonus for useful tools
        useful_tools = ["web_search", "file_reader", "file_writer", "calculator"]
        score += sum(0.1 for tool in tools if tool in useful_tools)
        
        # Normalize to 0-1 range
        return min(score, 1.0)
    
    def _determine_team_size_limit(self, primary_role: AgentRole, 
                                  capabilities: Set[AgentCapability]) -> Optional[int]:
        """Determine the maximum team size an agent can manage."""
        if primary_role == AgentRole.COORDINATOR:
            return 10  # Coordinators can manage more teams
        elif primary_role == AgentRole.SUPERVISOR:
            return 5   # Supervisors can manage fewer direct workers
        else:
            return None  # Workers don't manage teams
    
    def classify_agents_from_directory(self, directory: str) -> Dict[str, AgentMetadata]:
        """Classify all agents in a directory."""
        agents = {}
        configs_dir = Path(directory)
        
        if configs_dir.exists():
            for config_file in configs_dir.glob("*.yml"):
                try:
                    agent_metadata = self.classify_agent(str(config_file))
                    agents[config_file.stem] = agent_metadata
                except Exception as e:
                    print(f"Error classifying {config_file}: {e}")
        
        return agents
    
    def filter_agents_by_role(self, agents: Dict[str, AgentMetadata], 
                             role: AgentRole, include_secondary: bool = True) -> Dict[str, AgentMetadata]:
        """Filter agents by role."""
        filtered = {}
        for agent_id, metadata in agents.items():
            if metadata.primary_role == role:
                filtered[agent_id] = metadata
            elif include_secondary and role in metadata.secondary_roles:
                filtered[agent_id] = metadata
        
        return filtered
    
    def get_compatible_agents(self, agents: Dict[str, AgentMetadata], 
                             target_capabilities: Set[AgentCapability]) -> Dict[str, AgentMetadata]:
        """Get agents that have compatible capabilities."""
        compatible = {}
        for agent_id, metadata in agents.items():
            if target_capabilities.intersection(metadata.capabilities):
                compatible[agent_id] = metadata
        
        return compatible
    
    def suggest_team_composition(self, agents: Dict[str, AgentMetadata], 
                                task_description: str) -> Dict[str, List[AgentMetadata]]:
        """Suggest team composition based on task description."""
        # Analyze task for required capabilities
        required_capabilities = self._analyze_task_requirements(task_description)
        
        # Get suitable coordinators/supervisors
        coordinators = self.filter_agents_by_role(agents, AgentRole.COORDINATOR)
        supervisors = self.filter_agents_by_role(agents, AgentRole.SUPERVISOR)
        
        # Get workers with required capabilities
        compatible_workers = self.get_compatible_agents(agents, required_capabilities)
        
        return {
            "coordinators": list(coordinators.values()),
            "supervisors": list(supervisors.values()),
            "workers": list(compatible_workers.values())
        }
    
    def _analyze_task_requirements(self, task_description: str) -> Set[AgentCapability]:
        """Analyze task description to determine required capabilities."""
        capabilities = set()
        task_lower = task_description.lower()
        
        for capability, keywords in self.capability_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                capabilities.add(capability)
        
        return capabilities