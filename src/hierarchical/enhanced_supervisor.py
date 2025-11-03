"""
Enhanced Supervisor Agent with improved routing capabilities.
Uses the EnhancedRoutingEngine for better decision-making.
"""
from typing import Dict, Any, List, Optional, Literal
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import time
from datetime import datetime

from ..core.configurable_agent import ConfigurableAgent
from .worker_agent import WorkerAgent
from .enhanced_routing import (
    EnhancedRoutingEngine, 
    RoutingStrategy, 
    AgentCapability,
    RoutingDecision
)


class EnhancedSupervisorDecision(BaseModel):
    """Enhanced decision made by supervisor about which worker to route to."""
    next_worker: str
    reasoning: str = Field(description="Detailed reason for choosing this worker")
    confidence: float = Field(description="Confidence level (0-1) in this decision")
    task_description: str = Field(description="Description of the task for the worker")
    alternative_workers: List[str] = Field(default=[], description="Alternative worker options")
    strategy_used: str = Field(description="Routing strategy used for this decision")
    metadata: Dict[str, Any] = Field(default={}, description="Additional decision metadata")


class EnhancedSupervisorAgent:
    """Enhanced supervisor agent with intelligent routing capabilities."""
    
    def __init__(self, 
                 name: str = "enhanced_supervisor",
                 config_file: str = None,
                 llm: BaseChatModel = None,
                 workers: List[WorkerAgent] = None,
                 system_prompt: str = None,
                 routing_strategy: RoutingStrategy = RoutingStrategy.HYBRID,
                 routing_config: Dict[str, Any] = None):
        """
        Initialize an enhanced supervisor agent.
        
        Args:
            name: Name of the supervisor agent
            config_file: Path to configuration file (optional)
            llm: Language model to use (optional)
            workers: List of available worker agents
            system_prompt: System prompt for the supervisor
            routing_strategy: Default routing strategy to use
            routing_config: Configuration for routing engine
        """
        self.name = name
        self.workers = workers or []
        self.worker_names = [worker.name for worker in self.workers]
        self.routing_strategy = routing_strategy
        self.routing_config = routing_config or {}
        
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
        
        # Initialize enhanced routing engine
        self.routing_engine = EnhancedRoutingEngine(
            llm=self.llm,
            default_strategy=routing_strategy
        )
        
        # Register workers with routing engine
        self._register_workers_with_routing_engine()
        
        # Performance tracking
        self.task_history: List[Dict[str, Any]] = []
        self.decision_history: List[EnhancedSupervisorDecision] = []
    
    def _create_default_system_prompt(self) -> str:
        """Create default system prompt for enhanced supervisor."""
        worker_descriptions = []
        for worker in self.workers:
            capabilities = worker.get_available_tools() if hasattr(worker, 'get_available_tools') else []
            worker_descriptions.append(
                f"- {worker.name}: {worker.description} (Capabilities: {', '.join(capabilities)})"
            )
        
        return f"""You are an Enhanced Supervisor Agent managing a team of specialized worker agents.

Your role involves:
1. Intelligent task analysis and routing
2. Performance monitoring and optimization
3. Load balancing across workers
4. Quality assurance and coordination
5. Continuous learning from routing decisions

Available Workers:
{chr(10).join(worker_descriptions)}

You use advanced routing algorithms to ensure:
- Tasks are matched to the most capable workers
- Workload is distributed efficiently
- Performance metrics are considered
- Historical success patterns inform decisions

When making routing decisions, consider:
- Worker specialization and capabilities
- Current workload and availability
- Historical performance and success rates
- Task complexity and requirements
- Priority and urgency levels

Always provide clear reasoning for your routing decisions and maintain high confidence in your choices."""
    
    def _register_workers_with_routing_engine(self):
        """Register all workers with the routing engine."""
        for worker in self.workers:
            # Extract worker capabilities
            capabilities = []
            if hasattr(worker, 'get_available_tools'):
                capabilities.extend(worker.get_available_tools())
            
            # Try to extract capabilities from config if available
            if hasattr(worker, 'get_config') and worker.get_config():
                config = worker.get_config()
                if hasattr(config, 'tools') and config.tools:
                    capabilities.extend(config.tools.built_in)
            
            # Create specialization keywords from description
            specialization_keywords = []
            if hasattr(worker, 'description') and worker.description:
                # Simple keyword extraction from description
                words = worker.description.lower().split()
                specialization_keywords = [word for word in words if len(word) > 3]
            
            # Register with routing engine
            agent_capability = AgentCapability(
                agent_id=worker.name,
                capabilities=capabilities,
                specialization_keywords=specialization_keywords,
                priority=getattr(worker, 'priority', 1)
            )
            
            self.routing_engine.register_agent(agent_capability)
    
    def add_worker(self, worker: WorkerAgent):
        """Add a worker agent to the supervisor's team."""
        self.workers.append(worker)
        self.worker_names.append(worker.name)
        
        # Register with routing engine
        capabilities = worker.get_available_tools() if hasattr(worker, 'get_available_tools') else []
        specialization_keywords = []
        if hasattr(worker, 'description'):
            words = worker.description.lower().split()
            specialization_keywords = [word for word in words if len(word) > 3]
        
        agent_capability = AgentCapability(
            agent_id=worker.name,
            capabilities=capabilities,
            specialization_keywords=specialization_keywords,
            priority=getattr(worker, 'priority', 1)
        )
        
        self.routing_engine.register_agent(agent_capability)
        
        # Update system prompt
        self.system_prompt = self._create_default_system_prompt()
    
    def remove_worker(self, worker_name: str):
        """Remove a worker agent from the supervisor's team."""
        self.workers = [w for w in self.workers if w.name != worker_name]
        self.worker_names = [w.name for w in self.workers]
        
        # Remove from routing engine (would need to implement in routing engine)
        # For now, we'll just update the system prompt
        self.system_prompt = self._create_default_system_prompt()
    
    def decide_worker(self, 
                     input_text: str, 
                     context: Optional[Dict[str, Any]] = None,
                     strategy: Optional[RoutingStrategy] = None) -> EnhancedSupervisorDecision:
        """Enhanced decision making using the routing engine."""
        if not self.workers:
            raise ValueError("No workers available for supervisor to delegate to")
        
        context = context or {}
        strategy = strategy or self.routing_strategy
        
        # Add supervisor context
        context.update({
            'supervisor': self.name,
            'timestamp': datetime.now().isoformat(),
            'available_workers': len(self.workers),
            'task_length': len(input_text)
        })
        
        # Use routing engine for decision
        routing_decision = self.routing_engine.route_task(
            task_description=input_text,
            available_agents=self.worker_names,
            strategy=strategy,
            context=context
        )
        
        # Convert to supervisor decision format
        enhanced_decision = EnhancedSupervisorDecision(
            next_worker=routing_decision.target,
            confidence=routing_decision.confidence,
            reasoning=routing_decision.reasoning,
            task_description=input_text,
            alternative_workers=[alt[0] for alt in routing_decision.alternative_targets],
            strategy_used=routing_decision.strategy_used.value,
            metadata=routing_decision.metadata
        )
        
        # Store decision history
        self.decision_history.append(enhanced_decision)
        
        return enhanced_decision
    
    def get_worker(self, worker_name: str) -> Optional[WorkerAgent]:
        """Get a worker agent by name."""
        for worker in self.workers:
            if worker.name == worker_name:
                return worker
        return None
    
    def list_workers(self) -> List[Dict[str, Any]]:
        """List all available workers with enhanced information."""
        worker_info = []
        for worker in self.workers:
            # Get routing engine information
            agent_capability = self.routing_engine.agent_capabilities.get(worker.name)
            
            info = {
                "name": worker.name,
                "description": getattr(worker, 'description', 'No description'),
                "tools": worker.get_available_tools() if hasattr(worker, 'get_available_tools') else [],
                "config": worker.get_config() is not None if hasattr(worker, 'get_config') else False,
                "availability": agent_capability.availability if agent_capability else 1.0,
                "performance_score": agent_capability.performance_score if agent_capability else 1.0,
                "current_workload": agent_capability.current_workload if agent_capability else 0,
                "capabilities": agent_capability.capabilities if agent_capability else []
            }
            worker_info.append(info)
        return worker_info
    
    def run(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Enhanced run method with performance tracking."""
        start_time = time.time()
        
        # Enhanced decision making
        context = kwargs.get('context', {})
        context.update({
            'priority': kwargs.get('priority', 'normal'),
            'complexity': kwargs.get('complexity', 'medium'),
            'expected_response_time': kwargs.get('expected_response_time', 60)
        })
        
        # Make routing decision
        decision = self.decide_worker(input_text, context=context)
        
        # Get the chosen worker
        worker = self.get_worker(decision.next_worker)
        if not worker:
            return {
                "error": f"Worker '{decision.next_worker}' not found",
                "response": f"Error: Worker '{decision.next_worker}' is not available",
                "decision": decision.model_dump(),
                "metadata": kwargs
            }
        
        # Update workload
        self.routing_engine.update_agent_workload(decision.next_worker, 1)
        
        try:
            # Run the worker with the task
            worker_response = worker.run(input_text, **kwargs)
            
            # Calculate performance metrics
            response_time = time.time() - start_time
            success = not worker_response.get('error')
            
            # Update performance metrics
            self.routing_engine.update_agent_performance(
                decision.next_worker, 
                response_time, 
                success
            )
            
            # Store task history
            task_record = {
                'timestamp': datetime.now().isoformat(),
                'input': input_text,
                'worker_used': decision.next_worker,
                'response_time': response_time,
                'success': success,
                'confidence': decision.confidence,
                'strategy': decision.strategy_used
            }
            self.task_history.append(task_record)
            
            return {
                "response": worker_response.get("response", "No response from worker"),
                "worker_used": decision.next_worker,
                "confidence": decision.confidence,
                "strategy_used": decision.strategy_used,
                "decision_reasoning": decision.reasoning,
                "alternative_workers": decision.alternative_workers,
                "response_time": response_time,
                "worker_response": worker_response,
                "metadata": kwargs,
                "enhanced_metadata": {
                    "routing_metadata": decision.metadata,
                    "performance_score": self.routing_engine.agent_capabilities[decision.next_worker].performance_score
                }
            }
            
        except Exception as e:
            # Update failure metrics
            response_time = time.time() - start_time
            self.routing_engine.update_agent_performance(decision.next_worker, response_time, False)
            
            return {
                "error": f"Worker execution error: {str(e)}",
                "response": f"Error executing task with {decision.next_worker}: {str(e)}",
                "worker_used": decision.next_worker,
                "confidence": decision.confidence,
                "strategy_used": decision.strategy_used,
                "decision_reasoning": decision.reasoning,
                "response_time": response_time,
                "metadata": kwargs
            }
        
        finally:
            # Decrease workload
            self.routing_engine.update_agent_workload(decision.next_worker, -1)
    
    async def arun(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """Async version of enhanced run."""
        # For now, run synchronously
        # In a production system, this would be properly async
        return self.run(input_text, **kwargs)
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if not self.task_history:
            return {"message": "No task history available"}
        
        total_tasks = len(self.task_history)
        successful_tasks = sum(1 for task in self.task_history if task['success'])
        average_response_time = sum(task['response_time'] for task in self.task_history) / total_tasks
        average_confidence = sum(task['confidence'] for task in self.task_history) / total_tasks
        
        # Worker utilization
        worker_usage = {}
        for task in self.task_history:
            worker = task['worker_used']
            worker_usage[worker] = worker_usage.get(worker, 0) + 1
        
        # Strategy usage
        strategy_usage = {}
        for task in self.task_history:
            strategy = task['strategy']
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "success_rate": successful_tasks / total_tasks,
            "average_response_time": average_response_time,
            "average_confidence": average_confidence,
            "worker_utilization": worker_usage,
            "strategy_distribution": strategy_usage,
            "routing_statistics": self.routing_engine.get_routing_statistics(),
            "recent_decisions": [d.model_dump() for d in self.decision_history[-5:]]
        }
    
    def optimize_routing(self, strategy: Optional[RoutingStrategy] = None) -> Dict[str, Any]:
        """Optimize routing based on historical performance."""
        if strategy:
            self.routing_strategy = strategy
            return {"message": f"Routing strategy updated to {strategy.value}"}
        
        # Analyze historical performance to suggest optimization
        stats = self.get_performance_statistics()
        
        suggestions = []
        
        # Analyze strategy effectiveness
        if 'strategy_distribution' in stats:
            for strategy_name, usage_count in stats['strategy_distribution'].items():
                # Get success rate for this strategy
                strategy_tasks = [t for t in self.task_history if t['strategy'] == strategy_name]
                if strategy_tasks:
                    strategy_success_rate = sum(1 for t in strategy_tasks if t['success']) / len(strategy_tasks)
                    if strategy_success_rate < 0.8:
                        suggestions.append(f"Consider reducing usage of {strategy_name} strategy (success rate: {strategy_success_rate:.2f})")
        
        # Analyze worker performance
        if 'worker_utilization' in stats:
            routing_stats = self.routing_engine.get_routing_statistics()
            for worker_name, usage_count in stats['worker_utilization'].items():
                if worker_name in self.routing_engine.agent_capabilities:
                    agent = self.routing_engine.agent_capabilities[worker_name]
                    if agent.performance_score < 0.7:
                        suggestions.append(f"Worker {worker_name} has low performance score ({agent.performance_score:.2f})")
        
        return {
            "current_strategy": self.routing_strategy.value,
            "performance_stats": stats,
            "optimization_suggestions": suggestions
        }
    
    def __str__(self) -> str:
        return f"EnhancedSupervisorAgent(name='{self.name}', workers={len(self.workers)}, strategy={self.routing_strategy.value})"
    
    def __repr__(self) -> str:
        return self.__str__()