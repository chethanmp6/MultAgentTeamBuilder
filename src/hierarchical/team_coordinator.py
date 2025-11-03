"""
Team Coordinator for Hierarchical Agent Teams
"""
from typing import Dict, Any, List, Optional, Literal
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from ..core.configurable_agent import ConfigurableAgent
from .supervisor import SupervisorAgent
from .worker_agent import WorkerAgent


class TeamDecision(BaseModel):
    """Decision made by team coordinator about which team to route to."""
    next_team: str
    reasoning: str = Field(description="Reason for choosing this team")
    task_description: str = Field(description="Description of the task for the team")


class TeamCoordinator:
    """A team coordinator that manages multiple teams in a hierarchical structure."""
    
    def __init__(self, 
                 name: str = "coordinator",
                 config_file: str = None,
                 llm: BaseChatModel = None,
                 teams: Dict[str, SupervisorAgent] = None,
                 system_prompt: str = None):
        """
        Initialize a team coordinator.
        
        Args:
            name: Name of the coordinator
            config_file: Path to configuration file (optional)
            llm: Language model to use (optional)
            teams: Dictionary of team names to supervisor agents
            system_prompt: System prompt for the coordinator
        """
        self.name = name
        self.teams = teams or {}
        self.team_names = list(self.teams.keys())
        
        # Initialize from config file if provided
        if config_file:
            self.agent = ConfigurableAgent(config_file)
            self.llm = self.agent.llm
            self.system_prompt = self.agent.system_prompt
        else:
            # Initialize with provided components
            self.agent = None
            self.llm = llm
            self.system_prompt = system_prompt or self._create_default_system_prompt()
    
    def _create_default_system_prompt(self) -> str:
        """Create default system prompt for coordinator."""
        team_descriptions = []
        for team_name, supervisor in self.teams.items():
            worker_count = len(supervisor.workers)
            team_descriptions.append(f"- {team_name}: {worker_count} workers")
        
        return f"""You are a team coordinator managing multiple specialized teams.

Available teams:
{chr(10).join(team_descriptions)}

Your role is to:
1. Analyze incoming requests
2. Determine which team is best suited for the task
3. Route the task to the appropriate team
4. Coordinate between teams if needed
5. Provide final responses to users

When deciding which team to use, consider:
- The specific capabilities of each team
- The nature of the request
- The complexity of the task
- Whether multiple teams might be needed

Always provide clear reasoning for your decisions."""
    
    def add_team(self, team_name: str, supervisor: SupervisorAgent):
        """Add a team to the coordinator."""
        self.teams[team_name] = supervisor
        self.team_names.append(team_name)
        # Update system prompt with new team
        self.system_prompt = self._create_default_system_prompt()
    
    def remove_team(self, team_name: str):
        """Remove a team from the coordinator."""
        if team_name in self.teams:
            del self.teams[team_name]
            self.team_names = list(self.teams.keys())
            # Update system prompt
            self.system_prompt = self._create_default_system_prompt()
    
    def decide_team(self, input_text: str) -> TeamDecision:
        """Decide which team should handle the request."""
        if not self.llm:
            raise ValueError("No LLM configured for team coordinator")
        
        if not self.teams:
            raise ValueError("No teams available for coordinator to delegate to")
        
        # Create decision prompt
        team_info = []
        for team_name, supervisor in self.teams.items():
            workers = supervisor.list_workers()
            worker_descriptions = [f"{w['name']}: {w['description']}" for w in workers]
            team_info.append(f"- {team_name}: {', '.join(worker_descriptions)}")
        
        decision_prompt = f"""Given the following user request, decide which team should handle it.

User Request: {input_text}

Available Teams:
{chr(10).join(team_info)}

Please analyze the request and choose the most appropriate team. Consider:
1. The specific skills needed
2. The capabilities of each team
3. The complexity of the task
4. Whether the task matches the team's expertise

Provide your decision with reasoning."""
        
        # Prepare messages
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=decision_prompt)
        ]
        
        try:
            # Get structured output for decision
            response = self.llm.invoke(messages)
            
            # Parse response to extract decision
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Simple heuristic to choose team based on keywords
            team_choice = self._choose_team_by_keywords(input_text, content)
            
            return TeamDecision(
                next_team=team_choice,
                reasoning=content,
                task_description=input_text
            )
            
        except Exception as e:
            # Fallback: choose first available team
            return TeamDecision(
                next_team=self.team_names[0] if self.team_names else "none",
                reasoning=f"Error in decision making: {str(e)}. Using fallback team.",
                task_description=input_text
            )
    
    def _choose_team_by_keywords(self, input_text: str, reasoning: str) -> str:
        """Choose team based on keywords in input and reasoning."""
        input_lower = input_text.lower()
        reasoning_lower = reasoning.lower()
        
        # Define keyword mappings for each team type
        keyword_mappings = {
            "research": ["research", "search", "find", "information", "web", "lookup", "investigate"],
            "development": ["code", "program", "develop", "debug", "python", "function", "script", "build"],
            "support": ["help", "support", "customer", "issue", "problem", "assist", "troubleshoot"],
            "writing": ["write", "document", "report", "content", "article", "text", "create"],
            "analysis": ["analyze", "analyze", "data", "chart", "graph", "statistics", "examine"]
        }
        
        # Score each team based on keywords
        team_scores = {}
        for team_name in self.teams:
            score = 0
            team_lower = team_name.lower()
            
            # Check for keyword matches
            for category, keywords in keyword_mappings.items():
                if category in team_lower:
                    for keyword in keywords:
                        if keyword in input_lower or keyword in reasoning_lower:
                            score += 1
            
            team_scores[team_name] = score
        
        # Return team with highest score, or first team if no matches
        if team_scores:
            best_team = max(team_scores.items(), key=lambda x: x[1])
            return best_team[0] if best_team[1] > 0 else self.team_names[0]
        
        return self.team_names[0] if self.team_names else "none"
    
    def get_team(self, team_name: str) -> Optional[SupervisorAgent]:
        """Get a team by name."""
        return self.teams.get(team_name)
    
    def list_teams(self) -> List[Dict[str, Any]]:
        """List all available teams with their information."""
        team_info = []
        for team_name, supervisor in self.teams.items():
            workers = supervisor.list_workers()
            info = {
                "name": team_name,
                "supervisor": supervisor.name,
                "worker_count": len(workers),
                "workers": workers
            }
            team_info.append(info)
        return team_info
    
    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run the coordinator with given input."""
        # Decide which team should handle the request
        decision = self.decide_team(input_text)
        
        # Get the chosen team
        team = self.get_team(decision.next_team)
        if not team:
            return {
                "error": f"Team '{decision.next_team}' not found",
                "response": f"Error: Team '{decision.next_team}' is not available",
                "decision": decision.dict(),
                "metadata": kwargs
            }
        
        # Run the team with the task
        team_response = team.run(input_text, **kwargs)
        
        return {
            "response": team_response.get("response", "No response from team"),
            "team_used": decision.next_team,
            "decision_reasoning": decision.reasoning,
            "team_response": team_response,
            "metadata": kwargs
        }
    
    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Async version of run."""
        # For now, run synchronously
        return self.run(input_text, **kwargs)
    
    def get_all_workers(self) -> List[WorkerAgent]:
        """Get all workers from all teams."""
        all_workers = []
        for supervisor in self.teams.values():
            all_workers.extend(supervisor.workers)
        return all_workers
    
    def __str__(self) -> str:
        return f"TeamCoordinator(name='{self.name}', teams={len(self.teams)})"
    
    def __repr__(self) -> str:
        return self.__str__() 