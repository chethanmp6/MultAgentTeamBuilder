"""
Test Scenarios - Comprehensive test scenarios for evaluating hierarchical agent teams
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ScenarioType(Enum):
    """Types of test scenarios"""
    SIMPLE_TASK = "simple_task"
    COMPLEX_WORKFLOW = "complex_workflow" 
    EDGE_CASE = "edge_case"
    COMPARATIVE_TEST = "comparative_test"
    LOAD_TEST = "load_test"


class DifficultyLevel(Enum):
    """Difficulty levels for test scenarios"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class TestScenario:
    """Individual test scenario for team evaluation"""
    name: str
    scenario_type: ScenarioType
    difficulty: DifficultyLevel
    prompt: str
    expected_outcome: Optional[str] = None
    timeout_seconds: int = 60
    domain: str = "general"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TestScenarioRunner:
    """Executes test scenarios against hierarchical teams"""
    
    def __init__(self):
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_scenario(self, team_instance: Any, scenario: TestScenario) -> str:
        """
        Execute a test scenario against a team instance
        
        Args:
            team_instance: The hierarchical team to test
            scenario: The test scenario to execute
            
        Returns:
            Response from the team
        """
        start_time = time.time()
        
        try:
            # Execute the scenario with timeout
            response = await asyncio.wait_for(
                self._invoke_team(team_instance, scenario.prompt),
                timeout=scenario.timeout_seconds
            )
            
            execution_time = time.time() - start_time
            
            # Log execution
            self.execution_history.append({
                'scenario': scenario.name,
                'execution_time': execution_time,
                'success': True,
                'timestamp': datetime.now()
            })
            
            return response
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.execution_history.append({
                'scenario': scenario.name,
                'execution_time': execution_time,
                'success': False,
                'error': 'timeout',
                'timestamp': datetime.now()
            })
            raise Exception(f"Scenario timed out after {scenario.timeout_seconds} seconds")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_history.append({
                'scenario': scenario.name,
                'execution_time': execution_time,
                'success': False, 
                'error': str(e),
                'timestamp': datetime.now()
            })
            raise
    
    async def _invoke_team(self, team_instance: Any, prompt: str) -> str:
        """Invoke the team with a prompt and return response"""
        try:
            # Try different invocation methods based on team type
            if hasattr(team_instance, 'ainvoke'):
                result = await team_instance.ainvoke({"input": prompt})
            elif hasattr(team_instance, 'run'):
                result = await team_instance.run(prompt)
            elif hasattr(team_instance, 'invoke'):
                result = team_instance.invoke({"input": prompt})
            else:
                # Fallback for different team interfaces
                result = str(team_instance)
            
            # Extract response text from various result formats
            if isinstance(result, dict):
                return result.get('output', result.get('response', str(result)))
            elif hasattr(result, 'content'):
                return result.content
            else:
                return str(result)
                
        except Exception as e:
            return f"Error executing team: {str(e)}"


