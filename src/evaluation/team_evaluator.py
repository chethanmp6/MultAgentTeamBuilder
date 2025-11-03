"""
Team Evaluator - Core evaluation engine for hierarchical agent teams
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .common import EvaluationDimension, EvaluationSeverity
from .evaluation_prompts import EvaluationPrompts
from .test_scenarios import TestScenario, TestScenarioRunner, ScenarioType


@dataclass
class DimensionScore:
    """Score for a single evaluation dimension"""
    dimension: EvaluationDimension
    score: float  # 0.0 to 1.0
    raw_score: int  # 1 to 5
    reasoning: str
    suggestions: List[str] = field(default_factory=list)


@dataclass 
class TestResult:
    """Result from a single test scenario"""
    scenario_name: str
    scenario_type: ScenarioType
    success: bool
    execution_time: float
    response: str
    expected_outcome: Optional[str] = None
    error_message: Optional[str] = None
    dimension_scores: List[DimensionScore] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Complete evaluation result for a team"""
    team_name: str
    team_config: Dict[str, Any]
    overall_score: float  # 0.0 to 1.0
    dimension_scores: Dict[EvaluationDimension, float]
    test_results: List[TestResult]
    evaluation_time: float
    timestamp: datetime
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def grade(self) -> str:
        """Get letter grade based on overall score"""
        if self.overall_score >= 0.9:
            return "A+"
        elif self.overall_score >= 0.8:
            return "A"
        elif self.overall_score >= 0.7:
            return "B"
        elif self.overall_score >= 0.6:
            return "C"
        elif self.overall_score >= 0.5:
            return "D"
        else:
            return "F"


class DimensionEvaluation(BaseModel):
    """Structured output for dimension evaluation"""
    score: int = Field(description="Score from 1-5 for this dimension")
    reasoning: str = Field(description="Detailed reasoning for the score")
    suggestions: List[str] = Field(description="Specific suggestions for improvement")


