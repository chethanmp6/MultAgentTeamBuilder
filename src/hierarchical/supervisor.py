"""
Supervisor Agent for Hierarchical Agent Teams
"""
from typing import Dict, Any, List, Optional, Literal
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ..core.configurable_agent import ConfigurableAgent
from .worker_agent import WorkerAgent


class SupervisorDecision(BaseModel):
    """Decision made by supervisor about which worker to route to."""
    next_worker: str
    reasoning: str = Field(description="Reason for choosing this worker")
    task_description: str = Field(description="Description of the task for the worker")


class SupervisorAgent:
    """A supervisor agent that coordinates worker agents."""
    
    def __init__(self, 
                 name: str = "supervisor",
                 config_file: str = None,
                 llm: BaseChatModel = None,
                 workers: List[WorkerAgent] = None,
                 system_prompt: str = None):
        """
        Initialize a supervisor agent.
        
        Args:
            name: Name of the supervisor agent
            config_file: Path to configuration file (optional)
            llm: Language model to use (optional)
            workers: List of available worker agents
            system_prompt: System prompt for the supervisor
        """
        self.name = name
        self.workers = workers or []
        self.worker_names = [worker.name for worker in self.workers]
        
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
        """Create default system prompt for supervisor."""
        worker_descriptions = []
        for worker in self.workers:
            worker_descriptions.append(f"- {worker.name}: {worker.description}")
        
        return f"""You are a supervisor tasked with managing a team of worker agents.

Available workers:
{chr(10).join(worker_descriptions)}

Your role is to:
1. Analyze incoming requests
2. Determine which worker is best suited for the task
3. Route the task to the appropriate worker
4. Coordinate between workers if needed
5. Provide final responses to users

When deciding which worker to use, consider:
- The specific skills and tools each worker has
- The nature of the request
- The complexity of the task
- Whether multiple workers might be needed

Always provide clear reasoning for your decisions."""
    
    def add_worker(self, worker: WorkerAgent):
        """Add a worker agent to the supervisor's team."""
        self.workers.append(worker)
        self.worker_names.append(worker.name)
        # Update system prompt with new worker
        self.system_prompt = self._create_default_system_prompt()
    
    def remove_worker(self, worker_name: str):
        """Remove a worker agent from the supervisor's team."""
        self.workers = [w for w in self.workers if w.name != worker_name]
        self.worker_names = [w.name for w in self.workers]
        # Update system prompt
        self.system_prompt = self._create_default_system_prompt()
    
    def decide_worker(self, input_text: str) -> SupervisorDecision:
        """Decide which worker should handle the request."""
        if not self.llm:
            raise ValueError("No LLM configured for supervisor agent")
        
        if not self.workers:
            raise ValueError("No workers available for supervisor to delegate to")
        
        # Create decision prompt
        decision_prompt = f"""Given the following user request, decide which worker should handle it.

User Request: {input_text}

Available Workers:
{chr(10).join([f"- {w.name}: {w.description}" for w in self.workers])}

Please analyze the request and choose the most appropriate worker. Consider:
1. The specific skills needed
2. The tools each worker has access to
3. The complexity of the task
4. Whether the task matches the worker's expertise

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
            # For now, use simple parsing - in production, use structured output
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Simple heuristic to choose worker based on keywords
            worker_choice = self._choose_worker_by_keywords(input_text, content)
            
            return SupervisorDecision(
                next_worker=worker_choice,
                reasoning=content,
                task_description=input_text
            )
            
        except Exception as e:
            # Fallback: choose first available worker
            return SupervisorDecision(
                next_worker=self.workers[0].name if self.workers else "none",
                reasoning=f"Error in decision making: {str(e)}. Using fallback worker.",
                task_description=input_text
            )
    
    def _choose_worker_by_keywords(self, input_text: str, reasoning: str) -> str:
        """Choose worker based on keywords in input and reasoning."""
        input_lower = input_text.lower()
        reasoning_lower = reasoning.lower()
        
        # Define keyword mappings for each worker type
        keyword_mappings = {
            "research": ["research", "search", "find", "information", "web", "lookup"],
            "coding": ["code", "program", "develop", "debug", "python", "function", "script"],
            "support": ["help", "support", "customer", "issue", "problem", "assist"],
            "writing": ["write", "document", "report", "content", "article", "text"],
            "analysis": ["analyze", "analyze", "data", "chart", "graph", "statistics"]
        }
        
        # Score each worker based on keywords
        worker_scores = {}
        for worker in self.workers:
            score = 0
            worker_lower = worker.name.lower()
            
            # Check for keyword matches
            for category, keywords in keyword_mappings.items():
                if category in worker_lower:
                    for keyword in keywords:
                        if keyword in input_lower or keyword in reasoning_lower:
                            score += 1
            
            worker_scores[worker.name] = score
        
        # Return worker with highest score, or first worker if no matches
        if worker_scores:
            best_worker = max(worker_scores.items(), key=lambda x: x[1])
            return best_worker[0] if best_worker[1] > 0 else self.workers[0].name
        
        return self.workers[0].name if self.workers else "none"
    
    def get_worker(self, worker_name: str) -> Optional[WorkerAgent]:
        """Get a worker agent by name."""
        for worker in self.workers:
            if worker.name == worker_name:
                return worker
        return None
    
    def list_workers(self) -> List[Dict[str, Any]]:
        """List all available workers with their information."""
        worker_info = []
        for worker in self.workers:
            info = {
                "name": worker.name,
                "description": worker.description,
                "tools": worker.get_available_tools(),
                "config": worker.get_config() is not None
            }
            worker_info.append(info)
        return worker_info
    
    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Run the supervisor with given input."""
        # Decide which worker should handle the request
        decision = self.decide_worker(input_text)
        
        # Get the chosen worker
        worker = self.get_worker(decision.next_worker)
        if not worker:
            return {
                "error": f"Worker '{decision.next_worker}' not found",
                "response": f"Error: Worker '{decision.next_worker}' is not available",
                "decision": decision.dict(),
                "metadata": kwargs
            }
        
        # Run the worker with the task
        worker_response = worker.run(input_text, **kwargs)
        
        return {
            "response": worker_response.get("response", "No response from worker"),
            "worker_used": decision.next_worker,
            "decision_reasoning": decision.reasoning,
            "worker_response": worker_response,
            "metadata": kwargs
        }
    
    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Async version of run."""
        # For now, run synchronously
        return self.run(input_text, **kwargs)
    
    def __str__(self) -> str:
        return f"SupervisorAgent(name='{self.name}', workers={len(self.workers)})"
    
    def __repr__(self) -> str:
        return self.__str__() 