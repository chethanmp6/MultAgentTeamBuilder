"""
Enhanced routing algorithms for hierarchical agent teams.
Provides sophisticated decision-making capabilities for routing tasks to the most appropriate agents.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
import re
from dataclasses import dataclass
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Available routing strategies."""
    KEYWORD_BASED = "keyword_based"
    LLM_BASED = "llm_based"  
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"
    CAPABILITY_BASED = "capability_based"
    WORKLOAD_BASED = "workload_based"
    PERFORMANCE_BASED = "performance_based"


@dataclass
class RoutingDecision:
    """Represents a routing decision with confidence and reasoning."""
    target: str
    confidence: float
    reasoning: str
    strategy_used: RoutingStrategy
    alternative_targets: List[Tuple[str, float]] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.alternative_targets is None:
            self.alternative_targets = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentCapability:
    """Represents an agent's capabilities and current state."""
    agent_id: str
    capabilities: List[str]
    current_workload: int = 0
    max_workload: int = 10
    average_response_time: float = 0.0
    success_rate: float = 1.0
    specialization_keywords: List[str] = None
    priority: int = 1
    
    def __post_init__(self):
        if self.specialization_keywords is None:
            self.specialization_keywords = []
    
    @property
    def availability(self) -> float:
        """Calculate agent availability (0-1)."""
        if self.max_workload == 0:
            return 0.0
        return max(0.0, 1.0 - (self.current_workload / self.max_workload))
    
    @property
    def performance_score(self) -> float:
        """Calculate overall performance score (0-1)."""
        # Combine success rate, response time (inverted), and availability
        time_score = max(0.0, 1.0 - (self.average_response_time / 60.0))  # Normalize to 60s max
        return (self.success_rate * 0.5) + (time_score * 0.2) + (self.availability * 0.3)


