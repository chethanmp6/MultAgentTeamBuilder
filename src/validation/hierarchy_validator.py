"""
Hierarchical Agent Configuration Validator & Routing Optimizer
Uses LLM-as-judge pattern to analyze team configurations and optimize routing prompts.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.chat_models import init_chat_model
import os
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationCategory(Enum):
    """Categories of validation checks."""
    ROUTING_LOGIC = "routing_logic"
    CAPABILITY_ALIGNMENT = "capability_alignment"
    PROMPT_CLARITY = "prompt_clarity"
    FALLBACK_HANDLING = "fallback_handling"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    STRUCTURE_VALIDATION = "structure_validation"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the configuration."""
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    location: str  # Path to the issue in config (e.g., "teams.main_team.supervisor.prompts.system_prompt")
    suggestion: str
    auto_fixable: bool = False
    confidence: float = 1.0
    
    
@dataclass
class ValidationResult:
    """Complete validation result for a hierarchical configuration."""
    overall_score: float  # 0-100
    issues: List[ValidationIssue]
    suggestions: List[str]
    optimized_config: Optional[Dict[str, Any]] = None
    validation_timestamp: datetime = None
    
    def __post_init__(self):
        if self.validation_timestamp is None:
            self.validation_timestamp = datetime.now()


@dataclass
class AgentAnalysis:
    """Analysis of an individual agent's capabilities and configuration."""
    agent_id: str
    agent_type: str  # supervisor, worker, coordinator
    capabilities: List[str]
    tools: List[str]
    prompt_quality_score: float
    routing_clarity_score: float
    issues: List[ValidationIssue]