class ScenarioLibrary:
    """Library of predefined test scenarios for different domains"""
    
    @staticmethod
    def get_general_scenarios() -> List[TestScenario]:
        """Get general-purpose test scenarios"""
        return [
            TestScenario(
                name="Simple Question Answering",
                scenario_type=ScenarioType.SIMPLE_TASK,
                difficulty=DifficultyLevel.EASY,
                prompt="What is the capital of France?",
                expected_outcome="Paris",
                timeout_seconds=30,
                domain="general",
                tags=["factual", "simple"]
            ),
            
            TestScenario(
                name="Multi-Step Problem Solving",
                scenario_type=ScenarioType.COMPLEX_WORKFLOW,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="Plan a 3-day vacation to Tokyo. Include flights, accommodation, and daily activities with estimated costs.",
                expected_outcome="A detailed 3-day itinerary with flights, hotels, activities, and cost breakdown",
                timeout_seconds=120,
                domain="travel",
                tags=["planning", "research", "calculation"]
            ),
            
            TestScenario(
                name="Empty Input Handling",
                scenario_type=ScenarioType.EDGE_CASE,
                difficulty=DifficultyLevel.EASY,
                prompt="",
                expected_outcome="Appropriate handling of empty input with helpful response",
                timeout_seconds=30,
                domain="general",
                tags=["edge_case", "error_handling"]
            ),
            
            TestScenario(
                name="Contradictory Instructions",
                scenario_type=ScenarioType.EDGE_CASE,
                difficulty=DifficultyLevel.HARD,
                prompt="Write a short story that is both very sad and extremely funny at the same time, but also completely emotionless.",
                expected_outcome="Recognition of contradictory requirements and appropriate response",
                timeout_seconds=90,
                domain="creative",
                tags=["contradiction", "edge_case", "creative"]
            ),
            
            TestScenario(
                name="Information Synthesis",
                scenario_type=ScenarioType.COMPLEX_WORKFLOW,
                difficulty=DifficultyLevel.HARD,
                prompt="Compare renewable energy sources (solar, wind, hydro) considering efficiency, cost, environmental impact, and scalability. Provide recommendations for different geographical regions.",
                expected_outcome="Comprehensive comparison with regional recommendations",
                timeout_seconds=180,
                domain="analysis",
                tags=["research", "analysis", "comparison", "synthesis"]
            )
        ]
    
    @staticmethod
    def get_research_scenarios() -> List[TestScenario]:
        """Get research-focused test scenarios"""
        return [
            TestScenario(
                name="Literature Review",
                scenario_type=ScenarioType.COMPLEX_WORKFLOW,
                difficulty=DifficultyLevel.HARD,
                prompt="Conduct a literature review on artificial intelligence in healthcare, focusing on diagnostic applications from 2020-2024.",
                expected_outcome="Structured literature review with recent sources and key findings",
                timeout_seconds=300,
                domain="research",
                tags=["literature_review", "healthcare", "AI"]
            ),
            
            TestScenario(
                name="Data Analysis Request",
                scenario_type=ScenarioType.COMPLEX_WORKFLOW,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="Analyze the trend of remote work adoption post-2020. Include statistics, drivers, challenges, and future predictions.",
                expected_outcome="Data-driven analysis with statistics and predictions",
                timeout_seconds=240,
                domain="business",
                tags=["data_analysis", "trends", "remote_work"]
            ),
            
            TestScenario(
                name="Technical Explanation",
                scenario_type=ScenarioType.SIMPLE_TASK,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="Explain blockchain technology to a non-technical audience, including benefits and limitations.",
                expected_outcome="Clear, accessible explanation of blockchain with pros/cons",
                timeout_seconds=90,
                domain="technology",
                tags=["explanation", "technical", "accessibility"]
            )
        ]
    
    @staticmethod
    def get_creative_scenarios() -> List[TestScenario]:
        """Get creative task scenarios"""
        return [
            TestScenario(
                name="Creative Writing",
                scenario_type=ScenarioType.SIMPLE_TASK,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="Write a 200-word short story about a robot learning to paint.",
                expected_outcome="Creative, coherent short story about specified topic",
                timeout_seconds=120,
                domain="creative",
                tags=["creative_writing", "storytelling", "fiction"]
            ),
            
            TestScenario(
                name="Marketing Campaign",
                scenario_type=ScenarioType.COMPLEX_WORKFLOW,
                difficulty=DifficultyLevel.HARD,
                prompt="Create a marketing campaign for a new eco-friendly smartphone. Include target audience, key messages, channels, and success metrics.",
                expected_outcome="Comprehensive marketing campaign with all requested elements",
                timeout_seconds=180,
                domain="marketing",
                tags=["marketing", "strategy", "creative", "planning"]
            ),
            
            TestScenario(
                name="Product Innovation",
                scenario_type=ScenarioType.COMPLEX_WORKFLOW,
                difficulty=DifficultyLevel.EXPERT,
                prompt="Design an innovative solution for urban food waste. Include problem analysis, solution design, implementation plan, and impact measurement.",
                expected_outcome="Innovative, practical solution with detailed implementation plan",
                timeout_seconds=300,
                domain="innovation",
                tags=["innovation", "sustainability", "problem_solving", "design"]
            )
        ]
    
    @staticmethod
    def get_load_test_scenarios() -> List[TestScenario]:
        """Get scenarios for testing team performance under load"""
        return [
            TestScenario(
                name="Concurrent Simple Tasks",
                scenario_type=ScenarioType.LOAD_TEST,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="Answer 5 different questions simultaneously: 1) Capital of Brazil, 2) 15*23, 3) Author of 1984, 4) Chemical formula for water, 5) Year WWII ended",
                expected_outcome="Correct answers to all 5 questions",
                timeout_seconds=60,
                domain="general",
                tags=["concurrent", "factual", "multiple_tasks"]
            ),
            
            TestScenario(
                name="Resource Intensive Task",
                scenario_type=ScenarioType.LOAD_TEST,
                difficulty=DifficultyLevel.HARD,
                prompt="Generate a comprehensive business plan for a sustainable fashion startup, including market analysis, financial projections, marketing strategy, and operational plan.",
                expected_outcome="Detailed business plan with all requested components",
                timeout_seconds=400,
                domain="business",
                tags=["comprehensive", "resource_intensive", "business_planning"]
            )
        ]
    
    @staticmethod
    def get_scenarios_by_domain(domain: str) -> List[TestScenario]:
        """Get scenarios filtered by domain"""
        all_scenarios = (
            ScenarioLibrary.get_general_scenarios() +
            ScenarioLibrary.get_research_scenarios() +
            ScenarioLibrary.get_creative_scenarios() +
            ScenarioLibrary.get_load_test_scenarios()
        )
        
        return [s for s in all_scenarios if s.domain == domain]
    
    @staticmethod
    def get_scenarios_by_difficulty(difficulty: DifficultyLevel) -> List[TestScenario]:
        """Get scenarios filtered by difficulty level"""
        all_scenarios = (
            ScenarioLibrary.get_general_scenarios() +
            ScenarioLibrary.get_research_scenarios() +
            ScenarioLibrary.get_creative_scenarios() +
            ScenarioLibrary.get_load_test_scenarios()
        )
        
        return [s for s in all_scenarios if s.difficulty == difficulty]
    
    @staticmethod
    def get_quick_evaluation_set() -> List[TestScenario]:
        """Get a quick set of scenarios for fast evaluation"""
        return [
            ScenarioLibrary.get_general_scenarios()[0],  # Simple question
            ScenarioLibrary.get_general_scenarios()[1],  # Multi-step problem
            ScenarioLibrary.get_general_scenarios()[2],  # Edge case
            ScenarioLibrary.get_research_scenarios()[2],  # Technical explanation
            ScenarioLibrary.get_creative_scenarios()[0]   # Creative writing
        ]
    
    @staticmethod
    def get_comprehensive_evaluation_set() -> List[TestScenario]:
        """Get a comprehensive set of scenarios for thorough evaluation"""
        return (
            ScenarioLibrary.get_general_scenarios() +
            ScenarioLibrary.get_research_scenarios() +
            ScenarioLibrary.get_creative_scenarios()[:2] +  # First 2 creative scenarios
            ScenarioLibrary.get_load_test_scenarios()[:1]   # First load test scenario
        )
    
    @staticmethod
    def create_custom_scenario(name: str, 
                             prompt: str,
                             scenario_type: ScenarioType = ScenarioType.SIMPLE_TASK,
                             difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
                             expected_outcome: Optional[str] = None,
                             timeout_seconds: int = 120,
                             domain: str = "custom") -> TestScenario:
        """Create a custom test scenario"""
        return TestScenario(
            name=name,
            scenario_type=scenario_type,
            difficulty=difficulty,
            prompt=prompt,
            expected_outcome=expected_outcome,
            timeout_seconds=timeout_seconds,
            domain=domain,
            tags=["custom"]
        )