class EnhancedRoutingEngine:
    """Enhanced routing engine with multiple strategies and intelligent decision-making."""
    
    def __init__(self, 
                 llm: Optional[BaseChatModel] = None,
                 default_strategy: RoutingStrategy = RoutingStrategy.HYBRID):
        self.llm = llm
        self.default_strategy = default_strategy
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.routing_history: List[RoutingDecision] = []
        self.keyword_mappings = self._build_default_keyword_mappings()
        self.rule_engine = self._build_default_rules()
    
    def register_agent(self, agent_capability: AgentCapability):
        """Register an agent with its capabilities."""
        self.agent_capabilities[agent_capability.agent_id] = agent_capability
        logger.info(f"Registered agent: {agent_capability.agent_id}")
    
    def update_agent_workload(self, agent_id: str, workload_change: int):
        """Update an agent's current workload."""
        if agent_id in self.agent_capabilities:
            self.agent_capabilities[agent_id].current_workload += workload_change
            self.agent_capabilities[agent_id].current_workload = max(0, 
                self.agent_capabilities[agent_id].current_workload)
    
    def update_agent_performance(self, agent_id: str, response_time: float, success: bool):
        """Update an agent's performance metrics."""
        if agent_id not in self.agent_capabilities:
            return
        
        agent = self.agent_capabilities[agent_id]
        
        # Update rolling average response time
        if agent.average_response_time == 0:
            agent.average_response_time = response_time
        else:
            agent.average_response_time = (agent.average_response_time * 0.8) + (response_time * 0.2)
        
        # Update success rate
        if success:
            agent.success_rate = (agent.success_rate * 0.9) + 0.1
        else:
            agent.success_rate = agent.success_rate * 0.9
        
        agent.success_rate = max(0.1, min(1.0, agent.success_rate))
    
    def route_task(self, 
                   task_description: str,
                   available_agents: List[str],
                   strategy: Optional[RoutingStrategy] = None,
                   context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """Route a task to the most appropriate agent."""
        
        if not available_agents:
            raise ValueError("No available agents for routing")
        
        strategy = strategy or self.default_strategy
        context = context or {}
        
        # Filter to only available agents that are registered
        valid_agents = [agent_id for agent_id in available_agents 
                       if agent_id in self.agent_capabilities]
        
        if not valid_agents:
            raise ValueError("No valid registered agents available for routing")
        
        decision = None
        
        try:
            if strategy == RoutingStrategy.KEYWORD_BASED:
                decision = self._keyword_based_routing(task_description, valid_agents, context)
            elif strategy == RoutingStrategy.LLM_BASED:
                decision = self._llm_based_routing(task_description, valid_agents, context)
            elif strategy == RoutingStrategy.RULE_BASED:
                decision = self._rule_based_routing(task_description, valid_agents, context)
            elif strategy == RoutingStrategy.CAPABILITY_BASED:
                decision = self._capability_based_routing(task_description, valid_agents, context)
            elif strategy == RoutingStrategy.WORKLOAD_BASED:
                decision = self._workload_based_routing(task_description, valid_agents, context)
            elif strategy == RoutingStrategy.PERFORMANCE_BASED:
                decision = self._performance_based_routing(task_description, valid_agents, context)
            elif strategy == RoutingStrategy.HYBRID:
                decision = self._hybrid_routing(task_description, valid_agents, context)
            else:
                raise ValueError(f"Unknown routing strategy: {strategy}")
        
        except Exception as e:
            logger.error(f"Error in routing strategy {strategy}: {e}")
            # Fallback to simple round-robin
            decision = RoutingDecision(
                target=self._round_robin_fallback(valid_agents),
                confidence=0.3,
                reasoning=f"Fallback routing due to error: {str(e)}",
                strategy_used=strategy,
                metadata={"error": str(e)}
            )
        
        # Store decision in history
        self.routing_history.append(decision)
        logger.info(f"Routed task to {decision.target} with {decision.confidence:.2f} confidence")
        
        return decision
    
    def _keyword_based_routing(self, task: str, agents: List[str], context: Dict) -> RoutingDecision:
        """Route based on keyword matching."""
        task_lower = task.lower()
        agent_scores = {}
        
        for agent_id in agents:
            score = 0
            agent = self.agent_capabilities[agent_id]
            
            # Score based on capability keywords
            for capability in agent.capabilities:
                if capability.lower() in task_lower:
                    score += 2
            
            # Score based on specialization keywords
            for keyword in agent.specialization_keywords:
                if keyword.lower() in task_lower:
                    score += 3
            
            # Check keyword mappings
            for category, keywords in self.keyword_mappings.items():
                if category in [cap.lower() for cap in agent.capabilities]:
                    for keyword in keywords:
                        if keyword in task_lower:
                            score += 1
            
            agent_scores[agent_id] = score
        
        # Find best match
        best_agent = max(agent_scores.keys(), key=lambda x: agent_scores[x])
        max_score = agent_scores[best_agent]
        
        # Calculate confidence based on score difference
        second_best_score = sorted(agent_scores.values())[-2] if len(agent_scores) > 1 else 0
        confidence = min(0.9, max_score / max(1, max_score + second_best_score))
        
        # Prepare alternatives
        alternatives = [(agent, score) for agent, score in 
                       sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)[1:3]]
        
        return RoutingDecision(
            target=best_agent,
            confidence=confidence,
            reasoning=f"Keyword matching: {max_score} points for {best_agent}",
            strategy_used=RoutingStrategy.KEYWORD_BASED,
            alternative_targets=alternatives,
            metadata={"scores": agent_scores}
        )
    
    def _llm_based_routing(self, task: str, agents: List[str], context: Dict) -> RoutingDecision:
        """Route using LLM analysis."""
        if not self.llm:
            raise ValueError("LLM not available for LLM-based routing")
        
        # Prepare agent descriptions
        agent_descriptions = []
        for agent_id in agents:
            agent = self.agent_capabilities[agent_id]
            agent_descriptions.append(
                f"- {agent_id}: Capabilities: {', '.join(agent.capabilities)}, "
                f"Availability: {agent.availability:.2f}, "
                f"Performance: {agent.performance_score:.2f}"
            )
        
        system_prompt = """You are an intelligent task router. Analyze the task and available agents to make the best routing decision.

Consider:
1. Agent capabilities and task requirements
2. Agent availability and current workload  
3. Agent performance history
4. Task complexity and urgency

Respond with a JSON object containing:
{
  "chosen_agent": "agent_id",
  "confidence": 0.0-1.0,
  "reasoning": "explanation of choice",
  "alternatives": ["agent_id1", "agent_id2"]
}"""
        
        user_prompt = f"""Task: {task}

Available Agents:
{chr(10).join(agent_descriptions)}

Context: {json.dumps(context, indent=2)}

Choose the best agent for this task."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                chosen_agent = result.get('chosen_agent')
                confidence = float(result.get('confidence', 0.5))
                reasoning = result.get('reasoning', 'LLM decision')
                alternatives = result.get('alternatives', [])
                
                if chosen_agent in agents:
                    return RoutingDecision(
                        target=chosen_agent,
                        confidence=confidence,
                        reasoning=reasoning,
                        strategy_used=RoutingStrategy.LLM_BASED,
                        alternative_targets=[(alt, 0.5) for alt in alternatives[:2]],
                        metadata={"llm_response": response_text}
                    )
            except json.JSONDecodeError:
                pass
            
            # Fallback parsing
            chosen_agent = self._extract_agent_from_text(response_text, agents)
            return RoutingDecision(
                target=chosen_agent,
                confidence=0.6,
                reasoning=f"LLM analysis: {response_text[:200]}...",
                strategy_used=RoutingStrategy.LLM_BASED,
                metadata={"llm_response": response_text}
            )
            
        except Exception as e:
            logger.error(f"LLM routing error: {e}")
            raise
    
    def _rule_based_routing(self, task: str, agents: List[str], context: Dict) -> RoutingDecision:
        """Route based on predefined rules."""
        task_lower = task.lower()
        
        for rule in self.rule_engine:
            if rule['condition'](task_lower, context):
                for agent_id in agents:
                    agent = self.agent_capabilities[agent_id]
                    if rule['agent_filter'](agent):
                        return RoutingDecision(
                            target=agent_id,
                            confidence=rule['confidence'],
                            reasoning=rule['reasoning'],
                            strategy_used=RoutingStrategy.RULE_BASED,
                            metadata={"rule": rule['name']}
                        )
        
        # No rules matched, use first available agent
        return RoutingDecision(
            target=agents[0],
            confidence=0.3,
            reasoning="No rules matched, using first available agent",
            strategy_used=RoutingStrategy.RULE_BASED
        )
    
    def _capability_based_routing(self, task: str, agents: List[str], context: Dict) -> RoutingDecision:
        """Route based on capability matching and specialization."""
        task_keywords = self._extract_task_keywords(task)
        agent_scores = {}
        
        for agent_id in agents:
            agent = self.agent_capabilities[agent_id]
            score = 0
            
            # Perfect capability matches
            for keyword in task_keywords:
                if keyword in [cap.lower() for cap in agent.capabilities]:
                    score += 5
            
            # Specialization bonus
            for spec in agent.specialization_keywords:
                if spec.lower() in task.lower():
                    score += 3
            
            # Priority bonus
            score += agent.priority
            
            agent_scores[agent_id] = score
        
        best_agent = max(agent_scores.keys(), key=lambda x: agent_scores[x])
        max_score = agent_scores[best_agent]
        
        confidence = min(0.95, max_score / (max_score + 3))  # Normalize
        
        return RoutingDecision(
            target=best_agent,
            confidence=confidence,
            reasoning=f"Best capability match with score {max_score}",
            strategy_used=RoutingStrategy.CAPABILITY_BASED,
            metadata={"scores": agent_scores}
        )
    
    def _workload_based_routing(self, task: str, agents: List[str], context: Dict) -> RoutingDecision:
        """Route based on current workload and availability."""
        # Sort agents by availability (highest first)
        available_agents = [(agent_id, self.agent_capabilities[agent_id].availability) 
                           for agent_id in agents]
        available_agents.sort(key=lambda x: x[1], reverse=True)
        
        best_agent, availability = available_agents[0]
        
        confidence = availability * 0.8  # Lower confidence for pure workload routing
        
        return RoutingDecision(
            target=best_agent,
            confidence=confidence,
            reasoning=f"Best availability: {availability:.2f}",
            strategy_used=RoutingStrategy.WORKLOAD_BASED,
            alternative_targets=available_agents[1:3],
            metadata={"availabilities": dict(available_agents)}
        )
    
    def _performance_based_routing(self, task: str, agents: List[str], context: Dict) -> RoutingDecision:
        """Route based on historical performance."""
        # Sort agents by performance score
        performance_agents = [(agent_id, self.agent_capabilities[agent_id].performance_score) 
                             for agent_id in agents]
        performance_agents.sort(key=lambda x: x[1], reverse=True)
        
        best_agent, performance = performance_agents[0]
        
        confidence = performance * 0.9
        
        return RoutingDecision(
            target=best_agent,
            confidence=confidence,
            reasoning=f"Best performance score: {performance:.2f}",
            strategy_used=RoutingStrategy.PERFORMANCE_BASED,
            alternative_targets=performance_agents[1:3],
            metadata={"performance_scores": dict(performance_agents)}
        )
    
    def _hybrid_routing(self, task: str, agents: List[str], context: Dict) -> RoutingDecision:
        """Combine multiple strategies for optimal routing."""
        # Get decisions from multiple strategies
        strategies_to_combine = [
            RoutingStrategy.CAPABILITY_BASED,
            RoutingStrategy.PERFORMANCE_BASED,
            RoutingStrategy.WORKLOAD_BASED,
            RoutingStrategy.KEYWORD_BASED
        ]
        
        strategy_decisions = {}
        for strategy in strategies_to_combine:
            try:
                if strategy == RoutingStrategy.CAPABILITY_BASED:
                    decision = self._capability_based_routing(task, agents, context)
                elif strategy == RoutingStrategy.PERFORMANCE_BASED:
                    decision = self._performance_based_routing(task, agents, context)
                elif strategy == RoutingStrategy.WORKLOAD_BASED:
                    decision = self._workload_based_routing(task, agents, context)
                elif strategy == RoutingStrategy.KEYWORD_BASED:
                    decision = self._keyword_based_routing(task, agents, context)
                
                strategy_decisions[strategy] = decision
            except Exception as e:
                logger.warning(f"Strategy {strategy} failed in hybrid routing: {e}")
        
        # Weight and combine decisions
        strategy_weights = {
            RoutingStrategy.CAPABILITY_BASED: 0.4,
            RoutingStrategy.PERFORMANCE_BASED: 0.3,
            RoutingStrategy.WORKLOAD_BASED: 0.2,
            RoutingStrategy.KEYWORD_BASED: 0.1
        }
        
        agent_weighted_scores = {}
        
        for agent_id in agents:
            weighted_score = 0
            for strategy, decision in strategy_decisions.items():
                weight = strategy_weights.get(strategy, 0)
                if decision.target == agent_id:
                    weighted_score += decision.confidence * weight
                else:
                    # Check if agent is in alternatives
                    for alt_agent, alt_score in decision.alternative_targets:
                        if alt_agent == agent_id:
                            weighted_score += (alt_score / 10.0) * weight * 0.5  # Lower weight for alternatives
                            break
            
            agent_weighted_scores[agent_id] = weighted_score
        
        # Select best agent
        best_agent = max(agent_weighted_scores.keys(), key=lambda x: agent_weighted_scores[x])
        combined_confidence = agent_weighted_scores[best_agent]
        
        # Create reasoning from contributing strategies
        contributing_strategies = [str(s.value) for s in strategy_decisions.keys()]
        reasoning = f"Hybrid decision combining: {', '.join(contributing_strategies)}"
        
        return RoutingDecision(
            target=best_agent,
            confidence=min(0.95, combined_confidence),
            reasoning=reasoning,
            strategy_used=RoutingStrategy.HYBRID,
            metadata={
                "strategy_decisions": {str(k.value): v.target for k, v in strategy_decisions.items()},
                "weighted_scores": agent_weighted_scores
            }
        )
    
    def _build_default_keyword_mappings(self) -> Dict[str, List[str]]:
        """Build default keyword mappings for routing."""
        return {
            "web_search": ["search", "find", "lookup", "web", "internet", "browse", "website"],
            "research": ["research", "analyze", "investigate", "study", "examine", "explore"],
            "writing": ["write", "compose", "create", "draft", "document", "article", "content"],
            "coding": ["code", "program", "develop", "implement", "debug", "script", "function"],
            "support": ["help", "assist", "support", "troubleshoot", "fix", "resolve", "issue"],
            "analysis": ["analyze", "examine", "evaluate", "assess", "review", "check"],
            "data": ["data", "statistics", "numbers", "metrics", "chart", "graph"]
        }
    
    def _build_default_rules(self) -> List[Dict[str, Any]]:
        """Build default routing rules."""
        return [
            {
                "name": "urgent_high_priority",
                "condition": lambda task, ctx: ctx.get('priority') == 'high' or 'urgent' in task,
                "agent_filter": lambda agent: agent.performance_score > 0.8,
                "confidence": 0.9,
                "reasoning": "High priority task routed to high-performance agent"
            },
            {
                "name": "simple_task_available_agent",
                "condition": lambda task, ctx: len(task.split()) < 10,
                "agent_filter": lambda agent: agent.availability > 0.7,
                "confidence": 0.7,
                "reasoning": "Simple task routed to available agent"
            },
            {
                "name": "complex_task_expert",
                "condition": lambda task, ctx: len(task.split()) > 50 or ctx.get('complexity') == 'high',
                "agent_filter": lambda agent: agent.performance_score > 0.7 and len(agent.capabilities) > 3,
                "confidence": 0.85,
                "reasoning": "Complex task routed to expert agent"
            }
        ]
    
    def _extract_task_keywords(self, task: str) -> List[str]:
        """Extract relevant keywords from task description."""
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\b\w+\b', task.lower())
        # Filter out common stop words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]  # Limit to top 10 keywords
    
    def _extract_agent_from_text(self, text: str, agents: List[str]) -> str:
        """Extract agent name from LLM response text."""
        text_lower = text.lower()
        for agent in agents:
            if agent.lower() in text_lower:
                return agent
        return agents[0]  # Fallback to first agent
    
    def _round_robin_fallback(self, agents: List[str]) -> str:
        """Simple round-robin fallback selection."""
        if not hasattr(self, '_round_robin_index'):
            self._round_robin_index = 0
        
        agent = agents[self._round_robin_index % len(agents)]
        self._round_robin_index += 1
        return agent
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics and performance metrics."""
        if not self.routing_history:
            return {"message": "No routing decisions recorded"}
        
        total_decisions = len(self.routing_history)
        strategy_counts = {}
        confidence_scores = []
        
        for decision in self.routing_history:
            strategy = decision.strategy_used.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            confidence_scores.append(decision.confidence)
        
        return {
            "total_decisions": total_decisions,
            "strategy_distribution": strategy_counts,
            "average_confidence": sum(confidence_scores) / len(confidence_scores),
            "agent_utilization": {agent_id: sum(1 for d in self.routing_history if d.target == agent_id) 
                                for agent_id in self.agent_capabilities.keys()}
        }