class HierarchyValidator:
    """
    LLM-as-judge validator for hierarchical agent configurations.
    Analyzes team structure and optimizes routing prompts.
    """
    
    def __init__(self, judge_llm: Optional[BaseChatModel] = None):
        """
        Initialize the hierarchy validator.
        
        Args:
            judge_llm: LLM to use as judge. If None, uses default OpenAI model.
        """
        self.judge_llm = judge_llm or self._create_default_judge_llm()
        self.validation_history: List[ValidationResult] = []
    
    def _create_default_judge_llm(self) -> BaseChatModel:
        """Create a default LLM for validation judging."""
        return init_chat_model(
            "openai:gpt-4o",  # Use GPT-4 for better analysis
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=4000
        )
    
    def validate_hierarchy_config(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate a complete hierarchical configuration.
        
        Args:
            config: Hierarchical team configuration
            
        Returns:
            ValidationResult with issues, suggestions, and optimized config
        """
        logger.info("Starting hierarchical configuration validation")
        
        # Initialize validation result
        issues = []
        suggestions = []
        agent_analyses = []
        
        try:
            # 1. Structure validation
            structure_issues = self._validate_structure(config)
            issues.extend(structure_issues)
            
            # 2. Analyze coordinator
            if 'coordinator' in config:
                coord_analysis = self._analyze_coordinator(config['coordinator'], config.get('teams', []))
                agent_analyses.append(coord_analysis)
                issues.extend(coord_analysis.issues)
            
            # 3. Analyze teams and supervisors
            if 'teams' in config:
                for team_config in config['teams']:
                    if 'supervisor' in team_config:
                        supervisor_analysis = self._analyze_supervisor(
                            team_config['supervisor'], 
                            team_config.get('workers', []),
                            team_config.get('name', 'unknown')
                        )
                        agent_analyses.append(supervisor_analysis)
                        issues.extend(supervisor_analysis.issues)
            
            # 4. Generate LLM-based analysis and suggestions
            llm_analysis = self._get_llm_analysis(config, issues)
            suggestions.extend(llm_analysis['suggestions'])
            issues.extend(llm_analysis['additional_issues'])
            
            # 5. Generate optimized configuration
            optimized_config = self._generate_optimized_config(config, issues, agent_analyses)
            
            # 6. Calculate overall score
            overall_score = self._calculate_overall_score(issues, len(agent_analyses))
            
            result = ValidationResult(
                overall_score=overall_score,
                issues=issues,
                suggestions=suggestions,
                optimized_config=optimized_config
            )
            
            self.validation_history.append(result)
            logger.info(f"Validation completed. Score: {overall_score:.1f}/100, Issues found: {len(issues)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            # Return a basic result with the error
            return ValidationResult(
                overall_score=0.0,
                issues=[ValidationIssue(
                    category=ValidationCategory.STRUCTURE_VALIDATION,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation failed with error: {str(e)}",
                    location="root",
                    suggestion="Please check the configuration format and try again."
                )],
                suggestions=["Fix configuration format errors and retry validation."]
            )
    
    def _validate_structure(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate basic structure of hierarchical configuration."""
        issues = []
        
        # Check required sections
        required_sections = ['team', 'coordinator', 'teams']
        for section in required_sections:
            if section not in config:
                issues.append(ValidationIssue(
                    category=ValidationCategory.STRUCTURE_VALIDATION,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Missing required section: {section}",
                    location=f"root.{section}",
                    suggestion=f"Add the required '{section}' section to the configuration.",
                    auto_fixable=False
                ))
        
        # Check teams structure
        if 'teams' in config:
            teams = config['teams']
            if not isinstance(teams, list) or len(teams) == 0:
                issues.append(ValidationIssue(
                    category=ValidationCategory.STRUCTURE_VALIDATION,
                    severity=ValidationSeverity.HIGH,
                    message="Teams section must be a non-empty list",
                    location="root.teams",
                    suggestion="Ensure teams is configured as a list with at least one team.",
                    auto_fixable=False
                ))
            else:
                for i, team in enumerate(teams):
                    if 'supervisor' not in team:
                        issues.append(ValidationIssue(
                            category=ValidationCategory.STRUCTURE_VALIDATION,
                            severity=ValidationSeverity.HIGH,
                            message=f"Team {i} missing supervisor configuration",
                            location=f"teams[{i}].supervisor",
                            suggestion="Add supervisor configuration to the team.",
                            auto_fixable=False
                        ))
                    
                    if 'workers' not in team or len(team['workers']) == 0:
                        issues.append(ValidationIssue(
                            category=ValidationCategory.STRUCTURE_VALIDATION,
                            severity=ValidationSeverity.MEDIUM,
                            message=f"Team {i} has no workers configured",
                            location=f"teams[{i}].workers",
                            suggestion="Add worker agents to the team for proper functionality.",
                            auto_fixable=False
                        ))
        
        return issues
    
    def _analyze_coordinator(self, coordinator_config: Dict[str, Any], teams: List[Dict[str, Any]]) -> AgentAnalysis:
        """Analyze coordinator configuration for routing effectiveness."""
        issues = []
        
        # Analyze prompts
        prompts = coordinator_config.get('prompts', {})
        system_prompt = prompts.get('system_prompt', {}).get('template', '')
        
        # Check if coordinator prompt mentions teams
        team_names = [team.get('name', f'team_{i}') for i, team in enumerate(teams)]
        routing_clarity_score = 0.8  # Base score
        
        if not system_prompt:
            issues.append(ValidationIssue(
                category=ValidationCategory.PROMPT_CLARITY,
                severity=ValidationSeverity.HIGH,
                message="Coordinator system prompt is empty",
                location="coordinator.prompts.system_prompt.template",
                suggestion="Add a system prompt that explains the coordinator's role in routing tasks to teams.",
                auto_fixable=True,
                confidence=0.95
            ))
            routing_clarity_score = 0.2
        else:
            # Check if prompt mentions team routing
            routing_keywords = ['route', 'delegate', 'assign', 'team', 'coordinate']
            if not any(keyword in system_prompt.lower() for keyword in routing_keywords):
                issues.append(ValidationIssue(
                    category=ValidationCategory.ROUTING_LOGIC,
                    severity=ValidationSeverity.MEDIUM,
                    message="Coordinator prompt lacks clear routing instructions",
                    location="coordinator.prompts.system_prompt.template",
                    suggestion="Add specific instructions for how to route tasks to appropriate teams.",
                    auto_fixable=True,
                    confidence=0.85
                ))
                routing_clarity_score *= 0.7
            
            # Check if specific teams are mentioned
            teams_mentioned = sum(1 for team_name in team_names if team_name in system_prompt)
            if teams_mentioned == 0 and len(team_names) > 0:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CAPABILITY_ALIGNMENT,
                    severity=ValidationSeverity.MEDIUM,
                    message="Coordinator prompt doesn't reference specific teams",
                    location="coordinator.prompts.system_prompt.template",
                    suggestion="Include references to available teams and their capabilities in the prompt.",
                    auto_fixable=True,
                    confidence=0.80
                ))
                routing_clarity_score *= 0.8
        
        return AgentAnalysis(
            agent_id="coordinator",
            agent_type="coordinator",
            capabilities=["coordination", "routing", "delegation"],
            tools=coordinator_config.get('tools', {}).get('built_in', []),
            prompt_quality_score=min(routing_clarity_score + 0.1, 1.0),
            routing_clarity_score=routing_clarity_score,
            issues=issues
        )
    
    def _analyze_supervisor(self, supervisor_config: Dict[str, Any], workers: List[Dict[str, Any]], team_name: str) -> AgentAnalysis:
        """Analyze supervisor configuration for worker routing effectiveness."""
        issues = []
        
        # Extract worker information
        worker_capabilities = []
        worker_names = []
        for worker in workers:
            worker_names.append(worker.get('name', 'unnamed_worker'))
            worker_capabilities.extend(worker.get('capabilities', []))
        
        # Analyze supervisor prompts
        system_prompt = ""
        if 'prompts' in supervisor_config:
            system_prompt = supervisor_config['prompts'].get('system_prompt', {}).get('template', '')
        elif 'config_data' in supervisor_config and 'prompts' in supervisor_config['config_data']:
            system_prompt = supervisor_config['config_data']['prompts'].get('system_prompt', {}).get('template', '')
        
        routing_clarity_score = 0.7  # Base score
        
        if not system_prompt:
            issues.append(ValidationIssue(
                category=ValidationCategory.PROMPT_CLARITY,
                severity=ValidationSeverity.HIGH,
                message=f"Supervisor in team '{team_name}' has no system prompt",
                location=f"teams.{team_name}.supervisor.prompts.system_prompt",
                suggestion="Add a system prompt that defines the supervisor's role and worker delegation strategy.",
                auto_fixable=True,
                confidence=0.95
            ))
            routing_clarity_score = 0.2
        else:
            # Check for routing logic
            routing_keywords = ['delegate', 'assign', 'worker', 'choose', 'select', 'route']
            if not any(keyword in system_prompt.lower() for keyword in routing_keywords):
                issues.append(ValidationIssue(
                    category=ValidationCategory.ROUTING_LOGIC,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Supervisor in team '{team_name}' lacks clear worker delegation instructions",
                    location=f"teams.{team_name}.supervisor.prompts.system_prompt",
                    suggestion="Add specific instructions for how to delegate tasks to workers based on their capabilities.",
                    auto_fixable=True,
                    confidence=0.85
                ))
                routing_clarity_score *= 0.7
            
            # Check if workers are mentioned by name
            workers_mentioned = sum(1 for worker_name in worker_names if worker_name in system_prompt)
            if workers_mentioned == 0 and len(worker_names) > 0:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CAPABILITY_ALIGNMENT,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Supervisor in team '{team_name}' doesn't reference specific workers",
                    location=f"teams.{team_name}.supervisor.prompts.system_prompt",
                    suggestion="Include references to available workers and their specific capabilities in the prompt.",
                    auto_fixable=True,
                    confidence=0.80
                ))
                routing_clarity_score *= 0.8
            
            # Check if worker capabilities are referenced
            capabilities_mentioned = sum(1 for cap in worker_capabilities if cap.lower() in system_prompt.lower())
            if capabilities_mentioned == 0 and len(worker_capabilities) > 0:
                issues.append(ValidationIssue(
                    category=ValidationCategory.CAPABILITY_ALIGNMENT,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Supervisor in team '{team_name}' doesn't reference worker capabilities",
                    location=f"teams.{team_name}.supervisor.prompts.system_prompt",
                    suggestion="Include worker capabilities in the prompt to improve task delegation decisions.",
                    auto_fixable=True,
                    confidence=0.75
                ))
                routing_clarity_score *= 0.8
        
        return AgentAnalysis(
            agent_id=f"{team_name}_supervisor",
            agent_type="supervisor",
            capabilities=worker_capabilities,
            tools=supervisor_config.get('tools', {}).get('built_in', []) if 'tools' in supervisor_config else [],
            prompt_quality_score=min(routing_clarity_score + 0.1, 1.0),
            routing_clarity_score=routing_clarity_score,
            issues=issues
        )
    
    def _get_llm_analysis(self, config: Dict[str, Any], existing_issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Use LLM to perform deep analysis of the configuration."""
        try:
            analysis_prompt = self._create_analysis_prompt(config, existing_issues)
            
            messages = [
                SystemMessage(content="""You are an expert in hierarchical multi-agent systems and configuration optimization. 
                Your role is to analyze agent team configurations and provide specific, actionable suggestions for improving 
                task routing and coordination efficiency. Focus on practical improvements that will enhance the system's 
                ability to route tasks to the most appropriate agents."""),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = self.judge_llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse the response to extract suggestions and additional issues
            return self._parse_llm_analysis(content)
            
        except Exception as e:
            logger.warning(f"LLM analysis failed: {str(e)}")
            return {
                'suggestions': ['Consider reviewing the configuration manually for optimization opportunities.'],
                'additional_issues': []
            }
    
    def _create_analysis_prompt(self, config: Dict[str, Any], existing_issues: List[ValidationIssue]) -> str:
        """Create a prompt for LLM analysis of the configuration."""
        config_summary = json.dumps(config, indent=2)
        issues_summary = "\n".join([f"- {issue.severity.value}: {issue.message}" for issue in existing_issues])
        
        return f"""
        Please analyze this hierarchical agent team configuration for routing effectiveness and optimization opportunities:

        CONFIGURATION:
        {config_summary}

        ISSUES ALREADY IDENTIFIED:
        {issues_summary}

        Please provide:
        1. ADDITIONAL_SUGGESTIONS: List 3-5 specific suggestions for improving task routing and coordination
        2. ROUTING_IMPROVEMENTS: Specific improvements for supervisor/coordinator prompts
        3. PERFORMANCE_OPTIMIZATIONS: Ways to improve team performance and efficiency

        Focus on:
        - Clear task delegation strategies
        - Capability-based routing logic
        - Fallback mechanisms for unhandled tasks
        - Performance optimization opportunities
        - Team coordination improvements

        Provide your response in this format:
        ADDITIONAL_SUGGESTIONS:
        - [suggestion 1]
        - [suggestion 2]
        ...

        ROUTING_IMPROVEMENTS:
        - [improvement 1]
        - [improvement 2]
        ...

        PERFORMANCE_OPTIMIZATIONS:
        - [optimization 1]
        - [optimization 2]
        ...
        """
    
    def _parse_llm_analysis(self, content: str) -> Dict[str, Any]:
        """Parse LLM analysis response into structured suggestions."""
        suggestions = []
        additional_issues = []
        
        # Extract suggestions from different sections
        sections = {
            'ADDITIONAL_SUGGESTIONS:': 'general',
            'ROUTING_IMPROVEMENTS:': 'routing',
            'PERFORMANCE_OPTIMIZATIONS:': 'performance'
        }
        
        current_section = None
        for line in content.split('\n'):
            line = line.strip()
            
            # Check for section headers
            for section_header in sections:
                if line.startswith(section_header):
                    current_section = sections[section_header]
                    continue
            
            # Extract bullet points
            if line.startswith('-') and current_section:
                suggestion = line[1:].strip()
                if suggestion:
                    suggestions.append(f"[{current_section.title()}] {suggestion}")
        
        return {
            'suggestions': suggestions,
            'additional_issues': additional_issues
        }
    
    def _generate_optimized_config(self, original_config: Dict[str, Any], 
                                 issues: List[ValidationIssue], 
                                 agent_analyses: List[AgentAnalysis]) -> Dict[str, Any]:
        """Generate an optimized version of the configuration."""
        optimized_config = json.loads(json.dumps(original_config))  # Deep copy
        
        try:
            # Apply auto-fixable optimizations
            for issue in issues:
                if issue.auto_fixable and issue.confidence > 0.7:
                    optimized_config = self._apply_optimization(optimized_config, issue, agent_analyses)
            
            return optimized_config
            
        except Exception as e:
            logger.warning(f"Failed to generate optimized config: {str(e)}")
            return original_config
    
    def _apply_optimization(self, config: Dict[str, Any], 
                          issue: ValidationIssue, 
                          agent_analyses: List[AgentAnalysis]) -> Dict[str, Any]:
        """Apply a specific optimization to the configuration."""
        # This is a simplified implementation - in practice, you'd have more sophisticated optimization logic
        
        if issue.category == ValidationCategory.PROMPT_CLARITY:
            if "coordinator" in issue.location and "system_prompt" in issue.location:
                # Optimize coordinator prompt
                teams_info = self._extract_teams_info(config)
                optimized_prompt = self._generate_coordinator_prompt(teams_info)
                
                if 'coordinator' not in config:
                    config['coordinator'] = {}
                if 'prompts' not in config['coordinator']:
                    config['coordinator']['prompts'] = {}
                if 'system_prompt' not in config['coordinator']['prompts']:
                    config['coordinator']['prompts']['system_prompt'] = {}
                
                config['coordinator']['prompts']['system_prompt']['template'] = optimized_prompt
            
            elif "supervisor" in issue.location and "system_prompt" in issue.location:
                # Optimize supervisor prompt
                team_name = self._extract_team_name_from_location(issue.location)
                workers_info = self._extract_workers_info(config, team_name)
                optimized_prompt = self._generate_supervisor_prompt(team_name, workers_info)
                
                # Find and update the supervisor prompt
                for team in config.get('teams', []):
                    if team.get('name') == team_name:
                        if 'supervisor' not in team:
                            team['supervisor'] = {}
                        if 'prompts' not in team['supervisor']:
                            team['supervisor']['prompts'] = {}
                        if 'system_prompt' not in team['supervisor']['prompts']:
                            team['supervisor']['prompts']['system_prompt'] = {}
                        
                        team['supervisor']['prompts']['system_prompt']['template'] = optimized_prompt
                        break
        
        return config
    
    def _extract_teams_info(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract team information for coordinator prompt generation."""
        teams_info = []
        for team in config.get('teams', []):
            team_info = {
                'name': team.get('name', 'unnamed_team'),
                'description': team.get('description', 'No description'),
                'worker_count': len(team.get('workers', [])),
                'capabilities': []
            }
            
            # Extract worker capabilities
            for worker in team.get('workers', []):
                team_info['capabilities'].extend(worker.get('capabilities', []))
            
            teams_info.append(team_info)
        
        return teams_info
    
    def _extract_workers_info(self, config: Dict[str, Any], team_name: str) -> List[Dict[str, Any]]:
        """Extract worker information for supervisor prompt generation."""
        for team in config.get('teams', []):
            if team.get('name') == team_name:
                return team.get('workers', [])
        return []
    
    def _extract_team_name_from_location(self, location: str) -> str:
        """Extract team name from issue location path."""
        # Example location: "teams.main_team.supervisor.prompts.system_prompt"
        parts = location.split('.')
        if len(parts) >= 2 and parts[0] == 'teams':
            return parts[1]
        return 'unknown_team'
    
    def _generate_coordinator_prompt(self, teams_info: List[Dict[str, Any]]) -> str:
        """Generate an optimized coordinator system prompt."""
        teams_desc = "\n".join([
            f"- {team['name']}: {team['description']} ({team['worker_count']} workers) - Capabilities: {', '.join(set(team['capabilities']))}"
            for team in teams_info
        ])
        
        return f"""You are a team coordinator managing multiple specialized teams in a hierarchical structure.

Available teams:
{teams_desc}

Your primary responsibilities:
1. Analyze incoming requests to understand the task requirements
2. Determine which team is best suited for the task based on their capabilities
3. Route tasks to the appropriate team supervisor
4. Coordinate between teams when multi-team collaboration is needed
5. Provide final responses by synthesizing results from teams

Routing Decision Framework:
- Match task requirements to team capabilities
- Consider team workload and availability
- Route complex tasks that require multiple specializations to the most capable team
- Use fallback routing if no team is a perfect match

Always provide clear reasoning for your routing decisions and specific instructions for the selected team."""
    
    def _generate_supervisor_prompt(self, team_name: str, workers_info: List[Dict[str, Any]]) -> str:
        """Generate an optimized supervisor system prompt."""
        workers_desc = "\n".join([
            f"- {worker.get('name', 'unnamed_worker')}: {worker.get('description', 'No description')} - Capabilities: {', '.join(worker.get('capabilities', []))}"
            for worker in workers_info
        ])
        
        return f"""You are a supervisor for the {team_name} team, responsible for managing and coordinating worker agents.

Available workers:
{workers_desc}

Your key responsibilities:
1. Analyze tasks assigned to your team
2. Determine which worker is best suited for each task based on their specific capabilities
3. Delegate tasks with clear, specific instructions
4. Monitor task progress and coordinate between workers when needed
5. Provide consolidated responses from worker outputs

Worker Selection Criteria:
- Match task requirements to worker capabilities
- Consider worker specialization and expertise
- Balance workload across available workers
- Choose workers with the most relevant tools and skills

Task Delegation Best Practices:
- Provide clear, specific instructions to workers
- Include relevant context and requirements
- Set clear expectations for deliverables
- Monitor progress and provide guidance as needed

Always explain your reasoning for worker selection and provide detailed instructions for successful task completion."""
    
    def _calculate_overall_score(self, issues: List[ValidationIssue], num_agents: int) -> float:
        """Calculate overall configuration quality score (0-100)."""
        if num_agents == 0:
            return 0.0
        
        # Base score starts at 100
        score = 100.0
        
        # Deduct points based on issue severity
        severity_penalties = {
            ValidationSeverity.CRITICAL: 25.0,
            ValidationSeverity.HIGH: 15.0,
            ValidationSeverity.MEDIUM: 8.0,
            ValidationSeverity.LOW: 3.0,
            ValidationSeverity.INFO: 1.0
        }
        
        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 5.0)
            # Apply confidence weighting
            weighted_penalty = penalty * issue.confidence
            score -= weighted_penalty
        
        # Ensure score doesn't go below 0
        score = max(0.0, score)
        
        # Bonus for having more agents (more complex = higher expectations)
        complexity_bonus = min(5.0, num_agents * 1.0)
        if score > 80.0:  # Only apply bonus for already good configurations
            score += complexity_bonus
        
        return min(100.0, score)