class TeamEvaluator:
    """Advanced team evaluator using LLM-as-judge methodology"""
    
    def __init__(self, 
                 llm_provider: str = "openai",
                 model_name: str = "gpt-4o",
                 api_key: Optional[str] = None):
        """Initialize the team evaluator"""
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.prompts = EvaluationPrompts()
        
        # Initialize LLM
        if llm_provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=0.1,  # Low temperature for consistent evaluation
                api_key=api_key
            )
        elif llm_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=model_name,
                temperature=0.1,
                api_key=api_key
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
        
        self.scenario_runner = TestScenarioRunner()
    
    async def evaluate_team(self, 
                           team_config: Dict[str, Any],
                           team_instance: Any,
                           test_scenarios: List[TestScenario],
                           dimensions: List[EvaluationDimension] = None) -> EvaluationResult:
        """
        Evaluate a hierarchical team across multiple dimensions and scenarios
        
        Args:
            team_config: Team configuration dictionary
            team_instance: Actual team instance to test
            test_scenarios: List of test scenarios to run
            dimensions: Dimensions to evaluate (defaults to all)
        
        Returns:
            Comprehensive evaluation result
        """
        start_time = datetime.now()
        
        if dimensions is None:
            dimensions = list(EvaluationDimension)
        
        # Run test scenarios
        test_results = await self._run_test_scenarios(team_instance, test_scenarios)
        
        # Evaluate each dimension
        dimension_scores = {}
        all_dimension_scores = []
        
        for dimension in dimensions:
            dimension_score = await self._evaluate_dimension(
                dimension, test_results, team_config
            )
            dimension_scores[dimension] = dimension_score.score
            all_dimension_scores.append(dimension_score)
        
        # Calculate overall score
        overall_score = statistics.mean(dimension_scores.values())
        
        # Generate recommendations and warnings
        recommendations = self._generate_recommendations(all_dimension_scores, test_results)
        warnings = self._generate_warnings(all_dimension_scores, test_results)
        
        end_time = datetime.now()
        evaluation_time = (end_time - start_time).total_seconds()
        
        return EvaluationResult(
            team_name=team_config.get('team', {}).get('name', 'Unknown Team'),
            team_config=team_config,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            test_results=test_results,
            evaluation_time=evaluation_time,
            timestamp=end_time,
            recommendations=recommendations,
            warnings=warnings
        )
    
    async def _run_test_scenarios(self, 
                                 team_instance: Any, 
                                 scenarios: List[TestScenario]) -> List[TestResult]:
        """Run all test scenarios against the team"""
        results = []
        
        for scenario in scenarios:
            try:
                start_time = datetime.now()
                
                # Execute the scenario
                response = await self.scenario_runner.execute_scenario(
                    team_instance, scenario
                )
                
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                # Evaluate success
                success = await self._evaluate_scenario_success(
                    scenario, response
                )
                
                results.append(TestResult(
                    scenario_name=scenario.name,
                    scenario_type=scenario.scenario_type,
                    success=success,
                    execution_time=execution_time,
                    response=response,
                    expected_outcome=scenario.expected_outcome
                ))
                
            except Exception as e:
                results.append(TestResult(
                    scenario_name=scenario.name,
                    scenario_type=scenario.scenario_type,
                    success=False,
                    execution_time=0.0,
                    response="",
                    error_message=str(e)
                ))
        
        return results
    
    async def _evaluate_dimension(self, 
                                 dimension: EvaluationDimension,
                                 test_results: List[TestResult],
                                 team_config: Dict[str, Any]) -> DimensionScore:
        """Evaluate a specific dimension using LLM-as-judge"""
        
        # Prepare context for evaluation
        context = self._prepare_dimension_context(dimension, test_results, team_config)
        
        # Get evaluation prompt
        prompt = self.prompts.get_dimension_prompt(dimension, context)
        
        # Evaluate using LLM
        messages = [
            SystemMessage(content=prompt["system"]),
            HumanMessage(content=prompt["human"])
        ]
        
        try:
            # Use structured output for consistent evaluation
            response = await self.llm.ainvoke(messages)
            evaluation = self._parse_dimension_evaluation(response.content)
            
            # Convert 1-5 score to 0-1 scale
            normalized_score = (evaluation["score"] - 1) / 4.0
            
            return DimensionScore(
                dimension=dimension,
                score=normalized_score,
                raw_score=evaluation["score"],
                reasoning=evaluation["reasoning"],
                suggestions=evaluation.get("suggestions", [])
            )
            
        except Exception as e:
            # Fallback scoring if LLM evaluation fails
            return DimensionScore(
                dimension=dimension,
                score=0.5,  # Neutral score
                raw_score=3,
                reasoning=f"Evaluation failed: {str(e)}",
                suggestions=["Unable to evaluate this dimension due to technical issues"]
            )
    
    def _prepare_dimension_context(self, 
                                  dimension: EvaluationDimension,
                                  test_results: List[TestResult],
                                  team_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for dimension evaluation"""
        
        # Filter relevant test results for this dimension
        relevant_results = []
        for result in test_results:
            if self._is_result_relevant_for_dimension(result, dimension):
                relevant_results.append({
                    'scenario': result.scenario_name,
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'response': result.response[:500],  # Truncate for context
                    'error': result.error_message
                })
        
        return {
            'dimension': dimension.value,
            'team_config': {
                'name': team_config.get('team', {}).get('name'),
                'teams_count': len(team_config.get('teams', [])),
                'workers_count': sum(len(team.get('workers', [])) for team in team_config.get('teams', []))
            },
            'test_results': relevant_results,
            'success_rate': sum(1 for r in test_results if r.success) / len(test_results) if test_results else 0,
            'avg_execution_time': statistics.mean([r.execution_time for r in test_results]) if test_results else 0
        }
    
    def _is_result_relevant_for_dimension(self, 
                                        result: TestResult, 
                                        dimension: EvaluationDimension) -> bool:
        """Check if a test result is relevant for evaluating a specific dimension"""
        
        dimension_relevance = {
            EvaluationDimension.TASK_COMPLETION: [ScenarioType.SIMPLE_TASK, ScenarioType.COMPLEX_WORKFLOW],
            EvaluationDimension.COLLABORATION_EFFECTIVENESS: [ScenarioType.COMPLEX_WORKFLOW, ScenarioType.LOAD_TEST],
            EvaluationDimension.RESOURCE_UTILIZATION: [ScenarioType.LOAD_TEST, ScenarioType.COMPLEX_WORKFLOW],
            EvaluationDimension.RESPONSE_COHERENCE: [ScenarioType.SIMPLE_TASK, ScenarioType.COMPLEX_WORKFLOW],
            EvaluationDimension.SCALABILITY_PERFORMANCE: [ScenarioType.LOAD_TEST],
            EvaluationDimension.ERROR_HANDLING: [ScenarioType.EDGE_CASE]
        }
        
        relevant_types = dimension_relevance.get(dimension, [])
        return result.scenario_type in relevant_types
    
    def _parse_dimension_evaluation(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response for dimension evaluation"""
        try:
            # Try to parse as JSON first
            if response_content.strip().startswith('{'):
                return json.loads(response_content)
            
            # Fallback parsing for text responses
            lines = response_content.strip().split('\n')
            evaluation = {
                'score': 3,  # Default neutral score
                'reasoning': response_content,
                'suggestions': []
            }
            
            # Look for score in text
            for line in lines:
                if 'score:' in line.lower() or 'rating:' in line.lower():
                    try:
                        score = int(''.join(filter(str.isdigit, line)))
                        if 1 <= score <= 5:
                            evaluation['score'] = score
                    except:
                        pass
            
            return evaluation
            
        except Exception:
            return {
                'score': 3,
                'reasoning': 'Unable to parse evaluation response',
                'suggestions': []
            }
    
    async def _evaluate_scenario_success(self, 
                                       scenario: TestScenario, 
                                       response: str) -> bool:
        """Evaluate if a scenario was completed successfully"""
        if not scenario.expected_outcome:
            return len(response.strip()) > 0  # Basic check
        
        # Use LLM to compare response with expected outcome
        prompt = f"""
        Evaluate if the following response successfully addresses the scenario requirement.
        
        Scenario: {scenario.prompt}
        Expected: {scenario.expected_outcome}
        Response: {response}
        
        Return only 'true' if the response adequately addresses the scenario, 'false' otherwise.
        """
        
        try:
            messages = [HumanMessage(content=prompt)]
            result = await self.llm.ainvoke(messages)
            return result.content.strip().lower() == 'true'
        except:
            return len(response.strip()) > 50  # Fallback
    
    def _generate_recommendations(self, 
                                dimension_scores: List[DimensionScore],
                                test_results: List[TestResult]) -> List[str]:
        """Generate improvement recommendations based on evaluation"""
        recommendations = []
        
        # Add dimension-specific recommendations
        for score in dimension_scores:
            if score.score < 0.6:  # Poor performance
                recommendations.extend(score.suggestions)
        
        # Add general recommendations based on patterns
        failed_tests = [r for r in test_results if not r.success]
        if len(failed_tests) > len(test_results) * 0.3:  # >30% failure rate
            recommendations.append(
                "Consider simplifying team structure - high failure rate suggests complexity issues"
            )
        
        avg_time = statistics.mean([r.execution_time for r in test_results]) if test_results else 0
        if avg_time > 30:  # Slow responses
            recommendations.append(
                "Optimize team configuration for faster response times"
            )
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_warnings(self, 
                          dimension_scores: List[DimensionScore],
                          test_results: List[TestResult]) -> List[str]:
        """Generate warnings based on evaluation results"""
        warnings = []
        
        # Critical dimension scores
        critical_scores = [s for s in dimension_scores if s.score < 0.4]
        if critical_scores:
            warnings.append(
                f"Critical performance issues in: {', '.join([s.dimension.value for s in critical_scores])}"
            )
        
        # High error rate
        error_rate = sum(1 for r in test_results if r.error_message) / len(test_results) if test_results else 0
        if error_rate > 0.2:  # >20% error rate
            warnings.append(
                f"High error rate ({error_rate:.1%}) - team may be unstable"
            )
        
        return warnings

    async def compare_teams(self, 
                          evaluations: List[EvaluationResult]) -> Dict[str, Any]:
        """Compare multiple team evaluations"""
        if len(evaluations) < 2:
            raise ValueError("Need at least 2 evaluations to compare")
        
        comparison = {
            'teams': [e.team_name for e in evaluations],
            'overall_scores': {e.team_name: e.overall_score for e in evaluations},
            'winner': max(evaluations, key=lambda x: x.overall_score).team_name,
            'dimension_comparison': {},
            'performance_analysis': []
        }
        
        # Compare by dimension
        for dimension in EvaluationDimension:
            scores = {}
            for eval_result in evaluations:
                if dimension in eval_result.dimension_scores:
                    scores[eval_result.team_name] = eval_result.dimension_scores[dimension]
            
            if scores:
                best_team = max(scores.keys(), key=lambda x: scores[x])
                comparison['dimension_comparison'][dimension.value] = {
                    'scores': scores,
                    'best_team': best_team
                }
        
        return comparison